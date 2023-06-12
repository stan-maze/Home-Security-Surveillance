from flask import Flask, render_template, request, redirect, url_for, send_file, Blueprint
import json
import os

config_page = Blueprint('config_page', __name__)

dirpath = os.path.dirname(os.path.abspath(__file__))
dirpath = os.path.dirname(dirpath)

# 配置文件路径
config_files = [
    # 控制器参数
    os.path.join(dirpath, 'config.json'),
    # 火焰识别参数
    os.path.join(dirpath, 'firedet', 'api', 'fire_detector', 'config.json'),
    # 人脸识别参数, 这个要多花点功夫, 显示图片
    os.path.join(dirpath, 'facerec', 'api', 'data', 'faces.json')
    
    # '../config.json',
    # '../firedet/api/fire_detector/config.json'
    # '../facerec/api/data/faces.json',
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
@config_page.app_template_filter('is_bool')
def is_bool(value):
    return isinstance(value, bool)

@config_page.app_template_filter('is_int')
def is_int(value):
    return isinstance(value, int)

@config_page.app_context_processor
def inject_enumerate():
    return dict(enumerate=enumerate, list=list)


# 主页路由
@config_page.route('/config')
def index():
    # 读取配置文件内容
    configs = []
    for i, file in enumerate(config_files):
        print(file)
        config = read_config(file)
        configs.append(config)

    return render_template('config.html', configs=configs)

# 编辑配置文件路由
@config_page.route('/config/edit/<int:index>', methods=['GET', 'POST'])
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
            elif isinstance(config[key], float):
                config[key] = float(value)
            else:
                config[key] = value
        save_config(file, config)
        return redirect(url_for('config_page.index'))

    return render_template('edit.html', config=config, index=index)


@config_page.route('/config/facerec/images/<filename>', methods=['GET'])
def get_facerec_image(filename):
    image_path = os.path.join(dirpath, 'facerec', 'api', 'data', 'images', filename)
    return send_file(image_path, mimetype='image/jpeg')




# 删除图片路由
@config_page.route('/config/delete-image/<filename>', methods=['GET'])
def delete_image(filename):
    image_path = os.path.join(dirpath, 'facerec', 'api', 'data', 'images', filename)
    # 必然人脸配置页,直接读取第2个
    config = read_config(config_files[2])
    # 首先修改配置
    for key, value in config.items():
        # 删除配置项中这张图片的信息
        if filename in value:
            config[key].remove(filename)
            # 如果是该人最后一张图片，则此人的信息也要删除
            if len(config[key]) == 0:
                config.pop(key, None)
            break
    save_config(config_files[2], config)

    if os.path.exists(image_path):
        # 然后是真正删除图片
        os.remove(image_path)
        return redirect(url_for('config_page.edit', index=2))
    else:
        return "Image not found"


# 上传图片路由
@config_page.route('/config/upload-image', methods=['POST'])
def upload_image():
    config_key = request.form.get('config_key')
    newperson = request.form.get('name')
    image_file = request.files.get('image')
    print(config_key)

    if image_file:
        config = read_config(config_files[2])

        # 更新配置文件中的图像信息
        config_file = config_files[2]
        config = read_config(config_file)
        # 有两种上传方式，一种是已有的人上传新的图片，另一种是新建用户的图片
        if newperson:   # 新建用户的图片
            filename = f'{newperson}{1}.jpg'
            # 保存上传的图像
            save_path = os.path.join(dirpath, 'facerec', 'api', 'data', 'images', filename)
            config[newperson] = [filename]
        else:
            filename = f'{config_key}{len(config[config_key])+1}.jpg'
            # 保存上传的图像
            save_path = os.path.join(dirpath, 'facerec', 'api', 'data', 'images', filename)
            config[config_key].append(filename)
        image_file.save(save_path)
        save_config(config_file, config)

        return redirect(url_for('config_page.edit', index=2))

    return "请上传图片!"


if __name__ == '__main__':
    # config_page.run(host='localhost', port=5001)
    pass
