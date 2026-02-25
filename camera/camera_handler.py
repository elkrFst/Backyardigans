import cv2
import threading
import time

class CameraHandler:
    def __init__(self, fuente=0, resolucion=(640, 480), usar_picamera=False):
        self.fuente = fuente
        self.resolucion = resolucion
        self.usar_picamera = usar_picamera
        self.camara = None
        self.activo = False
        self.hilo = None
        self.ultimo_frame = None
        self.lock = threading.Lock()

        if usar_picamera:
            from .picamera_helper import PicameraHelper
            self.camara = PicameraHelper(resolucion)
        else:
            self.camara = cv2.VideoCapture(fuente)
            self.camara.set(cv2.CAP_PROP_FRAME_WIDTH, resolucion[0])
            self.camara.set(cv2.CAP_PROP_FRAME_HEIGHT, resolucion[1])

    def iniciar(self):
        self.activo = True
        if self.usar_picamera:
            self.camara.start()
        self.hilo = threading.Thread(target=self._capturar_loop, daemon=True)
        self.hilo.start()

    def _capturar_loop(self):
        while self.activo:
            if self.usar_picamera:
                ret, frame = self.camara.read()
            else:
                ret, frame = self.camara.read()
            if ret:
                with self.lock:
                    self.ultimo_frame = frame
            time.sleep(0.03)  # ~30 fps

    def leer_frame(self):
        with self.lock:
            if self.ultimo_frame is None:
                return False, None
            return True, self.ultimo_frame.copy()

    def stop(self):
        self.activo = False
        if self.hilo and self.hilo.is_alive():
            self.hilo.join(timeout=1)
        if self.usar_picamera:
            self.camara.stop()
        else:
            self.camara.release()