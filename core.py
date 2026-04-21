"""Lógica de negocio: Base de datos, Reconocimiento facial y Cámara"""
import os
import cv2
import threading
import time
from datetime import datetime, timezone, timedelta
import face_recognition
import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG, FACE_CONFIG, CAMERA_CONFIG


# ============================================================================
# BASE DE DATOS
# ============================================================================
class Database:
    """Gestión de base de datos MySQL para usuarios y accesos"""
    
    def __init__(self, **config):
        try:
            self.conn = mysql.connector.connect(**config)
            self.cursor = self.conn.cursor()
        except Error as e:
            raise RuntimeError(f"Error conexión BD: {e}")
    
    def guardar_usuario(self, nombre_usuario, contraseña, rol='usuario'):
        """Crea un nuevo usuario"""
        sql = "INSERT INTO usuarios (nombre_usuario, contraseña, rol) VALUES (%s, %s, %s)"
        try:
            self.cursor.execute(sql, (nombre_usuario, contraseña, rol))
            self.conn.commit()
            return self.cursor.lastrowid
        except Error as e:
            raise RuntimeError(f"Error al guardar usuario: {e}")
    
    def guardar_imagen(self, usuario_id, imagen_bytes):
        """Registra acceso/imagen de usuario"""
        sql = "INSERT INTO imagenes (usuario_id, fecha_hora, imagen) VALUES (%s, %s, %s)"
        fecha_hora = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.cursor.execute(sql, (usuario_id, fecha_hora, imagen_bytes))
            self.conn.commit()
            return self.cursor.lastrowid
        except Error as e:
            raise RuntimeError(f"Error al guardar imagen: {e}")
    
    def listar_usuarios(self):
        """Retorna lista de todos los usuarios"""
        try:
            self.cursor.execute("SELECT nombre_usuario FROM usuarios")
            return [row[0] for row in self.cursor.fetchall()]
        except Error:
            return []
    
    def listar_usuarios_detallados(self):
        """Retorna lista de usuarios con id, nombre y rol"""
        try:
            self.cursor.execute("SELECT id, nombre_usuario, rol FROM usuarios")
            return [{'id': row[0], 'nombre_usuario': row[1], 'rol': row[2]} 
                    for row in self.cursor.fetchall()]
        except Error:
            return []
    
    def autenticar_usuario(self, nombre_usuario, contraseña):
        """Autentica un usuario por nombre y contraseña"""
        sql = "SELECT id, nombre_usuario, rol FROM usuarios WHERE nombre_usuario=%s AND contraseña=%s"
        try:
            self.cursor.execute(sql, (nombre_usuario, contraseña))
            row = self.cursor.fetchone()
            if row:
                return {'id': row[0], 'nombre_usuario': row[1], 'rol': row[2]}
            return None
        except Error:
            return None
    
    def obtener_usuario_por_nombre(self, nombre_usuario):
        """Obtiene datos de un usuario por nombre"""
        sql = "SELECT id, nombre_usuario, rol FROM usuarios WHERE nombre_usuario=%s"
        try:
            self.cursor.execute(sql, (nombre_usuario,))
            row = self.cursor.fetchone()
            if row:
                return {'id': row[0], 'nombre_usuario': row[1], 'rol': row[2]}
            return None
        except Error:
            return None
    
    def eliminar_usuario(self, nombre_usuario):
        """Elimina un usuario y sus imágenes"""
        try:
            self.cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (nombre_usuario,))
            row = self.cursor.fetchone()
            if not row:
                return 0
            
            usuario_id = row[0]
            self.cursor.execute("DELETE FROM imagenes WHERE usuario_id=%s", (usuario_id,))
            self.cursor.execute("DELETE FROM usuarios WHERE nombre_usuario=%s", (nombre_usuario,))
            self.conn.commit()
            return self.cursor.rowcount
        except Error:
            return 0
    
    def contar_usuarios(self):
        """Cuenta total de usuarios"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM usuarios")
            return self.cursor.fetchone()[0]
        except Error:
            return 0
    
    def contar_accesos_hoy(self):
        """Cuenta accesos de hoy"""
        hoy = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        sql = "SELECT COUNT(*) FROM imagenes WHERE DATE(fecha_hora) = %s"
        try:
            self.cursor.execute(sql, (hoy,))
            return self.cursor.fetchone()[0]
        except Error:
            return 0
    
    def listar_lockers(self, total=4):
        """Devuelve estado de lockers (ocupado/libre) - Solo usuarios normales tienen lockers"""
        try:
            # Solo usuarios con rol 'usuario' pueden tener lockers asignados
            usuarios_normales = [u for u in self.listar_usuarios_detallados() if u['rol'] == 'usuario']
            
            lockers = []
            for i in range(1, total + 1):
                if i <= len(usuarios_normales):
                    usr = usuarios_normales[i - 1]['nombre_usuario']
                    estado = 'Ocupado'
                else:
                    usr = None
                    estado = 'Libre'
                lockers.append({'locker': i, 'usuario': usr, 'estado': estado})
            return lockers
        except Error:
            return []
    
    def liberar_locker(self, locker_num, total=4):
        """Libera un locker eliminando el usuario"""
        if locker_num < 1 or locker_num > total:
            raise ValueError(f"Locker inválido: {locker_num}")
        
        try:
            # Obtener solo usuarios normales (no admins)
            usuarios_normales = [u for u in self.listar_usuarios_detallados() 
                               if u['rol'] == 'usuario']
            
            if locker_num > len(usuarios_normales):
                return False
            
            usuario_nombre = usuarios_normales[locker_num - 1]['nombre_usuario']
            return self.eliminar_usuario(usuario_nombre) > 0
        except Error:
            return False
    
    def cerrar(self):
        """Cierra la conexión a la BD"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# ============================================================================
