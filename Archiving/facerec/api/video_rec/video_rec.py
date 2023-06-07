import face_recognition
import cv2
import numpy as np
import os
import yaml


CURRENT_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(os.path.dirname(CURRENT_PATH))
yaml_PATH = os.path.join(DIR_PATH, 'data', 'faces.yaml')
img_PATH = os.path.join(DIR_PATH, 'data', 'images')

class video_Recognizer:
    def __init__(self) -> None:
        self.known_face_encodings = {}
        with open(yaml_PATH, 'r') as f:
            data = yaml.safe_load(f)
        for face in data:
            name = face['name']
            image_paths = face['image_paths']
            
            for image_file in image_paths:
                img= face_recognition.load_image_file(os.path.join(img_PATH, image_file))
                # 返回一系列人脸嵌入列表, 保证一张脸, 所以直接取0
                self.known_face_encodings[name] = face_recognition.face_encodings(img)[0]
                
                # TODO
                # 多张图片
                break
            
            
    def recognize(self, video_path):
        
        # Open the input movie file
        input_movie = cv2.VideoCapture(video_path)
        length = int(input_movie.get(cv2.CAP_PROP_FRAME_COUNT))

        # Create an output movie file (make sure resolution/frame rate matches input video!)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        output_movie = cv2.VideoWriter('output.avi', fourcc, 29.97, (640, 360))
        
        # Initialize some variables
        face_locations = []
        face_names = []
        frame_number = 0

        while True:
            # Grab a single frame of video
            ret, frame = input_movie.read()
            frame_number += 1

            # Quit when the input video file ends
            if not ret:
                break

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            # 有问题,见https://stackoverflow.com/questions/75926662/face-recognition-problem-with-face-encodings-function/75943024#75943024
            # rgb_frame = frame[:, :, ::-1]
            rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])

            

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_frame)
            unknown_face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            face_names = []
            for unknown_face_encoding in unknown_face_encodings:
                results = face_recognition.compare_faces(list(self.known_face_encodings.values()), unknown_face_encoding, tolerance=0.50)
                name = 'Unknown'
                for i, match in enumerate(results):
                    if match:
                        name = list(self.known_face_encodings.keys())[i]

                face_names.append(name)

            # Label the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

            # Write the resulting image to the output video file
            print("Writing frame {} / {}".format(frame_number, length))
            output_movie.write(frame)

        # All done!
        input_movie.release()
        cv2.destroyAllWindows()


def test():
    videoRcer = video_Recognizer()
    videoRcer.recognize(os.path.join(DIR_PATH, 'detail', 'short_hamilton_clip.mp4'))
    
if __name__ == '__main__':
    test()