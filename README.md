# Home-Security-Surveillance
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
```
```
python3 app.py
```
