from flask import render_template, Blueprint
# from flask_socketio import SocketIO, emit
# import cv2
# import base64
# import time

import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from detector import detect_tasks_manager

manager = detect_tasks_manager()

cam_page = Blueprint('cam_page', __name__, url_prefix='/cam')

def gen_frame_stream(*args, **kwargs):
    # manager = create_manager()
    return manager.gen_frame_stream(*args, **kwargs)

@cam_page.route('/')
def index():
    return render_template('async.html')

if __name__ == '__main__':
    pass
    # socketio.start_background_task(manager.gen_frame_stream, socketio=socketio)
    # # socketio.start_background_task(process_frame)
    # socketio.run(app)
