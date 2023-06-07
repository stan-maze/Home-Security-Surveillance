# from firedet.api.fire_det.face_fire_mix import mix_Detector
from firedet.api.fire_det.face_fire_mix_flask_copy import mix_Detector, external_datastream
from firedet.api.fire_det.utils.camera import LoadStreams, LoadImages

from firedet.api.fire_det.utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadScreenshots
from firedet.api.fire_det.utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from firedet.api.fire_det.utils.plots import Annotator, colors, save_one_box

from firedet.api.fire_detector.fire_detector import fire_detector
