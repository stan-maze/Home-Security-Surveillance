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
```facerec/api/face_recognizer/face_recognizer.py```

首先将已知人脸文件夹和配置读入(```facerec/api/data```), 计算/保存已知人脸的encoding, 提供infer方法接收帧, 首先抓取人脸, 没有抓取到则返回空识别结果, 否则计算该人脸的encoding与已知人脸匹配, 选出 置信度最高并且超过阈值 的, 如果没有超过阈值的, 认为这个人脸不属于数据库中的人脸, 鉴定为非法传入, 传出识别结果
### 火焰识别
```firedet/api/fire_detector/fire_detector.py```

使用yolov5s模型训练火焰样本, 数据集基于网络数据集, 见(```firedet/api/firedetor/data/fire_config.yaml```), 训练好的模型权重为(```best.pt```), 模块首先载入权重以及其他一些配置信息(如设备阈值等), 然后同样提供infer方法读入帧并推断火焰, 同样传出识别结果
### 数据流处理
```detector.py/init_dataloader```
```utils/camera.py```

将视频流(摄像头/文件视频)包装成迭代器, 使得可以通过for循环迭代视频流以便捷调用识别模块(infer), 迭代器的封装主要基于cv2封装的cv2.VideoCapture捕捉视频流, 在读出camera/video的帧后, 添加resize/BGR2RGB/连续化等操作, 见(```utils/camera.py/LoadStreams```)
在迭代帧的时候, 针对识别结果, 要嵌入log, 告警模块
### 网页app
```flask/```

基于flask框架快速开发, 包括四个主要功能:
- 配置页(```flask/config_page.py```), 人脸识别/火焰识别/log/报警等功能都有相应的配置文件, 为了减小耦合各个配置文件独立, 配置页要求做到读取,显示,修改,保存各个模块的配置信息, 特别是要支持人脸图像的增删修改
- 日志页(```flask/file_page.py```), 日志文件包括文本log, 关键帧/录像, 旧日志的压缩文件, 日志页要求只读地访问整个日志文件夹, 对于文本log和关键帧图像支持在线预览, 对于录像和压缩文件支持保存
- 视频页(```flask/cam_page_async.py```), 支持在线查看当前摄像头的识别情况, 实现方式是在数据流模块中添加一个socket管道, 将绘制好的识别结果帧传出到前端, 前端读取管道取出帧并绘制, 同时页面后端也需要实现为异步模式(初始版本是将识别器的数据流模块设置成生成器, 但这样同步的设置导致前端一旦关闭, 后端识别也将暂停)
- 导航页(```flask/app_async.py```), 使用flask的蓝图模块封装上面三个界面, 在导航页载入生成, 添加跳转链接, 设置好异步socketio管道, 导航页由守护进程(```flask/runService.bat```)执行, 因此可以通过直接关闭进程让守护进程重启程序
### 告警和log
```detector.py/init_logger```
```utils/alert.py```


通过检查objs(每帧识别结果)判断是否存在异常情况, 但是仅检查一帧结果容易出现误报, 添加了一个deque用来缓冲, 当异常帧达到一定数量时再启动报警程序以避免告警过于敏感
通过logging模块保存识别结果, 可以定义日志最大存储空间/数量, 以及设置轮转, 同时设置preprocess对超过7天的日志文件压缩, 超过30天的日志文件释放
通过cv2也可以方便地保存视频和关键帧, 暂时报警系统用邮件替代, 利用smtplib模块可以便捷发送邮件及附图, 同样利用上面的缓冲队列以降低敏感度



## TODO
- [ ] face_recognizer:
    - [ ] 调用的api很简单, 可以自己复写
    - [ ] 选择的dlib模型选择可以进一步考察
    - [ ] 多张人脸能否提高识别能力
<!-- - [ ] fire_detector由yolov5项目改造而来, 清理非必要的文件 -->
- [x] 配置文件的管理:
    - [x] 是否分离face_recognizer和fire_detector
    - [x] 网页配置页, 日志页
    - [x] 服务的重启功能
- [x] 告警服务的形式
- [x] logging, 包括日志文件以及图像保存
- [x] 混乱的import关系和util
