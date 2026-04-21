#!/usr/bin/env python3
"""
Sistema de reconocimiento facial para control de acceso a lockers
Punto de entrada
"""
import sys
import os
import tkinter as tk
from tkinter import messagebox

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG
from core import Database, FaceRecognizer
from ui import UIApp


class DBSimulada:
    """BD simulada para cuando falla la conexión real"""
    def __init__(self):
        self.usuarios = {}
    
    def guardar_usuario(self, nombre, contraseña, rol='usuario'):
        self.usuarios[nombre] = {'contraseña': contraseña, 'rol': rol}
        return 1
    
    def autenticar_usuario(self, nombre, contraseña):
        if nombre in self.usuarios and self.usuarios[nombre]['contraseña'] == contraseña:
            return {'id': 1, 'nombre_usuario': nombre, 'rol': self.usuarios[nombre]['rol']}
        return None
    
    def obtener_usuario_por_nombre(self, nombre):
        if nombre in self.usuarios:
            return {'id': 1, 'nombre_usuario': nombre, 'rol': self.usuarios[nombre]['rol']}
        return None
    
    def guardar_imagen(self, usuario_id, imagen_bytes):
        return 1
    
    def listar_usuarios(self):
        return list(self.usuarios.keys())
    
    def listar_usuarios_detallados(self):
        return [{'id': 1, 'nombre_usuario': k, 'rol': v['rol']} for k, v in self.usuarios.items()]
    
    def eliminar_usuario(self, nombre):
        if nombre in self.usuarios:
            del self.usuarios[nombre]
            return 1
        return 0
    
    def contar_usuarios(self):
        return len(self.usuarios)
    
    def contar_accesos_hoy(self):
        return 0
    
    def listar_lockers(self, total=4):
        usuarios = self.listar_usuarios_detallados()
        lockers = []
        for i in range(1, total + 1):
            if i <= len(usuarios):
                usr = usuarios[i - 1]['nombre_usuario']
                estado = 'Ocupado'
            else:
                usr = None
                estado = 'Libre'
            lockers.append({'locker': i, 'usuario': usr, 'estado': estado})
        return lockers
    
    def liberar_locker(self, locker_num, total=4):
        usuarios = self.listar_usuarios_detallados()
        if locker_num > len(usuarios):
            return False
        usuario_nombre = usuarios[locker_num - 1]['nombre_usuario']
        return self.eliminar_usuario(usuario_nombre) > 0
    
    def cerrar(self):
        pass


def main():
    """Inicia la aplicación"""
    db = None
    
    try:
        # Crear ventana Tkinter primera
        root = tk.Tk()
        
        # Intentar conectar a base de datos
        print("[INFO] Intentando conectar a MySQL...")
        try:
            db = Database(**DB_CONFIG)
            print("[OK] ✅ Conectado a MySQL")
        except Exception as e:
            print(f"[ERROR] ❌ No se pudo conectar a MySQL: {e}")
            print("[INFO] Usando base de datos simulada (DEMO MODE)")
            db = DBSimulada()
        
        # Inicializar reconocedor de rostros
        print("[INFO] Inicializando reconocedor facial...")
        face_recognizer = FaceRecognizer()
        print("[OK] ✅ Reconocedor listo")
        
        # Crear interfaz gráfica
        print("[INFO] Abriendo interfaz gráfica...")
        app = UIApp(root, db, face_recognizer)
        print("[OK] ✅ Aplicación iniciada")
        
        root.mainloop()
    
    except Exception as e:
        print(f"\n[FATAL] Error crítico: {e}")
        import traceback
        traceback.print_exc()
        
        # Mostrar error en ventana
        try:
            root.destroy()
        except:
            pass
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error Fatal", f"No se pudo iniciar la aplicación:\n{e}")
    
    finally:
        # Limpiar
        if db:
            try:
                db.cerrar()
            except:
                pass
        print("[INFO] Aplicación cerrada")


if __name__ == "__main__":
    main()