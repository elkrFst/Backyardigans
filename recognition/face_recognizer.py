import face_recognition
import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
class FaceRecognizer:
    def __init__(self, carpeta="rostros_conocidos"):
        self.carpeta = carpeta
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

    def cargar_todos(self):
        encodings = []
        nombres = []
        for archivo in os.listdir(self.carpeta):
            if archivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                ruta = os.path.join(self.carpeta, archivo)
                imagen = face_recognition.load_image_file(ruta)
                encoding = face_recognition.face_encodings(imagen)
                if encoding:
                    encodings.append(encoding[0])
                    nombres.append(archivo)
        return encodings, nombres

    def comparar(self, encoding_desconocido, encodings_conocidos, nombres, umbral=0.6):
        if not encodings_conocidos:
            return None
        distancias = face_recognition.face_distance(encodings_conocidos, encoding_desconocido)
        min_dist = min(distancias)
        if min_dist < umbral:
            idx = list(distancias).index(min_dist)
            return nombres[idx]
        return None