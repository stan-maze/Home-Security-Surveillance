from flask import Blueprint, render_template
from flask_socketio import emit
import cv2
import base64
import time

cam_bp = Blueprint('cam', __name__)

# 简单的 infer 函数：将图像转换为灰度图并记录时间到日志文件
def infer(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return gray_frame

# 模拟获取帧 frame 并进行分析
def process_frame(socketio):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 进行推理
        res = infer(frame)
        
        # 将结果转换为base64编码
        _, buffer = cv2.imencode('.jpg', res)
        frame_base64 = base64.b64encode(buffer)

        # 将结果发送给客户端
        socketio.emit('frame', frame_base64.decode(), namespace='/cam')
        # socketio.emit('frame', frame_base64.decode(), namespace='/cam')
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open("log.txt", "a") as f:
            f.write(f"Inference time: {timestamp}\n")
        time.sleep(1)
        print(timestamp)

    cap.release()

@cam_bp.route('/as')
def index():
    return render_template('async.html')