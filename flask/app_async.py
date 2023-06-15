from flask import Flask, render_template
import os
from flask_socketio import SocketIO

from config_page import config_page
from file_page import file_page
# from cam_page import cam_page
from cam_page_async import cam_page, gen_frame_stream

app = Flask(__name__)
socketio = SocketIO(app)

app.register_blueprint(config_page)
app.register_blueprint(file_page)
app.register_blueprint(cam_page)


@app.route('/')
def navigation():
    print(os.getpid())
    return render_template('index.html')

@socketio.on('connect', namespace='/cam')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/cam')
def handle_disconnect():
    print('Client disconnected')



# 重启路由
@app.route('/restart', methods=['POST'])
def restart():
    # 执行重启操作
    os._exit(0) 
    

if __name__ == '__main__':
    # print(os.getpid())
    # app.run()
    # 使用后台进程在服务启动时直接开始运行gen_frame_stream过程并将绘制帧传回socketio
    # 供前端展示, 这样后端不会被前端阻塞
    socketio.start_background_task(gen_frame_stream, socketio=socketio)
    socketio.run(app)
