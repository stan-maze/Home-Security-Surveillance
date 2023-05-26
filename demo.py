from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadScreenshots
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode
from utils.camera import LoadImages, LoadStreams
# from utils.dataloaders import LoadStreams
from utils.alert import send_email

from pathlib import Path
import json
import torch
import platform
from collections import Counter
import os
import datetime
import logging
import logging.handlers
import tarfile
import glob
import shutil
from collections import deque


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
        
        
        # 后面整合到config里
        self.recording = False
        self.on_alarm = True
        self.patience = 100
        self.recemail = '2311306511@qq.com'
        

        self.init_dataloader()
        self.preprocess()
        self.init_logger()
        
        
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
    
    def preprocess(self):
        log_dir = 'log'  # 日志目录路径
        archive_dir = 'log_archive'  # 归档目录路径
        for required_dir in (log_dir, archive_dir):
            if not os.path.exists(required_dir):
                os.makedirs(required_dir)
        
        current_time = datetime.datetime.now()
        # 清理超过一个月的日志归档记录
        one_month_ago = current_time - datetime.timedelta(seconds=30)
        for archive_file in glob.glob(os.path.join(archive_dir, '*.tar.gz')):
            modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(archive_file))
            if modified_time < one_month_ago:
                os.remove(archive_file)
                print(f"Deleted archived log file: {archive_file}")

        # 归档超过一周的日志目录并压缩
        one_week_ago = current_time - datetime.timedelta(seconds=7)
        for log_subdir in os.listdir(log_dir):
            log_subdir_path = os.path.join(log_dir, log_subdir)
            if not os.path.isdir(log_subdir_path):
                continue
            modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(log_subdir_path))
            if modified_time < one_week_ago:
                # 创建归档文件路径
                archive_file = os.path.join(archive_dir, f"{log_subdir}.tar.gz")

                # 压缩整个目录到归档文件
                with tarfile.open(archive_file, "w:gz") as tar:
                    tar.add(log_subdir_path, arcname=log_subdir)

                # 删除原始日志目录
                shutil.rmtree(log_subdir_path)
                print(f"Archived and deleted log directory: {log_subdir_path} -> {archive_file}")

        self.log_dir = log_dir
        self.archive_dir = archive_dir

        
    
    def init_logger(self):
        # 创建按时间命名的目录
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        current_log_dir = os.path.join('log', current_time)
        os.makedirs(current_log_dir)

        # 更新日志文件路径
        log_file = os.path.join(current_log_dir, f'{current_time}.log')

        # 配置日志记录
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # 创建RotatingFileHandler对象，设置日志轮转条件
        log_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024,  # 每个日志文件的最大大小（字节）
            backupCount=3,  # 保留的日志文件个数（包括当前文件）
        )
        log_handler.setLevel(logging.INFO)

        # 设置日志记录格式
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(log_formatter)

        # 添加日志处理器到logger
        logger.addHandler(log_handler)
        
        self.current_log_dir = current_log_dir
        self.logger = logger
        self.log_handler = log_handler
        
        
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
        
    def alarm_and_loggging():
        pass
        
    
    def run_detect(self):
        def anomaly_detected(queue):
            if len(queue) < 5:
                return False
            if sum(queue) >= len(queue)/2:
                return True
            return False
        
        config = self.config
        
        max_length = 30  # 最大录像长度（单位：帧）
        alert_sent = False
        recording = False
        patience = self.patience
        video_writer = None
                
                
        save_img = not config['nosave'] and not config['source'].endswith('.txt')  # save inference images
        if self.webcam:
            view_img = check_imshow(warn=True)
        # 从webcam中取帧
        windows = []
        frame_count = 0
        obj_queue = deque(maxlen=7)
        for path, im, im0s, vid_cap in self.dataset:
            config['visualize'] = increment_path(config['save_dir'] / Path(path).stem, mkdir=True) if config['visualize'] else False
            
            preds, objs, im = self.infer_frame(im)
            
            # 应对多线程/gpu的复数batchsize, 所以帧会并行得到一个结果list
            # 没有应用这些技术, 这里解出来肯定是单元素的
            s = ''
            for i, (det, obj) in enumerate(zip(preds, objs)):
                if self.webcam:
                    p, im0, frame = path[i], im0s[i].copy(), self.dataset.count
                    # s += f'{i}: '
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
                            
                    
                    # 如果有obj都是要进入log的
                    self.logger.info(s)
                # 没检测到东西
                else:
                    self.logger.info('nothing')
                    

                # Stream results
                im0 = annotator.result()
                
                obj_queue.append('fire' in obj or 'Unknow' in obj)
                
                if anomaly_detected(obj_queue):
                    # 记录帧, 报警, 这两个要过滤重复
                    if self.on_alarm:
                        print(alert_sent, patience)
                        if not alert_sent or patience == 0:
                            current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            img_path = os.path.join(self.current_log_dir, f'{s}_{current_time}.jpg')
                            cv2.imwrite(img_path, im0)
                            alert_sent = send_email(self.recemail, '摄像机发现异常!', s, img_path)
                            print('发送邮件')
                            patience = self.patience
                        else:
                            patience -= 1
                    # 录视频
                    if not recording:
                        recording = True
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        video_path = os.path.join(self.current_log_dir, f'{current_time}.avi')
                        self.logger.info(f'开始录像, 录像保存至: {video_path}')
                        print('开始录像')
                        fps, w, h = 10, im0.shape[1], im0.shape[0]
                        video_writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                        video_writer.write(im0)
                # 停止录视频
                elif recording:
                        video_writer.write(im0)
                        frame_count += 1
                        if frame_count >= max_length:
                            # 达到最大录像长度或火情消失，停止录像
                            if anomaly_detected(obj_queue):
                                frame_count = 0
                            else:
                                recording = False
                                video_writer.release()
                                video_writer = None
                                frame_count = 0
                                self.logger.info(f'录像结束, 保存至{video_path}')
                                print(f'录像结束, 保存至{video_path}')
                
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