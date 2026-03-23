import cv2
import threading
import time
import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class CameraHandler:
    def __init__(self, fuente=0, resolucion=(640, 480), usar_picamera=False):
        """Manejador sencillo de cámara.

        Args:
            fuente (int): índice de la cámara (0 = cámara integrada del portátil).
            resolucion (tuple): resolución a solicitar (ancho, alto).
            usar_picamera (bool): si True utiliza la Raspberry Pi Camera.
        """
        self.fuente = 0 if fuente is None else fuente
        self.resolucion = resolucion
        self.usar_picamera = usar_picamera
        self.camara = None
        self.activo = False
        self.hilo = None
        self.ultimo_frame = None
        self.lock = threading.Lock()

        if usar_picamera:
            from .picamera_helper import PicameraHelper
            # la PiCamera administrada por su módulo específico
            self.camara = PicameraHelper(resolucion)
        else:
            # en Windows conviene utilizar el backend CAP_DSHOW para abrir la cámara 0
            if os.name == "nt":
                self.camara = cv2.VideoCapture(self.fuente, cv2.CAP_DSHOW)
            else:
                self.camara = cv2.VideoCapture(self.fuente)

            if not self.camara.isOpened():
                raise RuntimeError(f"No se pudo abrir la cámara {self.fuente}. Verifique el índice o los permisos.")

            # ajuste de resolución
            self.camara.set(cv2.CAP_PROP_FRAME_WIDTH, resolucion[0])
            self.camara.set(cv2.CAP_PROP_FRAME_HEIGHT, resolucion[1])
            print(f"[CameraHandler] cámara {self.fuente} abierta correctamente (backend os={os.name})")

    def iniciar(self):
        self.activo = True
        if self.usar_picamera:
            self.camara.start()
        self.hilo = threading.Thread(target=self._capturar_loop, daemon=True)
        self.hilo.start()
        # leer algunos frames de calentamiento para que la primera llamada a
        # leer_frame() no devuelva None inmediatamente.
        for _ in range(5):
            ret, frame = self.camara.read() if not self.usar_picamera else self.camara.read()
            time.sleep(0.03)

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