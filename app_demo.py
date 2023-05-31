# import the necessary packages
from firedet import (mix_Detector, LoadStreams, LoadImages, check_imshow, check_file, Annotator, xyxy2xywh,
                        increment_path, IMG_FORMATS, VID_FORMATS, LoadScreenshots, scale_boxes, save_one_box)
from flask import Response
from flask import Flask
from flask import render_template
import time
import torch
import json
import cv2
import os
from pathlib import Path
import platform



# initialize a flask object
app = Flask(__name__)

# initialize the video stream and allow the camera sensor to warmup
with open('config.json', 'r', encoding='utf8') as fp:
    opt = json.load(fp)
    print('[INFO] Config:', opt)

detector = mix_Detector()
source = opt['source']

is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
webcam = source.isnumeric() or source.endswith('.streams') or (is_url and not is_file)
screenshot = source.lower().startswith('screen')
if is_url and is_file:
    source = check_file(source)  # download
# Directories
save_dir = increment_path(Path(detector.project) / detector.name, exist_ok=detector.exist_ok)  # increment run
(save_dir / 'labels' if detector.save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir
bs = 1  # batch_size
print('source: ', source)
if webcam:
    view_img = check_imshow(warn=True)
    dataset = LoadStreams(source, img_size=detector.imgsz, stride=detector.stride)
    bs = len(dataset)
    print('webcam')
elif screenshot:
    dataset = LoadScreenshots(source, img_size=detector.imgsz, stride=detector.stride, auto=detector.pt)
else:
    dataset = LoadImages(source, img_size=detector.imgsz, stride=detector.stride)
    print('not webcam')

time.sleep(2.0)

@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")

def detect_gen(dataset, feed_type):
    save_img = not detector.nosave and not detector.source.endswith('.txt')  # save inference images
    if webcam:
        view_img = check_imshow(warn=True)
    # 从webcam中取帧
    windows, s = [], ''
    for path, im, im0s, vid_cap in dataset:
        detector.visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if detector.visualize else False
        
        preds, objs, im = detector.infer_frame(im)
        
        for i, (det, obj) in enumerate(zip(preds, objs)):
            if webcam:
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # im.jpg
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            # s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0.copy() if detector.save_crop else im0  # for save_crop
            annotator = Annotator(im0, line_width=detector.line_thickness, example=str(detector.names))
            
            # pred在之前已经测好了, det是detection
            # 现在要绘制box上去, 在这之前要查人脸, 加到det里, 按照det的规则， 前四列box，最后一列n, 第四列不知道干嘛的， 可能是置信度
            # [tensor(55.), tensor(19.), tensor(633.), tensor(477.)] person 0.87 (56, 56, 255)
            # 操作在im0上, im0表示原媒体流, imc是copy后的, 现在im0还是原流
            if len(det):
                # Rescale boxes from img_size to im0 size
                
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, 5].unique():
                    n = (det[:, 5] == c).sum()  # detections per class
                    s += f"{n} {detector.names[int(c)]}{'s' * (n > 1)}, "  # add to string
                # Write results
                for deti, cls in reversed(list(zip(det, obj))):
                    *xyxy, conf, _ = deti
                    if detector.save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        line = (cls, *xywh, conf) if detector.save_conf else (cls, *xywh)  # label format
                        with open(f'{txt_path}.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')

                    if save_img or detector.save_crop or view_img:  # Add bbox to image
                        label = f'{cls} {conf:.2f}'
                        annotator.box_label(xyxy, label)
                        
                        
                    if detector.save_crop:
                        save_one_box(xyxy, imc, file=save_dir / 'crops' / detector.names[c] / f'{p.stem}.jpg', BGR=True)


            # Stream results
            im0 = annotator.result()
            frame = cv2.imencode('.jpg', im0)[1].tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')       
            # 这里是绘制 
            # if detector.view_img:
            #     if platform.system() == 'Linux' and p not in windows:
            #         windows.append(p)
            #         cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
            #         cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
            #     cv2.imshow(str(p), im0)
            #     cv2.waitKey(1)  # 1 millisecond
    
    
        
@app.route('/video_feed/<feed_type>')
def video_feed(feed_type):
    """Video streaming route. Put this in the src attribute of an img tag."""
    if feed_type == 'Camera_0':
        return Response(detect_gen(dataset=dataset, feed_type=feed_type),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    elif feed_type == 'Camera_1':
        return Response(detect_gen(dataset=dataset, feed_type=feed_type),
                        mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port="5000", threaded=True)

