import json
from flask import Flask, render_template, request

app = Flask(__name__)

# 配置文件路径
config_files = {
    'config1': 'config1.json',
    'config2': 'config2.json',
    'config3': 'config3.json',
    'config4': 'config4.json'
}


class Config:
    def __init__(self, file_path):
        self.file_path = file_path
        self.load_config()

    def load_config(self):
        with open(self.file_path, 'r') as file:
            config_data = json.load(file)
            for key, value in config_data.items():
                setattr(self, key, value)

    def save_config(self):
        config_data = {key: getattr(self, key) for key in self.__dict__ if not key.startswith('_')}
        with open(self.file_path, 'w') as file:
            json.dump(config_data, file, indent=4)


# 创建配置对象
configs = {config_name: Config(config_path) for config_name, config_path in config_files.items()}


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 获取表单提交的数据
        config_name = request.form['config_name']
        config = configs[config_name]
        for key in request.form:
            if key != 'config_name':
                setattr(config, key, request.form[key])
        config.save_config()

    # 渲染模板并传递配置文件数据
    return render_template('index.html', configs=configs)


if __name__ == '__main__':
    app.run()
