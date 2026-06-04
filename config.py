"""Configuración centralizada del sistema de reconocimiento facial"""
import os

# Ambiente
DEBUG = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Colores (tema oscuro profesional)
COLORES = {
    "fondo": "#071223",
    "panel": "#0f1f33",
    "panel_sec": "#102a44",
    "info_bg": "#11263b",
    "texto": "#e2f1ff",
    "subtexto": "#a8c3eb",
    "boton_principal": "#0d9488",
    "boton_principal_hover": "#065f46",
    "boton_secundario": "#2563eb",
    "boton_secundario_hover": "#1d4ed8",
    "panel_header": "#0f172a",
    "panel_border": "#203a5a",
    "video_bg": "#11233a",
        "video_border": "#1f6f9a",
        "video_halo": "#5fb0ff",
    "badge_bg": "#18325d",
    "info_card": "#0f1f33",
    "outline": "#38bdf8",
    "accento": "#38bdf8",
    "admin": "#ef4444",
    "volver": "#f97316",
    "capturar": "#22c55e",
    "agregar": "#14b8a6",
    "eliminar": "#ef4444",
    "renombrar": "#f59e0b"
}

# Fuentes
FUENTES = {
    "titulo": ("Segoe UI", 20, "bold"),
    "subtitulo": ("Segoe UI", 12),
    "boton": ("Segoe UI", 11, "bold"),
    "boton_pequeno": ("Segoe UI", 9, "bold"),
    "resultado": ("Segoe UI", 13, "bold"),
    "normal": ("Segoe UI", 11),
    "cuenta": ("Segoe UI", 32, "bold")
}

# Base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'locker_scan'
}

# Cámara
CAMERA_CONFIG = {
    'resolucion': (600, 240),
    'fps': 30,
    'usar_picamera': os.environ.get("USAR_PICAMERA", "").lower() in ("1", "true", "yes")
}

# Reconocimiento facial
FACE_CONFIG = {
    'carpeta_rostros': 'rostros',  # Renombrada de rostros_conocidos
    'umbral_similitud': 0.6,
    'modelo': 'hog'  # 'hog' = rápido, 'cnn' = preciso (más lento)
}

# Admin
ADMIN_CONFIG = {
    'contraseña_defecto': 'Admin123',
    'total_lockers': 4
}

# GPIO - Control de relés de lockers (Raspberry Pi)
GPIO_CONFIG = {
    'habilitado': os.environ.get("GPIO_ENABLED", "").lower() in ("1", "true", "yes"),  # Activar/desactivar GPIO
    'pines': {
        1: 17,  # Locker 1
        2: 27,  # Locker 2
        3: 22,  # Locker 3
        4: 23   # Locker 4
    },
    'pulso_duracion': 2.0,  # Duración del pulso en segundos
    'active_high': False    # Los relés se activan con señal baja (active_high=False)
}

# UI
WINDOW_SIZE = "800x480"  # Pantalla 7 pulgadas Raspberry Pi
WINDOW_FULLSCREEN = False  # Activado para Raspberry Pi
