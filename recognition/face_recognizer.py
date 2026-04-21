import face_recognition
import cv2
import numpy as np
import os
import io
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class FaceRecognizer:
    def __init__(self, carpeta="rostros_conocidos", db_storage=None):
        self.carpeta = carpeta
        self.db_storage = db_storage
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

    def cargar_todos(self):
        """Carga encodings primero desde archivos locales, fallback a BD."""
        # Intentar cargar desde archivos primero (más confiable)
        encodings, nombres = self._cargar_desde_archivos()
        
        # Si no hay archivos, intenta desde BD
        if not encodings and self.db_storage:
            encodings, nombres = self._cargar_desde_db()
        
        return encodings, nombres
    
    def _cargar_desde_db(self):
        """Carga encodings desde la base de datos MySQL."""
        encodings = []
        nombres = []
        
        try:
            # Cargar todos los usuarios y sus imágenes
            usuarios = self.db_storage.listar_usuarios_detallados()
            for usuario in usuarios:
                usuario_id = usuario['id']
                nombre_usuario = usuario['nombre_usuario']
                
                # Obtener la imagen del usuario
                try:
                    self.db_storage.cursor.execute(
                        "SELECT imagen FROM imagenes WHERE usuario_id = %s LIMIT 1",
                        (usuario_id,)
                    )
                    row = self.db_storage.cursor.fetchone()
                    if row and row[0]:
                        imagen_bytes = row[0]
                        imagen_array = np.frombuffer(imagen_bytes, dtype=np.uint8)
                        imagen = cv2.imdecode(imagen_array, cv2.IMREAD_COLOR)
                        if imagen is not None:
                            rgb_imagen = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
                            encoding_list = face_recognition.face_encodings(rgb_imagen)
                            if encoding_list:
                                encodings.append(encoding_list[0])
                                nombres.append(nombre_usuario)
                except Exception as e:
                    pass
        except Exception as e:
            pass
        
        return encodings, nombres
    
    def _cargar_desde_archivos(self):
        """Carga encodings desde archivos locales (fallback)."""
        encodings = []
        nombres = []
        for archivo in os.listdir(self.carpeta):
            if archivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                ruta = os.path.join(self.carpeta, archivo)
                try:
                    imagen = face_recognition.load_image_file(ruta)
                    encoding = face_recognition.face_encodings(imagen)
                    if encoding:
                        encodings.append(encoding[0])
                        # Extraer nombre sin extensión
                        nombre = os.path.splitext(archivo)[0]
                        nombres.append(nombre)
                except Exception:
                    pass
        return encodings, nombres

    def comparar(self, encoding_desconocido, encodings_conocidos, nombres, umbral=0.6):
        if not encodings_conocidos:
            print("[comparar] Sin encodings conocidos")
            return None
        distancias = face_recognition.face_distance(encodings_conocidos, encoding_desconocido)
        min_dist = min(distancias)
        print(f"[comparar] Distancias: {[f'{d:.3f}' for d in distancias]}, mín: {min_dist:.3f}, umbral: {umbral}")
        if min_dist < umbral:
            idx = list(distancias).index(min_dist)
            match = nombres[idx]
            print(f"[comparar] MATCH encontrado: {match} (distancia: {min_dist:.3f})")
            return match
        print(f"[comparar] Sin match - distancia mínima {min_dist:.3f} >= umbral {umbral}")
        return None