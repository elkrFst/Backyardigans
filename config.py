"""Configuración centralizada del sistema de reconocimiento facial"""
import os

# Ambiente
DEBUG = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Colores (tema Smart Locker: oscuro, tecnologico y claro)
COLORES = {
    "fondo": "#07111f",
    "fondo_alt": "#0b1d33",
    "panel": "#0f243b",
    "panel_sec": "#132f4b",
    "panel_suave": "#173a5e",
    "info_bg": "#061827",
    "video_bg": "#020817",
    "borde": "#25577d",
    "texto": "#f8fbff",
    "subtexto": "#a8c7df",
    "muted": "#6f93ad",
    "boton_principal": "#00a7e8",
    "boton_principal_hover": "#22d3ee",
    "boton_secundario": "#12b981",
    "boton_secundario_hover": "#2dd4bf",
    "accento": "#37d5ff",
    "exito": "#22c55e",
    "alerta": "#f59e0b",
    "error": "#ef4444",
    "admin": "#ef4444",
    "volver": "#f97316",
    "capturar": "#22c55e",
    "agregar": "#14b8a6",
    "eliminar": "#ef4444",
    "renombrar": "#f59e0b"
}

# Fuentes
FUENTES = {
    "titulo": ("Segoe UI", 18, "bold"),
    "subtitulo": ("Segoe UI", 10),
    "boton": ("Segoe UI", 11, "bold"),
    "boton_pequeno": ("Segoe UI", 9, "bold"),
    "resultado": ("Segoe UI", 12, "bold"),
    "normal": ("Segoe UI", 10),
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
