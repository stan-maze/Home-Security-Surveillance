import os
import cv2
import logging
import datetime






if not os.path.exists('log'):
    os.makedirs('log')



# 创建按时间命名的目录
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_dir = os.path.join('log', current_time)
os.makedirs(log_dir)
# 更新日志文件路径
log_file = os.path.join(log_dir, f'{current_time}.log')

# 配置日志记录
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 创建Logger对象
logger = logging.getLogger(__name__)


def detect(cnt):
    if cnt < 100:
        return False
    elif cnt <200:
        return True
    return False


# 视频相关参数
video_fps = 30.0
video_codec = cv2.VideoWriter_fourcc(*'XVID')
max_length = 300  # 最大录像长度（单位：帧）

# 确保视频保存目录存在

# 开始处理视频流
cap = cv2.VideoCapture(0)  # 从摄像头读取视频流
recording = False  # 是否正在录像
frame_count = 0  # 录像帧计数
video_writer = None  # 视频写入器



cnt = 0
while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
        break

    # 在此处调用火灾检测函数，返回检测结果
    # fire_detected = detect(frame)
    cnt += 1
    fire_detected = detect(cnt)

    if fire_detected:
        # 火灾检测到了
        print(f'{cnt} 火灾检测到了！')
        logger.info('火灾检测到了！')

        if not recording:
            # 开始录像
            recording = True
            video_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            video_path = os.path.join(log_dir, f'{video_filename}.avi')
            print(video_path)
            height, width, _ = frame.shape
            video_writer = cv2.VideoWriter(video_path, video_codec, video_fps, (width, height))
            logger.info('开始录像')
    else:
        print(cnt)
    if recording:
        # 录像中
        video_writer.write(frame)
        frame_count += 1

        if frame_count >= max_length or not fire_detected:
            # 达到最大录像长度或火情消失，停止录像
            recording = False
            video_writer.release()
            video_writer = None
            frame_count = 0
            logger.info('录像结束')

    # 在此处进行其他处理或显示视频帧

# 释放资源
cap.release()

# 关闭视频写入器
if video_writer is not None:
    video_writer.release()
