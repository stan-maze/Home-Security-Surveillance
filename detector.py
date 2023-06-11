from utils.dataloaders import IMG_FORMATS, VID_FORMATS
from utils.general import check_file, check_imshow, cv2, increment_path, scale_boxes, xyxy2xywh
from utils.plots import Annotator, save_one_box
from utils.torch_utils import select_device
from utils.camera import LoadImages, LoadStreams
# from utils.dataloaders import LoadStreams
from utils.log_alarm import alarm, logger
# from utils.log_alarm import alarm, send_email

from pathlib import Path
import json
import torch
import platform
from collections import Counter
import os
from datetime import datetime, timedelta
import logging
import logging.handlers
import tarfile
import glob
import shutil
from collections import deque
import base64
import time


abs_path = os.path.abspath(__file__)
config_path = os.path.join((os.path.dirname(abs_path)), 'config.json')
log_dir = os.path.join((os.path.dirname(abs_path)), 'log')

from facerec import face_recognizer
from firedet import fire_detector



class detect_tasks_manager():
    def __init__(self) -> None:
        with open(config_path, 'r', encoding='utf8') as fp:
            self.config = json.load(fp)
            # print('[INFO] Config:', self.config)
        
        self.faceRecognizer = face_recognizer()
        self.fireDetector = fire_detector()
        self.device = select_device(self.fireDetector.device)
        
        self.fp16 = self.fireDetector.model.fp16
    
        self.on_alarm = self.config['on_alarm']
        if self.config['patience'] < 1:
            seconds = int(self.config['patience']*60)
            self.patience = timedelta(seconds=seconds)
        else:
            self.patience = timedelta(minutes=self.config['patience'])
        # self.recemail = self.config['recemail']
        
        self.min_length = self.config['min_length']
        
        self.start_time = datetime.strptime(self.config['start_time'], "%I.%M%p").time()
        self.end_time = datetime.strptime(self.config['end_time'], "%I.%M%p").time()
        # 不同的比较方式
        self.flag = self.start_time > self.end_time

        self.init_dataloader()
        self.init_logger_and_alarm()
        # self.preprocess()
        # self.init_logger()
    
    def is_within_time_range(self):
        now = datetime.now().time()
        # 处理跨越午夜的情况，例如10.pm到凌晨4.am
        if self.flag:
            return now >= self.start_time or now <= self.end_time
        else:
            return self.start_time <= now <= self.end_time
    
    
    def init_logger_and_alarm(self):
        self.logger = logger()
        self.logger.preprocess()
        self.logger.setup(maxMB=self.config['maxMB'], backupCount=self.config['backupCount'])
        self.alarm = alarm()
        self.alarm.setup(self.config['recemail'])

    def init_dataloader(self):
        source = self.config['source']

        is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
        is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
        # 判断是否为摄像头设备, 数字代表设备号, 或者是网络摄像头is_url
        self.webcam = source.isnumeric() or source.endswith('.streams') or (is_url and not is_file)
        
        # 文件后缀的话检查文件存在性
        if is_url and is_file:
            source = check_file(source)
        print('source: ', source)
        if self.webcam:
            # 摄像头画面流使用LoadStreams
            self.dataset = LoadStreams(source, img_size=self.config['imgsz'], stride=self.config['stride'])
            # bs = len(self.dataset)
            print('webcam')
        else:
            # 文件画面流使用LoadImages,但是要注意将路径补全
            source = os.path.join((os.path.dirname(abs_path)), source)
            self.dataset = LoadImages(source, img_size=self.config['imgsz'], stride=self.config['stride'])
            print('not webcam')
        self.source = source    
    
    def preprocess(self):
        # log_dir = 'log'  # 日志目录路径
        sub_log_dir = os.path.join(log_dir, 'log') # 日志目录路径
        archive_dir = os.path.join(log_dir, 'log_archive')  # 归档目录路径
        for required_dir in (log_dir, sub_log_dir, archive_dir):
            if not os.path.exists(required_dir):
                os.makedirs(required_dir)
        
        current_time = datetime.now()
        # 清理超过一个月的日志归档记录
        one_month_ago = current_time - timedelta(days=30)
        for archive_file in glob.glob(os.path.join(archive_dir, '*.tar.gz')):
            modified_time = datetime.fromtimestamp(os.path.getmtime(archive_file))
            if modified_time < one_month_ago:
                os.remove(archive_file)
                print(f"Deleted archived log file: {archive_file}")

        # 归档超过一周的日志目录并压缩
        one_week_ago = current_time - timedelta(days=7)
        for log_subdir in os.listdir(sub_log_dir):
            log_subdir_path = os.path.join(sub_log_dir, log_subdir)
            if not os.path.isdir(log_subdir_path):
                continue
            modified_time = datetime.fromtimestamp(os.path.getmtime(log_subdir_path))
            if modified_time < one_week_ago:
                # 创建归档文件路径
                archive_file = os.path.join(archive_dir, f"{log_subdir}.tar.gz")

                # 压缩整个目录到归档文件
                with tarfile.open(archive_file, "w:gz") as tar:
                    tar.add(log_subdir_path, arcname=log_subdir)

                # 删除原始日志目录
                shutil.rmtree(log_subdir_path)
                print(f"Archived and deleted log directory: {log_subdir_path} -> {archive_file}")

        self.sub_log_dir = sub_log_dir
        self.archive_dir = archive_dir
    
    def _init_logger(self):
        # 创建按时间命名的目录
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        current_log_dir = os.path.join(self.sub_log_dir, current_time)
        os.makedirs(current_log_dir)

        # 更新日志文件路径
        log_file = os.path.join(current_log_dir, f'{current_time}.log')

        # 配置日志记录
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # 创建RotatingFileHandler对象，设置日志轮转条件
        log_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024,  # 每个日志文件的最大大小（字节）
            backupCount=3,  # 保留的日志文件个数（包括当前文件）
        )
        log_handler.setLevel(logging.INFO)

        # 设置日志记录格式
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(log_formatter)

        # 添加日志处理器到logger
        logger.addHandler(log_handler)
        
        self.logger.current_log_dir = current_log_dir
        self.logger = logger
        # self.log_handler = log_handler
        
    def infer_frame(self, im):
        facepred, face = None, None
        # 判断是否在非法闯入检测时间段内
        if self.is_within_time_range():
            # 人脸识别结果, facepred为[[x1,x2,y1,y2,confidence], ...]为坐标和置信度列表
            # face是对应的检测结果字符串[hrz, ...]
            facepred, face = self.faceRecognizer.infer(im)
            
        # im在这里的处理是必要的,不仅火焰识别模型需要转化成[0, 1]的分数像素值, 后面的绘制也需要
        im = torch.from_numpy(im).to(self.device)
        im = im.half() if self.fp16 else im.float()
        im /= 255
        if len(im.shape) == 3:
            im = im[None]
            
        # 火灾识别结果同样格式
        firepred, fire = self.fireDetector.infer(im)
        
        if facepred is None:
            # print('不在非法闯入检测时间段内')
            print(fire)
            return firepred, fire, im
        preds = [torch.cat((facepred[0], firepred[0]), dim=0)]
        objs = [face[0] + fire[0]]
        print(objs)

        return preds, objs, im

    def gen_frame(self):
        def anomaly_detected(queue):
            if len(queue) < 5:
                return False
            if sum(queue) >= len(queue)/2:
                return True
            return False
        
        config = self.config
        
        min_length = 30  # 最大录像长度（单位：帧）
        alert_sent = False
        recording = False
        last_time = datetime.now()

        # patience = self.patience
        video_writer = None
                
                
        save_img = not config['nosave'] and not self.source.endswith('.txt')  # save inference images
        # if self.webcam:
            # view_img = check_imshow(warn=True)
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
                    self.logger.log(s)
                # 没检测到东西
                else:
                    self.logger.log('nothing')
                    

                # Stream results
                im0 = annotator.result()
                obj_queue.append('fire' in obj or 'Unknown' in obj)
                
                if anomaly_detected(obj_queue):
                    # 记录帧, 报警, 这两个要过滤重复
                    if self.on_alarm:
                        
                        # print(alert_sent, patience)
                        if not alert_sent or (datetime.now() - last_time>timedelta(minutes=self.patience)):
                            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            img_path = os.path.join(self.logger.current_log_dir, f'{s}_{current_time}.jpg')
                            cv2.imwrite(img_path, im0)
                            alert_sent = self.alarm.send_alert('摄像机发现异常!', s, img_path)
                            
                            print('发送邮件')
                            last_time = datetime.now()
                        # else:
                        #     print('patience:', patience)
                        #     patience -= 1
                    # 录视频
                    if not recording:
                        recording = True
                        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        video_path = os.path.join(self.logger.current_log_dir, f'{current_time}.avi')
                        self.logger.log(f'开始录像, 录像保存至: {video_path}')
                        print('开始录像')
                        fps, w, h = 10, im0.shape[1], im0.shape[0]
                        video_writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                        video_writer.write(im0)
                # 停止录视频
                elif recording:
                        video_writer.write(im0)
                        frame_count += 1
                        if frame_count >= min_length:
                            # 达到最大录像长度或火情消失，停止录像
                            if anomaly_detected(obj_queue):
                                frame_count = 0
                            else:
                                recording = False
                                video_writer.release()
                                video_writer = None
                                frame_count = 0
                                self.logger.log(f'录像结束, 保存至{video_path}')
                                print(f'录像结束, 保存至{video_path}')
                frame = cv2.imencode('.jpg', im0)[1].tobytes()
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 
    
    def run_detect(self):
        def anomaly_detected(queue):
            if len(queue) < 5:
                return False
            if sum(queue) >= len(queue)/2:
                return True
            return False
        
        config = self.config
        
        min_length = 30  # 最大录像长度（单位：帧）
        alert_sent = False
        recording = False
        # patience = self.patience
        last_time = datetime.now()
        video_writer = None
                
                
        # save_img = not config['nosave'] and not self.source.endswith('.txt')  # save inference images
        # if self.webcam:
            # view_img = check_imshow(warn=True)
        view_img = check_imshow(warn=True)
            
        # 从webcam中取帧
        windows = []
        frame_count = 0
        obj_queue = deque(maxlen=7)
        for path, im, im0s, _ in self.dataset:
            # config['visualize'] = increment_path(config['save_dir'] / Path(path).stem, mkdir=True) if config['visualize'] else False
            
            preds, objs, im = self.infer_frame(im)
            
            # 应对多线程/gpu的复数batchsize, 所以帧会并行得到一个结果list
            # 没有应用这些技术, 这里解出来肯定是单元素的
            s = ''
            for i, (det, obj) in enumerate(zip(preds, objs)):
                if self.webcam:
                    p, im0, _ = path[i], im0s[i].copy(), self.dataset.count
                    # s += f'{i}: '
                else:
                    p, im0, _ = path, im0s.copy(), getattr(self.dataset, 'frame', 0)

                p = Path(p)  # to Path
                # save_path = str(self.save_dir / p.name)  # im.jpg
                # txt_path = str(self.save_dir / 'labels' / p.stem) + ('' if self.dataset.mode == 'image' else f'_{frame}')  # im.txt
                # # s += '%gx%g ' % im.shape[2:]  # print string
                # gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                # imc = im0.copy() if self.config['save_crop'] else im0  # for save_crop
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
                        
                        if view_img:
                            label = str(cls) if self.config['hide_conf'] else f'{cls} {conf:.2f}'
                            annotator.box_label(xyxy, label)
                        
                        # if self.config['save_txt']:  # Write to file
                        #     xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        #     line = (cls, *xywh, conf) if self.config['save_conf'] else (cls, *xywh)  # label format
                        #     with open(f'{txt_path}.txt', 'a') as f:
                        #         f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        # if save_img or self.config['save_crop'] or view_img:
                        #     label = f'{cls} {conf:.2f}'
                        #     annotator.box_label(xyxy, label)
                            
                        # if self.config['save_crop']:
                        #     save_one_box(xyxy, imc, file=self.save_dir / 'crops' / cls / f'{p.stem}.jpg', BGR=True)
                            
                    
                    # 如果有obj都是要进入log的
                    self.logger.log(s)
                # 没检测到东西
                else:
                    self.logger.log('nothing')
                    

                # Stream results
                im0 = annotator.result()
                
                obj_queue.append('fire' in obj or 'Unknown' in obj)
                
                if anomaly_detected(obj_queue):
                    # 记录帧, 报警, 这两个要过滤重复
                    current_time = datetime.now()
                    if self.on_alarm:
                        print(alert_sent, last_time)
                        if not alert_sent or (current_time - last_time>self.patience):
                            curr = current_time.strftime("%Y-%m-%d_%H-%M-%S")
                            img_path = os.path.join(self.logger.current_log_dir, f'{s}_{curr}.jpg')
                            cv2.imwrite(img_path, im0)
                            alert_sent = self.alarm.send_alert('摄像机发现异常!', s, img_path)
                            
                            print('发送邮件')
                            last_time = current_time
                            # patience = self.patience
                        # else:
                        #     patience -= 1
                    # 录视频
                    if not recording:
                        recording = True
                        curr = current_time.strftime("%Y-%m-%d_%H-%M-%S")
                        video_path = os.path.join(self.logger.current_log_dir, f'{curr}.avi')
                        self.logger.log(f'开始录像, 录像保存至: {video_path}')
                        print('开始录像')
                        fps, w, h = 10, im0.shape[1], im0.shape[0]
                        video_writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                        video_writer.write(im0)
                # 停止录视频
                elif recording:
                        video_writer.write(im0)
                        frame_count += 1
                        if frame_count >= min_length:
                            # 达到最大录像长度或火情消失，停止录像
                            if anomaly_detected(obj_queue):
                                frame_count = 0
                            else:
                                recording = False
                                video_writer.release()
                                video_writer = None
                                frame_count = 0
                                self.logger.log(f'录像结束, 保存至{video_path}')
                                print(f'录像结束, 保存至{video_path}')
                
                # 这里是绘制 
                if self.config['view_img']:
                    if platform.system() == 'Linux' and p not in windows:
                        windows.append(p)
                        cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                        cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
                    cv2.imshow(str(p), im0)
                    cv2.waitKey(1)  # 1 millisecond
    
    
    # 使用yield方式只会在访问生成器的时候下一帧, 这会导致只能在打开网页的情况下才会推断
    # 传入一个socket异步传出数据
    def gen_frame_stream(self, socketio=None):
        
        # 简易的数据防抖, 在大小为7的窗口中如果出现了半数以上的异常帧才认为发生了异常
        # 这降低了报警和录像的敏感性, 节约了性能也降低了误报率
        obj_queue = deque(maxlen=7)
        
        def anomaly_detected(queue):
            if len(queue) < 7:
                return False
            if sum(queue) >= len(queue)/2:
                return True
            return False
        
        min_length = self.min_length  # 最大录像长度（单位：帧）
        alert_sent = False  # 标记是否已经发送警报
        recording = False  # 标记正在录像
        last_time = datetime.now()  # 标记上次警报时间
        video_writer = None
        view_img = check_imshow(warn=True)

        # 本地使用情况下展示窗口
        windows = []
        frame_count = 0
        
        for path, im, im0s, _ in self.dataset:
            
            preds, objs, im = self.infer_frame(im)
            # 面对多个线程在各自摄像头中读取出来的画面, 推断结果被总结成列表, 暂时还未实现
            # 所以这里解出来肯定是单元素的
            s = ''
            for i, (det, obj) in enumerate(zip(preds, objs)):
                # 取出原始帧的副本im0用于绘制
                if self.webcam:
                    p, im0, _ = path[i], im0s[i].copy(), self.dataset.count
                else:
                    p, im0, _ = path, im0s.copy(), getattr(self.dataset, 'frame', 0)
                p = Path(p)
                
                # 用于绘制识别结果的工具类
                annotator = Annotator(im0, line_width=self.config['line_thickness'])
                if len(det):
                    # 再缩放以便于绘制, [x1,y1,x2,y2,confidence], 前四列就是识别框
                    det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()
                    for c, n in Counter(obj).items():
                        s += f"{n} {c}{'s' * (n > 1)}, "
                        
                    for deti, cls in reversed(list(zip(det, obj))):
                        *xyxy, conf, _ = deti
                        if view_img:
                            label = str(cls) if self.config['hide_conf'] else f'{cls} {conf:.2f}'
                            annotator.box_label(xyxy, label)
                                            
                    # 如果有obj都是要进入log的
                    self.logger.log(s)
                # 没检测到东西
                else:
                    self.logger.log('nothing')
                
                
                
                
                
                im0 = annotator.result()    # 绘制好的帧
                obj_queue.append('fire' in obj or 'Unknown' in obj)
                if anomaly_detected(obj_queue):
                    # 记录帧, 报警, 这两个要过滤重复
                    current_time = datetime.now()
                    if self.on_alarm:   # 打开了报警开关
                        # print(alert_sent, last_time)
                        # 上次没成功报警或者已经过了一段时间
                        if not alert_sent or (current_time - last_time>self.patience):  
                            # 保存关键帧
                            curr = current_time.strftime("%Y-%m-%d_%H-%M-%S")
                            img_path = os.path.join(self.logger.current_log_dir, f'{s}_{curr}.jpg')
                            cv2.imwrite(img_path, im0)
                            # 发送警报
                            alert_sent = self.alarm.send_alert('摄像机发现异常!', s, img_path)
                            self.logger.log(f"成功发送警报邮件至: {self.config['recemail']}")
                            print('成功发送警报邮件')
                            last_time = current_time
                    # 不在录制视频那么开始录视频
                    if not recording:
                        recording = True
                        curr = current_time.strftime("%Y-%m-%d_%H-%M-%S")
                        video_path = os.path.join(self.logger.current_log_dir, f'{curr}.avi')
                        self.logger.log(f'开始录像, 录像保存至: {video_path}')
                        print('开始录像')
                        fps, w, h = 10, im0.shape[1], im0.shape[0]
                        # 产生一个新视频文件, 定义一个新的video_writer, write即可以往视频中写入帧
                        video_writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                        video_writer.write(im0)
                        
                        
                # 停止录视频
                elif recording:
                        video_writer.write(im0)
                        frame_count += 1
                        if frame_count >= min_length:
                            # 达到最低录像长度或火情消失，停止录像
                            if anomaly_detected(obj_queue):
                                frame_count = 0
                            else:
                                recording = False
                                video_writer.release()
                                video_writer = None
                                frame_count = 0
                                self.logger.log(f'录像结束, 保存至{video_path}')
                                print(f'录像结束, 保存至{video_path}')
                
                
                if socketio is not None:
                    # 将结果转换为base64编码
                    _, buffer = cv2.imencode('.jpg', im0)
                    frame_base64 = base64.b64encode(buffer)
                    socketio.emit('frame', frame_base64.decode())
                elif self.config['view_img']:
                    if platform.system() == 'Linux' and p not in windows:
                        windows.append(p)
                        cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO) 
                        cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
                    cv2.imshow(str(p), im0)
                    cv2.waitKey(1)
        
        return
    
def test():
    manager = detect_tasks_manager()
    manager.run_detect()

if __name__ == '__main__':
    test()