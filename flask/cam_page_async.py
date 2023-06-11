from flask import render_template, Blueprint

import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from detector import detect_tasks_manager

manager = detect_tasks_manager()

cam_page = Blueprint('cam_page', __name__, url_prefix='/cam')

def gen_frame_stream(*args, **kwargs):
    return manager.gen_frame_stream(*args, **kwargs)

@cam_page.route('/')
def index():
    return render_template('cam_async.html')

if __name__ == '__main__':
    pass
    # socketio.start_background_task(manager.gen_frame_stream, socketio=socketio)
    # # socketio.start_background_task(process_frame)
    # socketio.run(app)
