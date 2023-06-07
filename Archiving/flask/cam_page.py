from flask import Response, Flask, render_template, Blueprint
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from detector import detect_tasks_manager


cam_page = Blueprint('cam_page', __name__)


manager = detect_tasks_manager()


@cam_page.route("/cam/")
def index():
    return render_template("cam.html")

@cam_page.route('/cam/video_feed/<feed_type>')
def video_feed(feed_type):
    """Video streaming route. Put this in the src attribute of an img tag."""
    if feed_type == 'Camera_0':
        return Response(manager.gen_frame(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
        
        
def test():
    manager = detect_tasks_manager()
    manager.run_detect()

if __name__ == '__main__':
    # test()
    # app.run(host='localhost', port=5000)
    pass