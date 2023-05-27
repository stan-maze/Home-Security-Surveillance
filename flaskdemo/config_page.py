from flask import Flask, render_template, request, redirect, url_for, send_file
import json
import os

app = Flask(__name__)

dirpath = os.path.dirname(os.path.abspath(__file__))
dirpath = os.path.dirname(dirpath)

@app.route('/facerec/images/<filename>', methods=['GET'])
def get_facerec_image(filename):
    image_path = os.path.join(dirpath, 'facerec', 'api', 'data', 'images', filename)
    # Perform necessary validations and security checks on image_path

    return send_file(image_path, mimetype='image/jpeg')  # Adjust the mimetype as per your image format


# 配置文件路径
config_files = [
    # 控制器参数
    '../config.json',
    # 日志保存/报警参数
    '../config.json',
    # 人脸识别参数, 这个要多花点功夫, 显示图片
    '../facerec/api/data/faces.json',
    # 火焰识别参数
    '../firedet/api/fire_detector/config.json'
]

# 读取配置文件
def read_config(file):
    with open(file, 'r') as f:
        config = json.load(f)
    return config

# 保存配置文件
def save_config(file, config):
    with open(file, 'w') as f:
        json.dump(config, f, indent=4)

# 注册自定义过滤器
@app.template_filter('is_bool')
def is_bool(value):
    return isinstance(value, bool)

@app.template_filter('is_int')
def is_int(value):
    return isinstance(value, int)

@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate, list=list)

# 主页路由
@app.route('/')
def index():
    # 读取配置文件内容
    configs = []
    for i, file in enumerate(config_files):
        config = read_config(file)
        configs.append(config)

    return render_template('index.html', configs=configs)

# 编辑配置文件路由
@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit(index):
    file = config_files[index]
    config = read_config(file)

    if request.method == 'POST':
        # 更新配置文件内容
        for key in config:
            if isinstance(config[key], bool):
                config[key] = False

        for key, value in request.form.items():
            if isinstance(config[key], bool):
                config[key] = bool(value)
            elif isinstance(config[key], int):
                config[key] = int(value)
            else:
                config[key] = value
        save_config(file, config)
        return redirect(url_for('index'))

    return render_template('edit.html', config=config, index=index)

# 删除图片路由
@app.route('/delete-image/<filename>', methods=['GET'])
def delete_image(filename):
    image_path = os.path.join(dirpath, 'facerec', 'api', 'data', 'images', filename)
    # Perform necessary validations and security checks on image_path

    config = read_config(config_files[2])
    for key, value in config.items():
        if filename in value:
            config[key].remove(filename)
            break
    save_config(config_files[2], config)

    # Delete the image file
    if os.path.exists(image_path):
        os.remove(image_path)
        return redirect(url_for('index'))
    else:
        return "Image not found"


# 上传图片路由
@app.route('/upload-image', methods=['POST'])
def upload_image():
    config_key = request.form.get('config_key')
    image_file = request.files.get('image')
    print(config_key)

    if image_file:
        
        config = read_config(config_files[2])
        filename = f'{config_key}{len(config[config_key])+1}.jpg'
        # 保存上传的图像
        save_path = os.path.join(dirpath, 'facerec', 'api', 'data', 'images', filename)
        image_file.save(save_path)

        # 更新配置文件中的图像信息
        config_file = config_files[2]
        config = read_config(config_file)
        if config_key in config:
            config[config_key].append(filename)
        else:
            config[config_key] = [filename]
        save_config(config_file, config)

        return redirect(url_for('index'))

    return "Invalid image file"


if __name__ == '__main__':
    app.run()

