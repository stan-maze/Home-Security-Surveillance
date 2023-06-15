# coding:utf-8
import os
import glob
import time
import numpy as np
from pathlib import Path
from threading import Thread
from utils.augmentations import letterbox
from utils.general import clean_str, cv2

img_formats = ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff', 'dng', 'webp']  # 可接受的图像后缀
vid_formats = ['mov', 'avi', 'mp4', 'mpg', 'mpeg', 'm4v', 'wmv', 'mkv']  # 可接受的视频后缀

class LoadImages:  # 用于推理的加载图像类
    def __init__(self, path, img_size=640, stride=32):
        p = str(Path(path).absolute())  # 跨平台的绝对路径
        if '*' in p:
            files = sorted(glob.glob(p, recursive=True))  # glob
        elif os.path.isdir(p):
            files = sorted(glob.glob(os.path.join(p, '*.*')))  # 目录
        elif os.path.isfile(p):
            files = [p]  # 文件
        else:
            print(p)
            raise Exception(f'ERROR: {p} 不存在')

        images = [x for x in files if x.split('.')[-1].lower() in img_formats]
        videos = [x for x in files if x.split('.')[-1].lower() in vid_formats]
        ni, nv = len(images), len(videos)

        self.img_size = img_size
        self.stride = stride
        self.files = images + videos
        self.nf = ni + nv  # 文件数量
        self.video_flag = [False] * ni + [True] * nv
        self.mode = 'image'
        if any(videos):
            self.new_video(videos[0])  # 新的视频
        else:
            self.cap = None
        assert self.nf > 0, f'{p} 中没有找到图像或视频文件。支持的格式有：\n图像：{img_formats}\n视频：{vid_formats}'

    def __iter__(self):
        self.count = 0
        return self

    def __next__(self):
        if self.count == self.nf:
            raise StopIteration
        path = self.files[self.count]

        if self.video_flag[self.count]:
            # 读取视频
            self.mode = 'video'
            ret_val, img0 = self.cap.read()
            if not ret_val:
                self.count += 1
                self.cap.release()
                if self.count == self.nf:  # 最后一个视频
                    raise StopIteration
                else:
                    path = self.files[self.count]
                    self.new_video(path)
                    ret_val, img0 = self.cap.read()

            self.frame += 1
            print(f'video {self.count + 1}/{self.nf} ({self.frame}/{self.nframes}) {path}: ', end='')

        else:
            # 读取图像
            self.count += 1
            img0 = cv2.imread(path)  # BGR
            assert img0 is not None, '未找到图像 ' + path
            print(f'image {self.count}/{self.nf} {path}: ', end='')

        # 填充调整大小
        img = letterbox(img0, self.img_size, stride=self.stride)[0]

        # 转换
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB，变成3x416x416
        img = np.ascontiguousarray(img)

        return path, img, img0, self.cap

    def new_video(self, path):
        self.frame = 0
        self.cap = cv2.VideoCapture(path)
        self.nframes = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def __len__(self):
        return self.nf  # 文件数量

class LoadWebcam:  # 用于推理的加载摄像头类
    def __init__(self, pipe='0', img_size=640, stride=32):
        self.img_size = img_size
        self.stride = stride

        if pipe.isnumeric():
            pipe = eval(pipe)  # 本地摄像头
        # pipe = 'rtsp://192.168.1.64/1'  # IP摄像头
        # pipe = 'rtsp://username:password@192.168.1.64/1'  # 带有登录的IP摄像头
        # pipe = 'http://wmccpinetop.axiscam.net/mjpg/video.mjpg'  # IP高尔夫摄像头

        self.pipe = pipe
        self.cap = cv2.VideoCapture(pipe)  # 视频捕获对象
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # 设置缓冲区大小

    def __iter__(self):
        self.count = -1
        return self

    def __next__(self):
        self.count += 1
        if cv2.waitKey(1) == ord('q'):  # 按下q退出
            self.cap.release()
            cv2.destroyAllWindows()
            raise StopIteration

        # 读取帧
        if self.pipe == 0:  # 本地摄像头
            ret_val, img0 = self.cap.read()
            img0 = cv2.flip(img0, 1)  # 左右翻转
        else:  # IP摄像头
            n = 0
            while True:
                n += 1
                self.cap.grab()
                if n % 30 == 0:  # 跳过帧
                    ret_val, img0 = self.cap.retrieve()
                    if ret_val:
                        break

        # 打印
        assert ret_val, f'摄像头错误 {self.pipe}'
        img_path = 'webcam.jpg'
        print(f'webcam {self.count}: ', end='')

        # 填充调整大小
        img = letterbox(img0, self.img_size, stride=self.stride)[0]

        # 转换
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB，变成3x416x416
        img = np.ascontiguousarray(img)

        return img_path, img, img0, None

    def __len__(self):
        return 0

class LoadStreams:
    def __init__(self, sources='0', img_size=640, stride=32):
        self.mode = 'stream'
        self.img_size = img_size
        self.stride = stride

        if os.path.isfile(sources):
            with open(sources, 'r') as f:
                sources = [x.strip() for x in f.read().strip().splitlines() if len(x.strip())]
        else:
            sources = [sources]

        n = len(sources)
        self.imgs = [None] * n
        self.sources = [clean_str(x) for x in sources]  # 清理源名称以备后用
        for i, s in enumerate(sources):
            # 启动线程从视频流中读取帧
            print(f'{i + 1}/{n}: {s}... ', end='')
            cap = cv2.VideoCapture(eval(s) if s.isnumeric() else s)
            assert cap.isOpened(), f'无法打开 {s}'
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) % 100
            _, self.imgs[i] = cap.read()  # 确保第一帧
            # 启用线程处理, 这是提供同时对多个摄像头读取的支持, 尚未开发
            thread = Thread(target=self.update, args=([i, cap]), daemon=True)
            print(f' 成功 ({w}x{h} at {fps:.2f} FPS).')
            thread.start()
        print('')

        # 检查常见的形状
        s = np.stack([letterbox(x, self.img_size, stride=self.stride)[0].shape for x in self.imgs], 0)  # 形状
        self.rect = np.unique(s, axis=0).shape[0] == 1  # 如果所有形状都相等，则进行矩形推理
        if not self.rect:
            print('警告：检测到不同的流形状。为了获得最佳性能，请提供形状相似的流。')

    def update(self, index, cap):
        # 在守护线程中读取下一个流帧
        n = 0
        while cap.isOpened():
            n += 1
            # _, self.imgs[index] = cap.read()
            # 使用grab取帧
            cap.grab()
            # if n == 4:  # 每4帧读取一帧
            if n == 4:  # 每4帧读取一帧
                success, im = cap.retrieve()
                self.imgs[index] = im if success else self.imgs[index] * 0
                n = 0
            time.sleep(0.01)  # 等待时间

    def __next__(self):
        self.count += 1
        img0 = self.imgs.copy()
        if cv2.waitKey(1) == ord('q'):  # 按下q退出
            cv2.destroyAllWindows()
            raise StopIteration

        img = [letterbox(x, self.img_size, auto=self.rect, stride=self.stride)[0] for x in img0]
        img = np.stack(img, 0)

        # 前处理, 将BGR转化成RGB帧
        img = img[:, :, :, ::-1].transpose(0, 3, 1, 2)
        img = np.ascontiguousarray(img)

        return self.sources, img, img0, None

    def __iter__(self):
        self.count = -1
        return self
    
    def __len__(self):
        # 摄像头画面流不是靠长度终止的, 这个方法也确保不会被调用
        return 0
