import os
import sys
from pathlib import Path


FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

CURRENT_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(os.path.dirname(CURRENT_PATH))

config_PATH = os.path.join(DIR_PATH, 'fire_detector','config.json')

from models.common import DetectMultiBackend
from utils.general import check_img_size, non_max_suppression
from utils.torch_utils import select_device, smart_inference_mode

import json

class fire_detector:
    def __init__(self) -> None:
        with open(config_PATH, 'r') as f:
            config = json.load(f)
            if 'weights' in config:
                config['weights'] = ROOT / f"{config['weights']}"
            if 'data' in config:
                config['data'] = ROOT / f"{config['data']}"
            if 'project' in config:
                config['project'] = ROOT / f"{config['project']}"
            self.init_model(**config)
            self.load_model()
        
    def init_model(self, 
                weights=ROOT / 'yolov5s.pt',  # model path or triton URL
                source=ROOT / 'data/images',  # file/dir/URL/glob/screen/0(webcam)
                data=ROOT / 'data/fire_config.yaml',  # dataset.yaml path
                imgsz=(640, 640),  # inference size (height, width)
                conf_thres=0.25,  # confidence threshold
                iou_thres=0.45,  # NMS IOU threshold
                max_det=100,  # maximum detections per image
                device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
                view_img=False,  # show results
                save_txt=False,  # save results to *.txt
                save_conf=False,  # save confidences in --save-txt labels
                save_crop=False,  # save cropped prediction boxes
                nosave=False,  # do not save images/videos
                classes=None,  # filter by class: --class 0, or --class 0 2 3
                agnostic_nms=False,  # class-agnostic NMS
                augment=False,  # augmented inference
                visualize=False,  # visualize features
                update=False,  # update all models
                project=ROOT / 'runs/detect',  # save results to project/name
                name='exp',  # save results to project/name
                exist_ok=False,  # existing project/name ok, do not increment
                line_thickness=3,  # bounding box thickness (pixels)
                hide_labels=False,  # hide labels
                hide_conf=False,  # hide confidences
                half=False,  # use FP16 half-precision inference
                dnn=False,  # use OpenCV DNN for ONNX inference
                vid_stride=1,  # video frame-rate stride
        ):
        self.weights = weights
        self.source = source
        self.data = data
        self.imgsz = imgsz
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.max_det = max_det
        self.device = device
        self.view_img = view_img
        self.save_txt = save_txt
        self.save_conf = save_conf
        self.save_crop = save_crop
        self.nosave = nosave
        self.classes = classes
        self.agnostic_nms = agnostic_nms
        self.augment = augment
        self.visualize = visualize
        self.update = update
        self.project = project
        self.name = name
        self.exist_ok = exist_ok
        self.line_thickness = line_thickness
        self.hide_labels = hide_labels
        self.hide_conf = hide_conf
        self.half = half
        self.dnn = dnn
        self.vid_stride = vid_stride

    @smart_inference_mode()
    def load_model(self):
        # Load model
        device = select_device(self.device)
        model = DetectMultiBackend(self.weights, device=device, dnn=self.dnn, data=self.data, fp16=self.half)
        stride, names, pt = model.stride, model.names, model.pt
        imgsz = check_img_size(self.imgsz, s=stride)  # check image size

        # 不需要bs
        model.warmup(imgsz=(1 if pt or model.triton else 1, 3, *imgsz))  # warmup
        
        self.model = model
        self.names = names
        self.imgsz = imgsz
        self.stride = stride
        self.pt = pt
        

    def infer(self, im):
        # Inference
        # yolov5模型对每帧的推理， 但是是原始向量模式，要经过non_max_suppression才可理解
        # with dt[1]:
        pred = self.model(im, augment=self.augment, visualize=self.visualize)
        # NMS
        # 这里之后可以尝试插入人脸识别, 这里才是真正的推断
        # with dt[2]:
        # NMS的作用是通过抑制置信度较低或与其他框重叠较多的候选框，从而选择出最佳的检测结果。
        # 它的基本原理是按照置信度排序候选框，然后逐个考虑每个候选框，将与其重叠度（IOU）超过一定阈值的其他候选框去除，只保留置信度最高的候选框。
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, self.classes, self.agnostic_nms, max_det=self.max_det)
            
        # 原始的pred就这样了， 现在对pred进行转换， [xywh, conf, objs]
        # 换一种方式， 单独提出objs列表
        objs = []
        for predi in pred:
            objs.append([])
            for row in predi:
                objs[-1].append('' if self.hide_labels else self.names[int(row[-1])]) 
        
        return pred, objs
    
def main():
    
    mixDetector = fire_detector()
    # mixDetector.show_datastream('face.mp4')

if __name__ == '__main__':
    main()