# RECONOCIMIENTO FACIAL
# ============================================================================
class FaceRecognizer:
    """Reconocimiento y comparación de rostros"""
    
    def __init__(self, carpeta=None, umbral=0.6):
        self.carpeta = carpeta or FACE_CONFIG['carpeta_rostros']
        self.umbral = umbral
        
        if not os.path.exists(self.carpeta):
            os.makedirs(self.carpeta)
    
    def cargar_todos(self):
        """Carga todos los rostros conocidos de la carpeta"""
        encodings = []
        nombres = []
        
        try:
            for archivo in os.listdir(self.carpeta):
                if archivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                    ruta = os.path.join(self.carpeta, archivo)
                    imagen = face_recognition.load_image_file(ruta)
                    encoding = face_recognition.face_encodings(imagen)
                    if encoding:
                        encodings.append(encoding[0])
                        nombres.append(archivo)
        except Exception as e:
            print(f"Error cargando rostros: {e}")
        
        return encodings, nombres
    
    def asociar_rostro(self, nombre_usuario, imagen_bgr):
        """Extrae y guarda el encoding del rostro de una imagen"""
        try:
            # Convertir BGR a RGB
            imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(imagen_rgb)
            
            if not encodings:
                return None
            
            # Guardar imagen de rostro
            ruta = os.path.join(self.carpeta, f"{nombre_usuario}.jpg")
            cv2.imwrite(ruta, imagen_bgr)
            
            return encodings[0]
        except Exception as e:
            print(f"Error asociando rostro: {e}")
            return None
    
    def reconocer(self, imagen_bgr, encodings_conocidos, nombres_conocidos):
        """Identifica un rostro en una imagen - OPTIMIZADO"""
        try:
            imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
            
            # OPTIMIZACIÓN: Redimensionar para procesamiento más rápido
            imagen_pequena = cv2.resize(imagen_rgb, (0, 0), fx=0.25, fy=0.25)
            encodings = face_recognition.face_encodings(imagen_pequena)
            
            if not encodings:
                return None
            
            encoding = encodings[0]
            distancias = face_recognition.face_distance(encodings_conocidos, encoding)
            
            if len(distancias) == 0:
                return None
            
            min_dist = min(distancias)
            if min_dist < self.umbral:
                idx = list(distancias).index(min_dist)
                return nombres_conocidos[idx]
            
            return None
        except Exception as e:
            print(f"Error reconociendo rostro: {e}")
            return None
    
    def detectar_rostros(self, imagen_bgr):
        """Detecta rostros en una imagen (retorna coordenadas) - OPTIMIZADO"""
        try:
            imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
            
            # OPTIMIZACIÓN: Redimensionar para ir más rápido
            imagen_pequena = cv2.resize(imagen_rgb, (0, 0), fx=0.5, fy=0.5)
            faces = face_recognition.face_locations(imagen_pequena, model='hog')  # HOG es más rápido que CNN
            
            # Escalar coordenadas de vuelta al tamaño original
            faces_escaladas = [(int(top*2), int(right*2), int(bottom*2), int(left*2)) for (top, right, bottom, left) in faces]
            
            return faces_escaladas
        except Exception:
            return []


# ============================================================================
# CÁMARA
# ============================================================================
class Camera:
    """Manejo de cámara con streaming en thread"""
    
    def __init__(self, indice=0):
        self.indice = indice
        self.camara = None
        self.activo = False
        self.hilo = None
        self.ultimo_frame = None
        self.lock = threading.Lock()
        
        self._inicializar_camara()
    
    def _inicializar_camara(self):
        """Inicializa la conexión con la cámara"""
        try:
            if os.name == "nt":  # Windows
                self.camara = cv2.VideoCapture(self.indice, cv2.CAP_DSHOW)
            else:
                self.camara = cv2.VideoCapture(self.indice)
            
            if not self.camara.isOpened():
                raise RuntimeError(f"No se pudo abrir cámara {self.indice}")
            
            # Configurar resolución
            self.camara.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_CONFIG['resolucion'][0])
            self.camara.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_CONFIG['resolucion'][1])
            
            print(f"[Cámara] Inicializada correctamente (índice={self.indice})")
        except Exception as e:
            raise RuntimeError(f"Error inicializando cámara: {e}")
    
    def iniciar(self):
        """Inicia el stream de cámara en un thread"""
        self.activo = True
        self.hilo = threading.Thread(target=self._captura_loop, daemon=True)
        self.hilo.start()
        
        # Calentamiento
        for _ in range(5):
            ret, _ = self.camara.read()
            if ret:
                time.sleep(1 / CAMERA_CONFIG['fps'])
    
    def _captura_loop(self):
        """Loop de captura de frames"""
        while self.activo:
            ret, frame = self.camara.read()
            if ret:
                with self.lock:
                    self.ultimo_frame = frame.copy()
            time.sleep(1 / CAMERA_CONFIG['fps'])
    
    def leer_frame(self):
        """Lee el último frame capturado"""
        with self.lock:
            if self.ultimo_frame is None:
                return False, None
            return True, self.ultimo_frame.copy()
    
    def detener(self):
        """Detiene la cámara"""
        self.activo = False
        if self.hilo and self.hilo.is_alive():
            self.hilo.join(timeout=1)
        if self.camara:
            self.camara.release()
        print("[Cámara] Detenida")
