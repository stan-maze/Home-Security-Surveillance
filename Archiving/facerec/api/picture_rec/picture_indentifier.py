import yaml
from PIL import Image
import os
import face_recognition
import numpy as np


CURRENT_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(os.path.dirname(CURRENT_PATH))
yaml_PATH = os.path.join(DIR_PATH, 'data', 'faces.yaml')
img_PATH = os.path.join(DIR_PATH, 'data', 'images')


class picture_Indentifier:
    def __init__(self) -> None:
        self.known_face_encodings = {}
        with open(yaml_PATH, 'r') as f:
            data = yaml.safe_load(f)
        for face in data:
            name = face['name']
            image_paths = face['image_paths']
            
            face_encodings = []           
            
            for image_file in image_paths:
                img= face_recognition.load_image_file(os.path.join(img_PATH, image_file))
                # 返回一系列人脸嵌入列表, 保证一张脸, 所以直接取0
                face_encodings.append(face_recognition.face_encodings(img)[0])
                
            # TODO
            # 多张图片, 取平均值而已
            
            self.known_face_encodings[name] = np.mean(face_encodings, axis=0)
    
    def indentify(self, image_path):
        unknown_image = face_recognition.load_image_file(image_path)
        unknown_face_encodings = face_recognition.face_encodings(unknown_image)
        for unknown_face_encoding in unknown_face_encodings:
            results = face_recognition.compare_faces(list(self.known_face_encodings.values()), unknown_face_encoding)
            for i, match in enumerate(results):
                if match:
                    print('The person in the unknown image is a match with known face #' + list(self.known_face_encodings.keys())[i])


def test():
    pic_inder = picture_Indentifier()
    pic_inder.indentify(os.path.join(img_PATH, 'biden1.jpg'))
        
        
if __name__ == '__main__':
    test()