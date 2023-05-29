from flask import Flask, render_template
import sys, os

app = Flask(__name__)

@app.route('/')
def navigation():
    return render_template('index.html')


# 重启路由
@app.route('/restart', methods=['POST'])
def restart():
    # 执行重启操作
    python = sys.executable
    os.execl(python, python, *sys.argv)
    os._exit(0)

from config_page import config_page
from file_page import file_page
from cam_page import cam_page

# app.register_blueprint(config_page, url_prefix='/config')
# app.register_blueprint(file_page, url_prefix='/log')

app.register_blueprint(config_page)
app.register_blueprint(file_page)
app.register_blueprint(cam_page)


# ...其他配置和路由

if __name__ == '__main__':
    app.run()
