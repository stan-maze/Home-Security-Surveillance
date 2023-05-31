from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadScreenshots
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode
from utils.camera import LoadImages, LoadStreams
# from utils.dataloaders import LoadStreams
from utils.alert import send_email

from pathlib import Path
import json
import torch
import platform
from collections import Counter
import os
import datetime
import logging
import logging.handlers
import tarfile
import glob
import shutil
from collections import deque


from facerec import face_recognizer
from firedet import fire_detector

from detector import detect_tasks_manager

    
def test():
    manager = detect_tasks_manager()
    manager.run_detect()

if __name__ == '__main__':
    test()