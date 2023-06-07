from flask import Response, Flask, render_template
from detector import detect_tasks_manager

app = Flask(__name__)


manager = detect_tasks_manager()


@app.route("/")
def index():
    return render_template("index.html")

@app.route('/video_feed/<feed_type>')
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
    app.run(host='localhost', port=5000)