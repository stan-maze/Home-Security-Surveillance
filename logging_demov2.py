import os
import cv2
import logging
import logging.handlers
import datetime

import shutil
import datetime
import tarfile
import glob
import os

from utils.alert import send_email

log_dir = 'log'  # 日志目录路径
archive_dir = 'log_archive'  # 归档目录路径
for required_dir in (log_dir, archive_dir):
    if not os.path.exists(required_dir):
        os.makedirs(required_dir)

def preprocess():
    current_time = datetime.datetime.now()
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    # 清理超过一个月的日志归档记录
    one_month_ago = current_time - datetime.timedelta(seconds=30)
    for archive_file in glob.glob(os.path.join(archive_dir, '*.tar.gz')):
        modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(archive_file))
        if modified_time < one_month_ago:
            os.remove(archive_file)
            print(f"Deleted archived log file: {archive_file}")

    # 归档超过一周的日志目录并压缩
    one_week_ago = current_time - datetime.timedelta(days=7)
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


def detect(cnt):
    if cnt < 100:
        return False
    elif cnt < 500:
        return True
    return False


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

def logging():

    # 视频相关参数
    video_fps = 30.0
    video_codec = cv2.VideoWriter_fourcc(*'XVID')
    max_length = 300  # 最大录像长度（单位：帧）

    # 开始处理视频流
    cap = cv2.VideoCapture(0)  # 从摄像头读取视频流
    recording = False  # 是否正在录像
    frame_count = 0  # 录像帧计数
    video_writer = None  # 视频写入器

    cnt = 0
    em_sent = False
    # 应该是一个config
    alerts, patience, recemail = True, 0, '2311306511@qq.com'
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        cnt += 1
        fire_detected = detect(cnt)

        if fire_detected:
            # 火灾检测到了
            print(f'{cnt} 火灾检测到了！')
            logger.info(f'{cnt} 火灾检测到了！')
            
            if alerts:
                print(em_sent, patience)
                if not em_sent or patience == 0:
                    em_sent = send_email(recemail, '火, 火!', '你嫲喊你回家灭火')
                    patience = 1000
                else:
                    patience -= 1

            if not recording:
                # 开始录像
                recording = True
                video_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                video_path = os.path.join(current_log_dir, f'{video_filename}.avi')
                print(video_path)
                height, width, _ = frame.shape
                video_writer = cv2.VideoWriter(video_path, video_codec, video_fps, (width, height))
                logger.info('开始录像')
        else:
            print(cnt)
            logger.info(cnt)

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

    # 释放资源
    cap.release()

    # 关闭日志处理器
    log_handler.close()
    logger.removeHandler(log_handler)


if __name__ == '__main__':
    preprocess()
    logging()