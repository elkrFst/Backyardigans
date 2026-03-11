import cv2
import numpy as np
from picamera2 import Picamera2
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class PicameraHelper:
    def __init__(self, resolucion=(640, 480)):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": resolucion})
        self.picam2.configure(config)
        self.resolucion = resolucion

    def start(self):
        self.picam2.start()

    def stop(self):
        self.picam2.stop()

    def read(self):
        frame = self.picam2.capture_array()
        # Convertir XRGB a BGR
        if frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return True, frame