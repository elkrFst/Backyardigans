"""
Simulación de face_recognition usando OpenCV
Para evitar dependencia de dlib que es difícil de compilar en Windows
"""
import cv2
import numpy as np
import os
from pathlib import Path


class CascadeDetector:
    """Detector de rostros usando OpenCV Cascade Classifier"""
    
    def __init__(self):
        # Usar el cascade classifier integrado de OpenCV
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.cascade = cv2.CascadeClassifier(cascade_path)
        self.trained = False
        self.labels_map = {}
        self.reverse_labels = {}
    
    def load_image_file(self, image_path):
        """Carga una imagen del disco"""
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"No se pudo cargar {image_path}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    def face_encodings(self, image, known_face_locations=None):
        """
        Retorna 'encodings' de rostros (en nuestro caso, histogramas)
        Para ser compatible con face_recognition
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        faces = self.cascade.detectMultiScale(gray, 1.3, 5)
        
        encodings = []
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            # Usar histograma como "encoding"
            hist = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            encodings.append(hist)
        
        return encodings
    
    def face_locations(self, image, model="hog"):
        """Retorna localizaciones de rostros"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        faces = self.cascade.detectMultiScale(gray, 1.3, 5)
        
        # Convertir a formato (top, right, bottom, left)
        locations = []
        for (x, y, w, h) in faces:
            locations.append((y, x + w, y + h, x))
        
        return locations
    
    def compare_faces(self, known_encodings, face_encoding, tolerance=0.6):
        """Compara un encoding con una lista de encodings conocidos"""
        if not known_encodings:
            return []
        
        known_encodings = np.array(known_encodings)
        face_encoding = np.array(face_encoding)
        
        # Usar distancia euclidiana
        distances = np.linalg.norm(known_encodings - face_encoding, axis=1)
        
        # Retornar True/False basado en tolerancia (distancia umbral)
        return list(distances <= tolerance)
    
    def face_distance(self, known_encodings, face_encoding):
        """Retorna distancias entre encodings"""
        if not known_encodings:
            return np.array([])
        
        known_encodings = np.array(known_encodings)
        face_encoding = np.array(face_encoding)
        
        return np.linalg.norm(known_encodings - face_encoding, axis=1)


# Crear instancia global
_detector = None


def get_detector():
    global _detector
    if _detector is None:
        _detector = CascadeDetector()
    return _detector


def load_image_file(file_path):
    """API compatible con face_recognition"""
    return get_detector().load_image_file(file_path)


def face_encodings(image, known_face_locations=None, num_jitters=1):
    """API compatible con face_recognition"""
    return get_detector().face_encodings(image, known_face_locations)


def face_locations(image, number_of_times_to_upsample=1, model="hog"):
    """API compatible con face_recognition"""
    return get_detector().face_locations(image, model)


def compare_faces(known_face_encodings, face_encoding_to_compare, tolerance=0.6):
    """API compatible con face_recognition"""
    return get_detector().compare_faces(known_face_encodings, face_encoding_to_compare, tolerance)


def face_distance(known_face_encodings, face_encoding_to_compare):
    """API compatible con face_recognition"""
    return get_detector().face_distance(known_face_encodings, face_encoding_to_compare)
