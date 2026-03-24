import os
import threading
import time

import cv2
from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog
from camera.camera_handler import CameraHandler
from gui.styles import colores, fuentes
from database.mysql_face_storage import MySQLFaceStorage


class UserAdminWindow(tk.Toplevel):
    def __init__(self, parent, db_config=None):
        super().__init__(parent)
        self.title("Administración de Usuarios")
        self.geometry("640x520")
        self.configure(bg=colores["fondo"])

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Conectar almacenamiento (usar configuración por defecto si no se pasa)
        cfg = db_config or {}
        self.storage = MySQLFaceStorage(**cfg)

        # Autenticación mínima (puede saltarse si el entorno ya es seguro)
        # Asume usuario admin/contraseña guardados en la BD para simplificar.
        usuario = tk.simpledialog.askstring("Usuario", "Usuario administrador:", parent=self)
        contraseña = tk.simpledialog.askstring("Contraseña", "Contraseña:", show='*', parent=self)
        if not usuario or not contraseña:
            messagebox.showerror("Acceso denegado", "Credenciales requeridas")
            self.destroy()
            return

        try:
            auth = self.storage.autenticar_usuario(usuario, contraseña)
        except Exception as e:
            messagebox.showerror("Error", f"Error al autenticar: {e}")
            self.destroy()
            return

        if not auth or auth.get('rol') not in ('administrador', 'admin'):
            messagebox.showerror("Acceso denegado", "Credenciales inválidas o no es administrador")
            self.destroy()
            return

        self.camera_handler = None
        self.current_frame = None
        self.captured_image = None

        self._build_ui()
        self.cargar_lista()

    def _build_ui(self):
        self.lista = tk.Listbox(self, font=fuentes['normal'], bg='white')
        self.lista.place(x=10, y=10, width=300, height=300)

        frame = ttk.Frame(self)
        frame.place(x=10, y=320)
        ttk.Button(frame, text="Refrescar", command=self.cargar_lista, style='Small.TButton').pack(side='left', padx=4)
        ttk.Button(frame, text="Mostrar Form Agregar", command=self.agregar, style='Primary.TButton').pack(side='left', padx=4)
        ttk.Button(frame, text="Eliminar", command=self.eliminar, style='Secondary.TButton').pack(side='left', padx=4)
        ttk.Button(frame, text="Cerrar", command=self._on_close, style='Secondary.TButton').pack(side='left', padx=4)

        self.frame_agregar = ttk.LabelFrame(self, text="Agregar/Nuevo usuario")
        self.frame_agregar.place(x=320, y=10, width=300, height=420)

        tk.Label(self.frame_agregar, text="Nombre:", bg=colores['fondo']).place(x=10, y=10)
        self.entry_nombre = tk.Entry(self.frame_agregar, font=fuentes['normal'])
        self.entry_nombre.place(x=90, y=10, width=190)

        tk.Label(self.frame_agregar, text="Contraseña:", bg=colores['fondo']).place(x=10, y=45)
        self.entry_contrasena = tk.Entry(self.frame_agregar, show='*', font=fuentes['normal'])
        self.entry_contrasena.place(x=90, y=45, width=190)

        tk.Label(self.frame_agregar, text="Rol:", bg=colores['fondo']).place(x=10, y=80)
        self.entry_rol = tk.Entry(self.frame_agregar, font=fuentes['normal'])
        self.entry_rol.insert(0, 'usuario')
        self.entry_rol.place(x=90, y=80, width=190)

        self.label_video = tk.Label(self.frame_agregar, text="Cámara inactiva", bg='black', fg='white')
        self.label_video.place(x=10, y=120, width=280, height=200)

        boton_frame = ttk.Frame(self.frame_agregar)
        boton_frame.place(x=10, y=330)
        self.btn_iniciar_camera = ttk.Button(boton_frame, text="Iniciar cámara", command=self.iniciar_camera, style='Primary.TButton')
        self.btn_iniciar_camera.pack(side='left', padx=3)
        self.btn_detener_camera = ttk.Button(boton_frame, text="Detener cámara", command=self.detener_camera, style='Secondary.TButton')
        self.btn_detener_camera.pack(side='left', padx=3)

        self.btn_capturar_foto = ttk.Button(self.frame_agregar, text="Capturar foto", command=self.capturar_foto, style='Primary.TButton', state='disabled')
        self.btn_capturar_foto.place(x=20, y=370, width=130)

        self.btn_guardar = ttk.Button(self.frame_agregar, text="Guardar usuario con foto", command=self.guardar_usuario_con_foto, style='Primary.TButton')
        self.btn_guardar.place(x=150, y=370, width=140)

    def cargar_lista(self):
        try:
            usuarios = self.storage.listar_usuarios_detallados()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo listar usuarios: {e}")
            usuarios = []
        self.lista.delete(0, tk.END)
        for u in usuarios:
            self.lista.insert(tk.END, f"{u['nombre_usuario']}  ({u['rol']})")

    def agregar(self):
        self.frame_agregar.lift()
        self.entry_nombre.focus_set()

    def iniciar_camera(self):
        if self.camera_handler and self.camera_handler.activo:
            return
        try:
            index = int(os.environ.get('CAMERA_INDEX', 0))
        except ValueError:
            index = 0
        usar_picamera = os.environ.get('USAR_PICAMERA', '').lower() in ('1', 'true', 'yes')
        try:
            self.camera_handler = CameraHandler(fuente=index, resolucion=(640, 480), usar_picamera=usar_picamera)
            self.camera_handler.iniciar()
            self.btn_capturar_foto.config(state='normal')
            threading.Thread(target=self._actualizar_video, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error cámara", f"No se pudo iniciar la cámara: {e}")

    def _actualizar_video(self):
        while self.camera_handler and self.camera_handler.activo:
            valid, frame = self.camera_handler.leer_frame()
            if valid and frame is not None:
                self.current_frame = frame.copy()
                self._mostrar_frame(frame)
            time.sleep(0.03)

    def _mostrar_frame(self, frame):
        try:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = img.resize((280, 180), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label_video.imgtk = imgtk
            self.label_video.configure(image=imgtk, text='')
        except Exception:
            pass

    def detener_camera(self):
        if self.camera_handler:
            self.camera_handler.stop()
            self.camera_handler = None
            self.btn_capturar_foto.config(state='disabled')
            self.label_video.configure(image='', text='Cámara detenida', bg='black')

    def capturar_foto(self):
        if self.current_frame is None:
            messagebox.showwarning("Advertencia", "No hay frame disponible para capturar")
            return
        self.captured_image = self.current_frame.copy()
        messagebox.showinfo("Capturado", "Foto tomada exitosamente. Ahora guarde el usuario.")

    def guardar_usuario_con_foto(self):
        nombre = self.entry_nombre.get().strip()
        contraseña = self.entry_contrasena.get().strip()
        rol = self.entry_rol.get().strip() or 'usuario'

        if not nombre or not contraseña:
            messagebox.showwarning("Faltan datos", "Complete nombre y contraseña")
            return

        if self.captured_image is None:
            messagebox.showwarning("Faltan datos", "Capture la foto del usuario antes de guardar")
            return

        try:
            uid = self.storage.guardar_usuario(nombre, contraseña, rol)

            ret, buffer = cv2.imencode('.jpg', self.captured_image)
            if not ret:
                raise RuntimeError('No se pudo codificar imagen')
            imagen_bytes = buffer.tobytes()
            self.storage.guardar_imagen(uid, imagen_bytes)

            # Guardar copia local adicional para reconocimiento con rostros_conocidos
            carpeta_local = 'rostros_conocidos'
            os.makedirs(carpeta_local, exist_ok=True)
            path_local = os.path.join(carpeta_local, f"{nombre}.jpg")
            cv2.imwrite(path_local, self.captured_image)

            messagebox.showinfo("Éxito", f"Usuario {nombre} guardado con ID {uid} y foto asignada")
            self.cargar_lista()
            self.entry_nombre.delete(0, tk.END)
            self.entry_contrasena.delete(0, tk.END)
            self.entry_rol.delete(0, tk.END)
            self.entry_rol.insert(0, 'usuario')
            self.captured_image = None
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar usuario: {e}")

    def eliminar(self):
        sel = self.lista.curselection()
        if not sel:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para eliminar")
            return
        texto = self.lista.get(sel[0])
        nombre = texto.split()[0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar usuario {nombre}?"):
            try:
                filas = self.storage.eliminar_usuario(nombre)
                if filas:
                    messagebox.showinfo("Eliminado", f"Usuario {nombre} eliminado")
                    # También limpiar imagen local si existe
                    path_local = os.path.join('rostros_conocidos', f"{nombre}.jpg")
                    if os.path.exists(path_local):
                        os.remove(path_local)
                else:
                    messagebox.showwarning("No encontrado", "Usuario no encontrado o ya eliminado")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")
            self.cargar_lista()

    def _on_close(self):
        self.detener_camera()
        try:
            self.storage.cerrar()
        except Exception:
            pass
        self.destroy()
