from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadScreenshots
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode
from utils.camera import LoadImages, LoadStreams
# from utils.dataloaders import LoadStreams

from pathlib import Path
import json
import torch
import platform
from collections import Counter


from facerec import face_recognizer
from firedet import fire_detector

class detect_tasks_manager():
    def __init__(self) -> None:
        with open('config.json', 'r', encoding='utf8') as fp:
            self.config = json.load(fp)
            print('[INFO] Config:', self.config)
        
        self.device = select_device(self.config['device'])
        self.faceRecognizer = face_recognizer()
        self.fireDetector = fire_detector()
        
        self.fp16 = self.fireDetector.model.fp16
        
        self.init_dataloader()
        
        
    def init_dataloader(self):
        source = self.config['source']

        is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
        is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
        self.webcam = source.isnumeric() or source.endswith('.streams') or (is_url and not is_file)
        if is_url and is_file:
            source = check_file(source)  # download
        # Directories
        self.save_dir = increment_path(Path(self.config['project']) / self.config['name'], exist_ok=self.config['exist_ok'])  # increment run
        (self.save_dirsave_dir / 'labels' if self.config['save_txt'] else self.save_dir).mkdir(parents=True, exist_ok=True)  # make dir
        bs = 1  # batch_size
        print('source: ', source)
        if self.webcam:
            view_img = check_imshow(warn=True)
            self.dataset = LoadStreams(source, img_size=self.config['imgsz'], stride=self.config['stride'])
            bs = len(self.dataset)
            print('webcam')
        else:
            self.dataset = LoadImages(source, img_size=self.config['imgsz'], stride=self.config['stride'])
            print('not webcam')
    
    def infer_frame(self, im):
        
        facepred, face = self.faceRecognizer.infer(im)

        im = torch.from_numpy(im).to(self.device)
        im = im.half() if self.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim

        # 输入的是百分比坐标, 输出怎么变回了绝对坐标, 奇怪
        firepred, fire = self.fireDetector.infer(im)
        # print(facepred, face, facepred[0].dtype)
        preds = [torch.cat((facepred[0], firepred[0]), dim=0)]
        objs = [face[0] + fire[0]]
        print(objs)
        
        return preds, objs, im
        
    
    def run_detect(self):
        
        config = self.config
                
        save_img = not config['nosave'] and not config['source'].endswith('.txt')  # save inference images
        if self.webcam:
            view_img = check_imshow(warn=True)
        # 从webcam中取帧
        windows, s = [], ''
        for path, im, im0s, vid_cap in self.dataset:
            config['visualize'] = increment_path(config['save_dir'] / Path(path).stem, mkdir=True) if config['visualize'] else False
            
            preds, objs, im = self.infer_frame(im)
            
            for i, (det, obj) in enumerate(zip(preds, objs)):
                if self.webcam:
                    p, im0, frame = path[i], im0s[i].copy(), self.dataset.count
                    s += f'{i}: '
                else:
                    p, im0, frame = path, im0s.copy(), getattr(self.dataset, 'frame', 0)

                p = Path(p)  # to Path
                save_path = str(self.save_dir / p.name)  # im.jpg
                txt_path = str(self.save_dir / 'labels' / p.stem) + ('' if self.dataset.mode == 'image' else f'_{frame}')  # im.txt
                # s += '%gx%g ' % im.shape[2:]  # print string
                gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                imc = im0.copy() if self.config['save_crop'] else im0  # for save_crop
                annotator = Annotator(im0, line_width=self.config['line_thickness'])
                
                # pred在之前已经测好了, det是detection
                # 现在要绘制box上去, 在这之前要查人脸, 加到det里, 按照det的规则， 前四列box，最后一列n, 第四列不知道干嘛的， 可能是置信度
                # [tensor(55.), tensor(19.), tensor(633.), tensor(477.)] person 0.87 (56, 56, 255)
                # 操作在im0上, im0表示原媒体流, imc是copy后的, 现在im0还是原流
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    
                    det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                    # Print results
                    # for c in det[:, 5].unique():
                    #     n = (det[:, 5] == c).sum()  # detections per class
                    #     s += f"{n} {detector.names[int(c)]}{'s' * (n > 1)}, "  # add to string
                    for c, n in Counter(obj).items():
                        s += f"{n} {c}{'s' * (n > 1)}, "
                        
                    # Write results
                    for deti, cls in reversed(list(zip(det, obj))):
                        *xyxy, conf, _ = deti
                        if self.config['save_txt']:  # Write to file
                            xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf) if self.config['save_conf'] else (cls, *xywh)  # label format
                            with open(f'{txt_path}.txt', 'a') as f:
                                f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        if save_img or self.config['save_crop'] or view_img:
                            label = f'{cls} {conf:.2f}'
                            annotator.box_label(xyxy, label)
                            
                            
                        if self.config['save_crop']:
                            save_one_box(xyxy, imc, file=self.save_dir / 'crops' / cls / f'{p.stem}.jpg', BGR=True)

                # Stream results
                im0 = annotator.result()     
                # 这里是绘制 
                if self.config['view_img']:
                    if platform.system() == 'Linux' and p not in windows:
                        windows.append(p)
                        cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                        cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
                    cv2.imshow(str(p), im0)
                    cv2.waitKey(1)  # 1 millisecond
    
    
    
def test():
    manager = detect_tasks_manager()
    manager.run_detect()

if __name__ == '__main__':
    test()