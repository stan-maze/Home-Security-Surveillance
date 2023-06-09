import face_recognition
import numpy as np
import os
import torch
import json

CURRENT_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(os.path.dirname(CURRENT_PATH))
json_PATH = os.path.join(DIR_PATH, 'data', 'faces.json')
# yaml_PATH = os.path.join(DIR_PATH, 'data', 'faces.yaml')
img_PATH = os.path.join(DIR_PATH, 'data', 'images')



class face_recognizer():
    def __init__(self) -> None:
        self.known_face_encodings = {}
        self.init_model()
        

    def init_model(self):
        with open(json_PATH) as file:
            data = json.load(file)
        # with open(yaml_PATH, 'r') as f:
        #     data = yaml.safe_load(f)
        for name, image_paths in data.items():
            # name = face['name']
            # image_paths = face['image_paths']
            
            for image_file in image_paths:
                img= face_recognition.load_image_file(os.path.join(img_PATH, image_file))
                # 返回一系列人脸嵌入列表, 保证一张脸, 所以直接取0
                self.known_face_encodings[name] = face_recognition.face_encodings(img)[0]
                
                # TODO
                # 多张图片
                break
            
    def infer(self, im):

        rgb_frame = np.ascontiguousarray(np.squeeze(im).transpose(1, 2, 0))
        face_locations = face_recognition.face_locations(rgb_frame)
        unknown_face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        pred = []
        faces = []
        # with dt[1]:
        for (top, right, bottom, left), unknown_face_encoding in zip(face_locations, unknown_face_encodings):
            face_distances = face_recognition.face_distance(list(self.known_face_encodings.values()), unknown_face_encoding)
            closest_face_index = np.argmin(face_distances)
            name = "Unknown"
            if face_distances[closest_face_index] < 0.6:
                name = list(self.known_face_encodings.keys())[closest_face_index]
                # dinstance, 也是confidence
                confidence = 1- face_distances[closest_face_index]
            else:
                confidence = face_distances[closest_face_index]
            pred.append([left, top, right, bottom, confidence, 0])
            faces.append(name)
            
        return [torch.tensor(pred, dtype=torch.float32)], [faces]
