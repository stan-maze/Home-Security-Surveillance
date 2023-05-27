import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# 定义要浏览的根文件夹路径
root_folder_path = '../total_log'  # 替换为你的根文件夹路径


@app.route('/')
def index():
    # 调用递归函数获取根文件夹的目录结构
    folder_structure = get_folder_structure(root_folder_path)
    # 渲染模板并传递根文件夹的目录结构
    return render_template('file.html', folder_structure=folder_structure)


@app.route('/download/<path:file_path>')
def download(file_path):
    # 构建文件的完整路径
    full_path = os.path.join(root_folder_path, file_path)
    # 检查文件是否存在
    if os.path.isfile(full_path):
        # 提供文件下载
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), as_attachment=True)
    else:
        # 文件不存在，返回错误页面或提示信息
        return render_template('error.html', message='File not found')


@app.route('/preview/<path:file_path>')
def preview(file_path):
    # 构建文件的完整路径
    full_path = os.path.join(root_folder_path, file_path)
    # 检查文件是否存在
    if os.path.isfile(full_path):
        # 获取文件扩展名
        file_extension = os.path.splitext(file_path)[1].lower()
        # 根据文件扩展名选择模板文件和内容显示方式
        if file_extension == '.jpg':
            # 如果是.jpg文件，则渲染图片预览页面
            return render_template('preview.html', file_path=file_path, file_type='image')
        elif file_extension == '.log':
            # 如果是.log文件，则渲染文本预览页面，并显示文件内容
            with open(full_path, 'r') as file:
                content = file.read()
            return render_template('preview.html', file_path=file_path, file_type='text', content=content)
    # 文件不存在或不支持预览，返回错误页面或提示信息
    return render_template('error.html', message='Preview not available')


def get_folder_structure(folder_path):
    folder_structure = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            folder_structure.append({
                'name': item,
                'type': 'folder',
                'children': get_folder_structure(item_path)
            })
        else:
            folder_structure.append({
                'name': item,
                'type': 'file'
            })
    return folder_structure


if __name__ == '__main__':
    app.run()
