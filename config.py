"""Configuración centralizada del sistema de reconocimiento facial"""
import os

# Ambiente
DEBUG = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Colores (tema limpio y amigable)
COLORES = {
    "fondo": "#f5f7fb",
    "panel": "#ffffff",
    "panel_sec": "#eef2f7",
    "info_bg": "#e5f1ff",
    "texto": "#102a43",
    "subtexto": "#475569",
    "boton_principal": "#2563eb",
    "boton_principal_hover": "#1d4ed8",
    "boton_secundario": "#0ea5e9",
    "boton_secundario_hover": "#0284c7",
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
    "titulo": ("Segoe UI", 14, "bold"),
    "subtitulo": ("Segoe UI", 9),
    "boton": ("Segoe UI", 8, "bold"),
    "boton_pequeno": ("Segoe UI", 8, "bold"),
    "resultado": ("Segoe UI", 11, "bold"),
    "normal": ("Segoe UI", 9),
    "cuenta": ("Segoe UI", 28, "bold")
}

# Base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root1',
    'password': 'micontraseña',
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
    'habilitado': True,  # ✅ GPIO HABILITADO - Cambiar a False para deshabilitar
    'pines': {
        1: 17,  # Locker 1
        2: 27,  # Locker 2
        3: 22,  # Locker 3
        4: 23   # Locker 4
    },
    'pulso_duracion': 2.0,  # Duración del pulso en segundos
    'active_high': True    # ✅ CAMBIAR: Relés se activan con señal ALTA (active_high=True)
}

# UI
WINDOW_SIZE = "800x400"  # Pantalla 7 pulgadas Raspberry Pi
WINDOW_FULLSCREEN = True  # Pantalla completa; salir con Esc
