import os
import shutil
import cv2
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class FaceStorage:
    def __init__(self, carpeta="rostros_conocidos"):
        self.carpeta = carpeta
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

    def listar(self):
        archivos = [f for f in os.listdir(self.carpeta) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        return sorted(archivos)

    def eliminar(self, nombre_archivo):
        ruta = os.path.join(self.carpeta, nombre_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)

    def renombrar(self, nombre_viejo, nombre_nuevo):
        ruta_vieja = os.path.join(self.carpeta, nombre_viejo)
        ruta_nueva = os.path.join(self.carpeta, nombre_nuevo)
        if not os.path.exists(ruta_vieja):
            raise FileNotFoundError("El archivo no existe")
        if os.path.exists(ruta_nueva):
            raise FileExistsError("Ya existe un archivo con ese nombre")
        os.rename(ruta_vieja, ruta_nueva)

    def guardar(self, frame, nombre):
        """Guarda un *frame* de OpenCV en la carpeta de rostros.

        El parámetro *nombre* puede venir con o sin ".jpg"; la función se asegura de
        añadir la extensión. Devuelve la ruta completa donde se guardó la imagen.
        """
        # Asegurar extensión .jpg
        if not nombre.lower().endswith('.jpg'):
            nombre += '.jpg'
        ruta = os.path.join(self.carpeta, nombre)
        cv2.imwrite(ruta, frame)
        return ruta