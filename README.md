# Home-Security-Surveillance
通过(摄像头)视频流检测火情和非法闯入, 火情识别基于yolov5模型, 非法闯入基于人脸识别, 目前是基于dlib(opencv), 并支持部署应用到服务器支持远程查看和修改参数

## 主要模块

- facerec模块, 支持人脸识别和录入, 基于dlib库
- firedet模块, 支持火焰识别, 模型训练, 基于yolov5的backbone
- 数据流处理模块, 尚未单独分离, 原型在demo中对视频流做前后处理, 基于迭代器和opencv管理视频流
- app模块, 服务器应用, 基于flask框架



## 文件还比较乱, 具体的两个检测器在
```
facerec\api\face_recognizer
firedet\api\fire_detector
```
安装相关的库, 主要是torch, scipy, dlib和opencv
```
pip install -r requirements.txt
```
安装face_recognition的时候可能有点问题, 是因为dlib导致的,  可以试试先手动安装cmake, boost, 再用conda安装dlib, 再重新安装face_recognition
```
pip install cmake, boost
```
## 运行demo
```
python3 demo.py
```
## 运行网页app, 需要安装flask, 然后去提示网址
```
pip install flask
python3 app.py
```

## 各功能细节
### 人脸识别
### 火焰识别
### 数据流处理
### 网页app

### 告警和log
通过检查objs(每帧识别结果)判断是否存在异常情况, 但是仅检查一帧结果容易出现误报, 添加了一个deque用来缓冲, 当异常帧达到一定数量时再启动报警程序以避免告警过于敏感
通过logging模块保存识别结果, 可以定义日志最大存储空间/数量, 以及设置轮转, 同时设置preprocess对超过7天的日志文件压缩, 超过30天的日志文件释放
通过cv2也可以方便地保存视频和关键帧, 同样利用上面的缓冲队列以降低敏感度
暂时报警系统用邮件替代, 利用smtplib模块可以便捷发送邮件及附图, 同样利用上面的缓冲队列以降低敏感度



## TODO

- face_recognizer:
    - 调用的api很简单, 可以自己复写
    - 选择的dlib模型选择可以进一步考察
- fire_detector由yolov5项目改造而来, 清理非必要的文件
- 配置文件的管理:
    - 是否分离face_recognizer和fire_detector
    - 网页配置页以及服务的重启
- 告警服务的形式
- logging, 包括日志文件以及图像保存
