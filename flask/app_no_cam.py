from flask import Flask, render_template
import os
from flask_socketio import SocketIO

from config_page import config_page
from file_page import file_page
# from cam_page import cam_page
# from cam_page_async import cam_page, gen_frame_stream

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def navigation():
    print(os.getpid())
    return render_template('index.html')

# 重启路由
@app.route('/restart', methods=['POST'])
def restart():
    # 执行重启操作
    os._exit(0)
    

app.register_blueprint(config_page)
app.register_blueprint(file_page)


if __name__ == '__main__':
    print(os.getpid())
    # app.run()
    # socketio.start_background_task(gen_frame_stream, socketio=socketio)
    socketio.run(app)
