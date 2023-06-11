import os
from flask import Flask, render_template, send_from_directory, url_for, Blueprint

file_page = Blueprint('file_page', __name__)

# log文件夹
root_folder_path = os.path.abspath('../log')

def get_folder_structure(folder_path):
    folder_structure = []
    # 递归地访问目录，构建文件列表
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            folder_structure.append({
                'name': item,
                'type': 'folder',
                'path': os.path.normpath(os.path.relpath(item_path, root_folder_path))
            })
        else:
            folder_structure.append({
                'name': item,
                'path': os.path.normpath(os.path.relpath(item_path, root_folder_path)),
                'type': 'file'
            })
    return folder_structure


@file_page.route('/log/')
def index():
    # 调用递归函数获取根文件夹的目录结构
    folder_structure = get_folder_structure(root_folder_path)
    # 渲染模板并传递根文件夹的目录结构
    return render_template('file.html', folder_structure=folder_structure)


@file_page.route('/log/download/<path:folder_path>')
def download(file_path):
    # 构建文件的完整路径
    full_path = os.path.join(root_folder_path, file_path)
    print('now download', full_path)

    # 检查文件是否存在
    if os.path.isfile(full_path):
        # 提供文件下载，参数依次为，目录名，文件名，下载开关(as_attachment=True说明文件会以附件形式下载)
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), as_attachment=True)
    else:
        # 文件不存在，返回错误示信息
        return 'File not found'


@file_page.route('/log/preview/<path:file_path>')
def preview(file_path):
    # 构建文件的完整路径
    full_path = os.path.join(root_folder_path, file_path)
    print('now preview', full_path)

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
    # 返回错误信息
    return 'Preview not available'


@file_page.route('/log/browse/<path:folder_path>')
def browse(folder_path):
    parent_path = os.path.dirname(folder_path)
    print('folder_path', folder_path)
    print('parent_path', parent_path)
    # 构建文件夹的完整路径
    folder_full_path = os.path.join(root_folder_path, folder_path)
    # 调用递归函数获取文件夹的目录结构
    folder_structure = get_folder_structure(folder_full_path)
    print('now browse', folder_full_path)
    
    # 渲染模板并传递当前文件夹路径和目录结构
    return render_template('file.html', current_path=folder_path, folder_structure=folder_structure, parent_path=parent_path)





if __name__ == '__main__':
    # file_page.run(host='localhost', port=5002)
    pass