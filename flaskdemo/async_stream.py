from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
import base64
import time

app = Flask(__name__)
socketio = SocketIO(app)

# 客户端连接事件
@socketio.on('connect')
def handle_connect():
    print('Client connected')

# 客户端断开连接事件
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# 简单的 infer 函数：将图像转换为灰度图并记录时间到日志文件
def infer(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return gray_frame

# 模拟获取帧 frame 并进行分析
def process_frame():
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
        socketio.emit('frame', frame_base64.decode())
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open("log.txt", "a") as f:
            f.write(f"Inference time: {timestamp}\n")
        time.sleep(1)

    cap.release()

@app.route('/')
def index():
    return render_template('async.html')

if __name__ == '__main__':
    socketio.start_background_task(process_frame)
    socketio.run(app)
