from flask import Flask, render_template, request, redirect, url_for, send_file
import json
import os


app = Flask(__name__)

dirpath = os.path.dirname(os.path.abspath(__file__))
dirpath = os.path.dirname(dirpath)

@app.route('/facerec/images/<filename>', methods=['GET'])
def get_facerec_image(filename):
    print(dirpath)
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
    return dict(enumerate=enumerate)


# 主页路由
@app.route('/')
def index():
    # 读取配置文件内容
    configs = []
    for i, file in enumerate(config_files):
        config = read_config(file)
        # if i == 2:
        #     print(config)
        #     for name, paths in config.items():
        #         config[name] = [f'{faceimg_path}/{path}' for path in paths]
            
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
            # 无用的, 因为不会传true/false, 传的是checkbox的on, close也不会传
            if isinstance(config[key], bool):
                config[key] = bool(value)
                # print('bool', key, value)
            elif isinstance(config[key], int):
                config[key] = int(value)
            else:
                config[key] = value
        save_config(file, config)
        return redirect(url_for('index'))
    
    return render_template('edit.html', config=config, index=index)

if __name__ == '__main__':
    app.run(debug=True)
