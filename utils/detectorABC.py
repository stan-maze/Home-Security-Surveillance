from abc import ABC, abstractmethod

class Detector(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def init_model(self):
        pass

    @abstractmethod
    def infer(self, image):
        pass