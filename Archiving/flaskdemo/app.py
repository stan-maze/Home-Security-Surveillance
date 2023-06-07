from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

# 注册蓝图
from cam import cam_bp, process_frame
app.register_blueprint(cam_bp)


@socketio.on('connect', namespace='/cam')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/cam')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.start_background_task(process_frame, socketio=socketio)
    socketio.run(app)
