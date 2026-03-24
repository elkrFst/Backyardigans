import os
import sys
import time

# permitir ejecución directa desde el subdirectorio gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog
import cv2
from PIL import Image, ImageTk
from gui.styles import colores, fuentes
from camera.camera_handler import CameraHandler
from recognition.face_recognizer import FaceRecognizer
<<<<<<< HEAD
from database.mysql_face_storage import MySQLFaceStorage
=======
from database.face_storage import FaceStorage
from gui.admin_window import AdminWindow
>>>>>>> 648f57ea0f264a389bbeecd1299088102f436832
import threading
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Lockers - Profesional")

        # pantalla completa en Raspberry
        # Ventana clásica no full-screen para desarrollo, pero permite maximizar.
        self.root.geometry("1024x640")
        self.root.state('zoomed')
        self.root.bind('<Escape>', lambda e: self.root.state('normal'))

        self.root.configure(bg=colores["fondo"])
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

        # fondo sencillo (el color ya lo tiene). Mantener widget superior persistente.
        self.crear_fondo()

        # estilos ttk para apariencia moderna
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        self.style.configure('TFrame', background=colores['fondo'])
        self.style.configure('TLabel', background=colores['fondo'], foreground=colores['texto'], font=fuentes['normal'])
        self.style.configure('Header.TLabel', background=colores['panel'], foreground=colores['texto'], font=fuentes['titulo'])
        self.style.configure('Card.TFrame', background=colores['panel_sec'], borderwidth=1, relief='flat')
        self.style.configure('Info.TLabel', background=colores['info_bg'], foreground=colores['texto'], font=fuentes['subtitulo'])

        self.style.configure('Primary.TButton', font=fuentes['boton'], padding=12,
                             background=colores['boton_principal'], foreground=colores['texto'])
        self.style.map('Primary.TButton',
                       background=[('active', colores['boton_principal_hover']), ('disabled', '#94a3b8')],
                       foreground=[('active', colores['texto'])])

        self.style.configure('Secondary.TButton', font=fuentes['boton'], padding=12,
                             background=colores['boton_secundario'], foreground=colores['texto'])
        self.style.map('Secondary.TButton',
                       background=[('active', colores['boton_secundario_hover']), ('disabled', '#94a3b8')],
                       foreground=[('active', colores['texto'])])

        self.style.configure('Small.TButton', font=fuentes['boton_pequeno'], padding=8,
                             background=colores['boton_secundario'], foreground=colores['texto'])

        # botón salir persistente en un badge
        btn_salir = ttk.Button(self.root, text="Salir", command=self.cerrar, style='Secondary.TButton')
        btn_salir.place(relx=0.0, rely=1.0, anchor='sw', x=14, y=-12)
        btn_salir.persistent = True

        # ya no usamos el mini‑juego; interfaz más limpia

        self.camera_handler = None
        self.usar_picamera = os.environ.get("USAR_PICAMERA", "").lower() in ("1", "true", "yes")

        self.face_recognizer = FaceRecognizer()
        self.face_storage = FaceStorage("rostros_conocidos")
        from database.mysql_face_storage import MySQLFaceStorage
        self.db_storage = MySQLFaceStorage(host='localhost', user='root', password='', database='locker_scan')

        # garantizar admin inicial
        admin = self.db_storage.obtener_usuario_por_nombre('admin')
        if not admin:
            self.db_storage.guardar_usuario('admin', 'admin123', 'administrador')

        self.reconociendo = False
        self.modo = None                # 'abrir' o 'registrar' o None
        self.capturar = False           # usado en registro
        self.locker_abierto = None

        # Admin integrado
        self.admin_camera_handler = None
        self.admin_frame = None
        self.admin_current_frame = None
        self.admin_captured_image = None

        self.mostrar_menu_principal()

    def cerrar(self):
        if self.camera_handler:
            self.camera_handler.stop()
        if self.admin_camera_handler:
            self.admin_camera_handler.stop()
        self.root.destroy()

    def crear_fondo(self):
        """Establece un fondo sencillo usando el color de tema.

        No se necesitan imágenes complejas: un label del color de fondo
        cubre toda la ventana y garantiza que los widgets previos no sean
        visibles cuando se cambia de pantalla.
        """
        label = tk.Label(self.root, bg=colores['fondo'])
        label.place(x=0, y=0, relwidth=1, relheight=1)
        label.persistent = True

    def limpiar_frame(self):
        for widget in self.root.winfo_children():
            # algunos widgets persistentes (como el botón salir) se mantienen
            if getattr(widget, 'persistent', False):
                continue
            widget.destroy()

    def mostrar_menu_principal(self):
        """Diseño de pantalla principal inspirado en la captura de 800×480.

        - Encabezado con fecha y hora de México
        - Área central con marco gris para la foto/video
        - Panel derecho con dos recuadros de información
        - Barra inferior con dos botones grandes lado a lado
        """
        self.limpiar_frame()

        # configurar grid de la ventana principal
        # filas: 0 = encabezado, 1 = contenido, 2 = botones
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)

        # encabezado + título principal
        header_frame = ttk.Frame(self.root, style='Card.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=(10,5))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        lbl_titulo = ttk.Label(header_frame, text="Smart Locker - Control Facial",
                               style='Header.TLabel')
        lbl_titulo.grid(row=0, column=0, sticky='w', padx=12, pady=10)

        self.lbl_fecha = ttk.Label(header_frame, text="", style='Info.TLabel')
        self.lbl_fecha.grid(row=0, column=1, sticky='e', padx=12, pady=10)
        self.actualizar_header()

        # Botón de acceso rápido a administración de usuarios
        btn_admin = ttk.Button(header_frame, text="Admin", command=self.open_admin_login, style='Small.TButton')
        btn_admin.grid(row=0, column=2, padx=8, pady=8, sticky='ne')

        # marco central para video con borde suave
        self.frame_central = ttk.Frame(self.root, style='Card.TFrame')
        self.frame_central.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.label_video = ttk.Label(self.frame_central, background="#101828")
        self.label_video.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Placeholder cuando no hay video
        self.label_placeholder = ttk.Label(self.frame_central, text="Smart Locker\nListo para usar",
                                           style='Header.TLabel', anchor='center', justify='center')
        self.label_placeholder.place(relx=0.5, rely=0.5, anchor='center')

        # panel de información derecha en formato tarjeta compacta
        frame_info = ttk.Frame(self.root, style='Card.TFrame')
        frame_info.grid(row=1, column=1, sticky='nsew', padx=10, pady=10)
        frame_info.grid_rowconfigure(0, weight=0)
        frame_info.grid_rowconfigure(1, weight=0)

        self.lbl_registro = ttk.Label(frame_info, text="Fecha y hora de registro",
                                      style='Info.TLabel', anchor='center', justify='center')
        self.lbl_registro.grid(row=0, column=0, padx=10, pady=(15, 8), sticky='ew')

        self.lbl_acceso = ttk.Label(frame_info, text="Bienvenido, por favor seleccione una acción",
                                   style='Info.TLabel', anchor='center', justify='center')
        self.lbl_acceso.grid(row=1, column=0, padx=10, pady=(0, 8), sticky='ew')

        self.lbl_lockers = ttk.Label(frame_info, text="Lockers disponibles: 4", style='Info.TLabel', anchor='center', justify='center')
        self.lbl_lockers.grid(row=1, column=0, padx=10, pady=(0, 12), sticky='ew')

        self.actualizar_estado_lockers()

        # botones inferiores
        self.btn_left = ttk.Button(self.root, text="🔓 Abrir Locker", command=self.abrir_locker,
                                   style='Primary.TButton')
        self.btn_right = ttk.Button(self.root, text="📝 Registrar Locker", command=self.iniciar_registro,
                                    style='Secondary.TButton')
        self.btn_left.grid(row=2, column=0, sticky='ew', padx=10, pady=10, ipadx=10, ipady=8)
        self.btn_right.grid(row=2, column=1, sticky='ew', padx=10, pady=10, ipadx=10, ipady=8)

    def open_admin_login(self):
        usuario = simpledialog.askstring("Admin", "Usuario administrador:", parent=self.root)
        contraseña = simpledialog.askstring("Admin", "Contraseña:", show='*', parent=self.root)
        if not usuario or not contraseña:
            return
        user = self.db_storage.autenticar_usuario(usuario, contraseña)
        if not user or user.get('rol') != 'administrador':
            messagebox.showerror("Acceso denegado", "Credenciales inválidas o no autorizado")
            return
        self.abrir_admin()

    def abrir_admin(self):
        usuario = simpledialog.askstring("Usuario", "Usuario administrador:", parent=self.root)
        contraseña = simpledialog.askstring("Contraseña", "Contraseña:", show='*', parent=self.root)
        if not usuario or not contraseña:
            messagebox.showerror("Acceso denegado", "Credenciales requeridas")
            return

        try:
<<<<<<< HEAD
            AdminWindow(self.root, self.db_storage, self.actualizar_lista_encodings)
=======
<<<<<<< HEAD
            auth = self.face_storage.autenticar_usuario(usuario, contraseña)
        except Exception as e:
            messagebox.showerror("Error", f"Error al autenticar: {e}")
            return

        if not auth or auth.get('rol') not in ('administrador', 'admin'):
            messagebox.showerror("Acceso denegado", "Credenciales inválidas o no es administrador")
            return

        try:
            self.mostrar_admin_panel()
=======
            AdminWindow(self.root, self.face_storage, self.actualizar_lista_encodings)
>>>>>>> 648f57ea0f264a389bbeecd1299088102f436832
>>>>>>> 61cfc4eae350694155c74db4a7bfecae3be33e75
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir administración: {e}")

    def mostrar_admin_panel(self):
        self.limpiar_frame()
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=2)
        self.root.grid_columnconfigure(1, weight=3)

        lbl_heading = tk.Label(self.root, text="Administración de Usuarios", font=fuentes['titulo'], bg=colores['panel'], fg=colores['texto'])
        lbl_heading.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)

        btn_back = ttk.Button(self.root, text="Volver", command=self.volver_menu, style='Secondary.TButton')
        btn_back.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

        # Lista de usuarios
        self.admin_listbox = tk.Listbox(self.root, font=fuentes['normal'], bg='white')
        self.admin_listbox.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

        bot_frame = ttk.Frame(self.root)
        bot_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=(0,10))
        ttk.Button(bot_frame, text="Refrescar", command=self.admin_refrescar_lista, style='Small.TButton').pack(side='left', padx=2)
        ttk.Button(bot_frame, text="Eliminar", command=self.admin_eliminar_usuario, style='Secondary.TButton').pack(side='left', padx=2)

        # Panel de formulario
        self.admin_frame = ttk.LabelFrame(self.root, text="Agregar usuario")
        self.admin_frame.grid(row=1, column=1, rowspan=2, sticky='nsew', padx=10, pady=10)

        tk.Label(self.admin_frame, text="Nombre:", bg=colores['fondo']).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.admin_entry_nombre = tk.Entry(self.admin_frame, font=fuentes['normal'])
        self.admin_entry_nombre.grid(row=0, column=1, sticky='ew', padx=10, pady=5)

        tk.Label(self.admin_frame, text="Contraseña:", bg=colores['fondo']).grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.admin_entry_contrasena = tk.Entry(self.admin_frame, show='*', font=fuentes['normal'])
        self.admin_entry_contrasena.grid(row=1, column=1, sticky='ew', padx=10, pady=5)

        tk.Label(self.admin_frame, text="Rol:", bg=colores['fondo']).grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.admin_entry_rol = tk.Entry(self.admin_frame, font=fuentes['normal'])
        self.admin_entry_rol.insert(0, 'usuario')
        self.admin_entry_rol.grid(row=2, column=1, sticky='ew', padx=10, pady=5)

        self.admin_frame.grid_columnconfigure(1, weight=1)

        self.admin_video_label = tk.Label(self.admin_frame, text="Cámara inactiva", bg='black', fg='white')
        self.admin_video_label.grid(row=3, column=0, columnspan=2, padx=10, pady=(8, 6), sticky='nsew')

        camera_btn_frame = ttk.Frame(self.admin_frame)
        camera_btn_frame.grid(row=4, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        self.admin_btn_camera_on = ttk.Button(camera_btn_frame, text="Iniciar cámara", command=self.admin_iniciar_camera, style='Primary.TButton')
        self.admin_btn_camera_on.grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        self.admin_btn_camera_off = ttk.Button(camera_btn_frame, text="Detener cámara", command=self.admin_detener_camera, style='Secondary.TButton')
        self.admin_btn_camera_off.grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        camera_btn_frame.grid_columnconfigure(0, weight=1)
        camera_btn_frame.grid_columnconfigure(1, weight=1)

        action_btn_frame = ttk.Frame(self.admin_frame)
        action_btn_frame.grid(row=5, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        self.admin_btn_capture = ttk.Button(action_btn_frame, text="Capturar foto", command=self.admin_capturar_foto, style='Primary.TButton', state='disabled')
        self.admin_btn_capture.grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        self.admin_btn_save = ttk.Button(action_btn_frame, text="Guardar usuario", command=self.admin_guardar_usuario, style='Primary.TButton')
        self.admin_btn_save.grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        action_btn_frame.grid_columnconfigure(0, weight=1)
        action_btn_frame.grid_columnconfigure(1, weight=1)

        self.admin_refrescar_lista()

    def admin_refrescar_lista(self):
        try:
            usuarios = self.face_storage.listar_usuarios_detallados()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo listar usuarios: {e}")
            usuarios = []
        self.admin_listbox.delete(0, tk.END)
        for u in usuarios:
            self.admin_listbox.insert(tk.END, f"{u['nombre_usuario']}  ({u['rol']})")

    def admin_eliminar_usuario(self):
        sel = self.admin_listbox.curselection()
        if not sel:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para eliminar")
            return
        texto = self.admin_listbox.get(sel[0])
        nombre = texto.split()[0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar usuario {nombre}?"):
            try:
                filas = self.face_storage.eliminar_usuario(nombre)
                if filas:
                    messagebox.showinfo("Eliminado", f"Usuario {nombre} eliminado")
                    local_img = os.path.join('rostros_conocidos', f"{nombre}.jpg")
                    if os.path.exists(local_img):
                        os.remove(local_img)
                else:
                    messagebox.showwarning("No encontrado", "Usuario no encontrado o ya eliminado")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")
            self.admin_refrescar_lista()

    def admin_iniciar_camera(self):
        if self.admin_camera_handler and self.admin_camera_handler.activo:
            return
        index = int(os.environ.get('CAMERA_INDEX', 0)) if os.environ.get('CAMERA_INDEX', '0').isdigit() else 0
        usar_picamera = os.environ.get('USAR_PICAMERA', '').lower() in ('1', 'true', 'yes')
        try:
            self.admin_camera_handler = CameraHandler(fuente=index, resolucion=(640, 480), usar_picamera=usar_picamera)
            self.admin_camera_handler.iniciar()
            self.admin_btn_capture.config(state='normal')
            threading.Thread(target=self.admin_actualizar_video, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error cámara", f"No se pudo iniciar la cámara: {e}")

    def admin_actualizar_video(self):
        while self.admin_camera_handler and self.admin_camera_handler.activo:
            valid, frame = self.admin_camera_handler.leer_frame()
            if valid and frame is not None:
                self.admin_current_frame = frame.copy()
                self.admin_mostrar_frame(frame)
            time.sleep(0.03)

    def admin_mostrar_frame(self, frame):
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb).resize((280, 180), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.admin_video_label.imgtk = imgtk
            self.admin_video_label.configure(image=imgtk, text='')
        except Exception:
            pass

    def admin_capturar_foto(self):
        if self.admin_current_frame is None:
            messagebox.showwarning("Advertencia", "No hay frame disponible para capturar")
            return
        self.admin_captured_image = self.admin_current_frame.copy()
        messagebox.showinfo("Capturado", "Foto tomada exitosamente. Ahora guarde el usuario.")

    def admin_guardar_usuario(self):
        nombre = self.admin_entry_nombre.get().strip()
        contraseña = self.admin_entry_contrasena.get().strip()
        rol = self.admin_entry_rol.get().strip() or 'usuario'
        if not nombre or not contraseña:
            messagebox.showwarning("Faltan datos", "Complete nombre y contraseña")
            return
        if self.admin_captured_image is None:
            messagebox.showwarning("Faltan datos", "Capture la foto del usuario antes de guardar")
            return
        try:
            uid = self.face_storage.guardar_usuario(nombre, contraseña, rol)
            ret, buffer = cv2.imencode('.jpg', self.admin_captured_image)
            if not ret:
                raise RuntimeError('No se pudo codificar imagen')
            imagen_bytes = buffer.tobytes()
            self.face_storage.guardar_imagen(uid, imagen_bytes)
            os.makedirs('rostros_conocidos', exist_ok=True)
            cv2.imwrite(os.path.join('rostros_conocidos', f"{nombre}.jpg"), self.admin_captured_image)
            messagebox.showinfo("Éxito", f"Usuario {nombre} guardado con ID {uid} y foto asignada")
            self.admin_refrescar_lista()
            self.admin_entry_nombre.delete(0, tk.END)
            self.admin_entry_contrasena.delete(0, tk.END)
            self.admin_entry_rol.delete(0, tk.END)
            self.admin_entry_rol.insert(0, 'usuario')
            self.admin_captured_image = None
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar usuario: {e}")

    def admin_detener_camera(self):
        if self.admin_camera_handler:
            self.admin_camera_handler.stop()
            self.admin_camera_handler = None
            self.admin_btn_capture.config(state='disabled')
            self.admin_video_label.configure(image='', text='Cámara detenida', bg='black')

    def actualizar_lista_encodings(self):
        self.face_recognizer.recargar()
        if hasattr(self, 'lbl_acceso') and self.lbl_acceso.winfo_exists():
            self.lbl_acceso.config(text=f"Rostros disponibles: {len(self.face_recognizer.nombres_conocidos)}")
        self.actualizar_estado_lockers()

    def actualizar_estado_lockers(self):
        if hasattr(self, 'lbl_lockers') and self.lbl_lockers.winfo_exists():
            lockers = self.db_storage.listar_lockers()
            ocupados = sum(1 for l in lockers if l['estado'] == 'ocupado')
            self.lbl_lockers.config(text=f"Lockers ocupados: {ocupados} / 4")

    def actualizar_header(self):
        """Actualiza la etiqueta de fecha/hora cada segundo.

        Se usa la hora local del sistema. Si la Pi está configurada a la zona
        de México obtendrá la hora correcta.
        """
        ahora = time.strftime("%d/%m/%Y %H:%M:%S")
        self.lbl_fecha.config(text=ahora)
        self.root.after(1000, self.actualizar_header)

    def preparar_camera(self):
        """Intenta iniciar la cámara probando varios índices automáticamente."""
        posibles_indices = [0, 1, 2]
        error_msg = ""
        for cam_index in posibles_indices:
            try:
                self.camera_handler = CameraHandler(fuente=cam_index,
                                                    resolucion=(640, 480),
                                                    usar_picamera=self.usar_picamera)
                self.camera_handler.iniciar()
                # esperar un frame válido
                for _ in range(15):
                    valid, _ = self.camera_handler.leer_frame()
                    if valid:
                        break
                    time.sleep(0.03)
                else:
                    raise RuntimeError(f"La cámara {cam_index} no devolvió imágenes tras iniciar.")
                print(f"[App] Cámara abierta con índice {cam_index}")
                self.label_placeholder.place_forget()  # Ocultar placeholder cuando hay video
                break
            except RuntimeError as e:
                error_msg += f"\nÍndice {cam_index}: {str(e)}"
                self.camera_handler = None
        else:
            messagebox.showerror("Error de cámara", f"No se pudo abrir ninguna cámara.\n{error_msg}")
            self.volver_menu()
            return False
        # in this version, la lógica de modo se gestiona en los métodos de acción, no aquí
        return True

    def abrir_locker(self):
        self.face_recognizer.recargar()
        if not self.face_recognizer.tiene_registros():
            messagebox.showwarning("Sin registros", "Aún no hay rostros guardados. Por favor registre un locker.")
            return

        self.modo = 'abrir'
        self.lbl_acceso.config(text="Modo: Abrir locker (7 segundos de reconocimiento)")
        self.lbl_registro.config(text="Progreso: iniciando cámara...")
        self.btn_left.state(['disabled'])
        self.btn_right.state(['disabled'])

        if not self.preparar_camera():
            self.btn_left.state(['!disabled'])
            self.btn_right.state(['!disabled'])
            return

        self.locker_abierto = None
        threading.Thread(target=self.procesar_abrir_temporizado, daemon=True).start()

    def procesar_abrir(self):
        """Compatibilidad antigua: antes se llamaba procesar_abrir desde preparar_camera."""
        self.procesar_abrir_temporizado()

    def procesar_registro(self):
        """Compatibilidad antigua: antes se llamaba procesar_registro desde preparar_camera."""
        self.procesar_registro_temporizado()

    def procesar_abrir_temporizado(self):
        inicio = time.time()
        while self.camera_handler and self.camera_handler.activo and time.time() - inicio < 7:
            ret, frame = self.camera_handler.leer_frame()
            if not ret:
                time.sleep(0.02)
                continue
            self.root.after(0, self.mostrar_frame, frame)
            if not self.reconociendo:
                self.reconociendo = True
                copia = frame.copy()
                threading.Thread(target=self._reconocer_copia, args=(copia,), daemon=True).start()
            time.sleep(0.02)

        if self.camera_handler:
            self.camera_handler.stop()

        if self.locker_abierto:
            self.lbl_acceso.config(text=f"Locker {self.locker_abierto} abierto")
            self.lbl_registro.config(text=f"{time.strftime('%H:%M:%S')} - Acceso aprobado")
        else:
            self.lbl_acceso.config(text="No se detectó usuario válido.")
            self.lbl_registro.config(text=f"{time.strftime('%H:%M:%S')} - Acceso fallido")

        self.btn_left.state(['!disabled'])
        self.btn_right.state(['!disabled'])
        self.actualizar_estado_lockers()

    def _reconocer_copia(self, frame):
        """Detecta un rostro en la copia de un frame y actualiza el resultado en la GUI."""
        import face_recognition

        try:
            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_small)
            encodings = face_recognition.face_encodings(rgb_small, locations)

            if encodings:
                nombre = self.face_recognizer.comparar(encodings[0], umbral=0.55)
                if nombre:
                    possible_name = os.path.splitext(nombre)[0]
                    user_record = self.db_storage.obtener_usuario_por_nombre(possible_name)
                    if user_record:
                        locker_num = self.db_storage.obtener_locker_por_usuario_id(user_record['id'])
                        if locker_num:
                            texto = f"Acceso concedido: {possible_name} (Locker {locker_num})"
                            self.locker_abierto = locker_num
                            self.abrir_solenoide(locker_num)
                        else:
                            texto = f"Usuario {possible_name} no tiene locker asignado"
                    else:
                        texto = f"Usuario {possible_name} no registrado en DB"
                    self.lbl_registro.config(text=f"Último acceso: {time.strftime('%H:%M:%S')}")
                else:
                    texto = "Acceso denegado"
                self.root.after(0, self.actualizar_resultado, texto)
            else:
                self.root.after(0, self.actualizar_resultado, "Buscando rostro...")
        except Exception as e:
            print(f"[reconocer_copia] Error: {e}")
        finally:
            self.reconociendo = False

    def actualizar_resultado(self, texto):
        # actualiza el recuadro de acceso de la derecha
        if hasattr(self, "lbl_acceso") and self.lbl_acceso.winfo_exists():
            try:
                self.lbl_acceso.config(text=texto)
            except tk.TclError:
                pass

    def abrir_solenoide(self, locker_num):
        """Simula encendido de solenoide (para Raspberry Pi usar RPi.GPIO)."""
        print(f"[solenoide] Abriendo locker {locker_num}...")
        try:
            import RPi.GPIO as GPIO
            pin = 17 + (locker_num - 1)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(pin, GPIO.LOW)
            GPIO.cleanup(pin)
            print(f"[solenoide] Locker {locker_num} accionado.")
        except Exception as e:
            print(f"[solenoide] No se pudo accionar el solenoide: {e}")

    def iniciar_registro(self):
        disponibles = self.db_storage.listar_lockers()
        ocupados = sum(1 for l in disponibles if l['estado'] == 'ocupado')
        if ocupados >= 4:
            messagebox.showwarning("Sin lockers", "No hay lockers disponibles")
            return

        locker_num = self.db_storage.locker_disponible()
        if locker_num is None:
            messagebox.showwarning("Sin lockers", "No hay lockers disponibles")
            return

        self.nombre_registro = f"locker{locker_num}"
        if self.db_storage.obtener_usuario_por_nombre(self.nombre_registro):
            # si ya existe, buscar siguiente disponible por seguridad
            locker_num = None
            for l in disponibles:
                if l['estado'] == 'libre':
                    locker_num = l['locker']
                    break
            if locker_num is None:
                messagebox.showwarning("Sin lockers", "No hay lockers disponibles")
                return
            self.nombre_registro = f"locker{locker_num}"

        self.locker_num_seleccionado = locker_num

        self.modo = 'registrar'
        self.lbl_acceso.config(text=f"Registrando {self.nombre_registro} por 7 segundos...")
        self.btn_left.state(['disabled'])
        self.btn_right.state(['disabled'])

        if not self.preparar_camera():
            self.btn_left.state(['!disabled'])
            self.btn_right.state(['!disabled'])
            return

        threading.Thread(target=self.procesar_registro_temporizado, daemon=True).start()

    def procesar_registro_temporizado(self):
        inicio = time.time()
        ultimo_frame = None
        while self.camera_handler and self.camera_handler.activo and time.time() - inicio < 7:
            ret, frame = self.camera_handler.leer_frame()
            if not ret:
                time.sleep(0.02)
                continue
            ultimo_frame = frame.copy()
            h, w, _ = frame.shape
            cv2.rectangle(frame, (int(w*0.3), int(h*0.2)), (int(w*0.7), int(h*0.8)), (56, 189, 248), 3)
            cv2.putText(frame, "Alinea tu rostro dentro del recuadro", (20, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (236, 240, 241), 2, cv2.LINE_AA)
            self.root.after(0, self.mostrar_frame, frame)
            time.sleep(0.02)

        if self.camera_handler:
            self.camera_handler.stop()

        if ultimo_frame is not None:
            self.guardar_foto(ultimo_frame)
        else:
            self.lbl_acceso.config(text="No se capturó ninguna imagen")

        self.btn_left.state(['!disabled'])
        self.btn_right.state(['!disabled'])

    def guardar_foto(self, frame):
        import face_recognition
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)

        if locations:
            if self.camera_handler:
                self.camera_handler.stop()

            locker_num = getattr(self, 'locker_num_seleccionado', None)
            if locker_num is None:
                locker_num = self.db_storage.locker_disponible()

            if locker_num is None:
                self.lbl_acceso.config(text="⚠️ No hay lockers libres. Cancelado.")
                self.root.after(2500, self.volver_menu)
                return

            user_id = self.db_storage.guardar_usuario(self.nombre_registro, '1234', 'usuario')

            nombre_archivo = f"{self.nombre_registro}.jpg"
            if os.path.exists(os.path.join(self.face_storage.carpeta, nombre_archivo)):
                now = time.strftime('%Y%m%d_%H%M%S')
                nombre_archivo = f"{self.nombre_registro}_{now}.jpg"

            self.face_storage.guardar(frame, nombre_archivo)
            self.face_recognizer.recargar()

            _, buffer = cv2.imencode('.jpg', frame)
            if buffer is not None:
                self.db_storage.guardar_imagen(user_id, buffer.tobytes())

            self.db_storage.asignar_locker(user_id, locker_num)

            self.lbl_acceso.config(text=f"✅ {self.nombre_registro} registrado y asignado a locker {locker_num}")
            self.lbl_registro.config(text=f"Registrado: {time.strftime('%d/%m/%Y %H:%M:%S')}")
            self.actualizar_estado_lockers()
            self.root.after(2500, self.volver_menu)
        else:
            self.lbl_acceso.config(text="⚠️ No se detecta rostro. Intenta de nuevo.")
            self.btn_left.state(['!disabled'])
            self.btn_right.state(['!disabled'])


    def iniciar_cuenta_regresiva(self):
        self.btn_capturar.config(state="disabled")
        self.cuenta = 3
        self.actualizar_cuenta()

    def actualizar_cuenta(self):
        if self.cuenta > 0:
            self.label_cuenta.config(text=str(self.cuenta))
            self.cuenta -= 1
            self.root.after(1000, self.actualizar_cuenta)
        else:
            self.label_cuenta.config(text="")
            self.capturar = True

    def mostrar_frame(self, frame):
        if not (hasattr(self, "label_video") and self.label_video.winfo_exists()):
            return
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            w = self.label_video.winfo_width() or 800
            h = self.label_video.winfo_height() or 480
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label_video.imgtk = imgtk
            self.label_video.configure(image=imgtk)
        except tk.TclError:
            pass

    def obtener_nombre_automatico(self):
        """Retorna el siguiente nombre de usuario en formato 'usuarioX'."""
        archivos = self.face_storage.listar()
        max_n = 0
        for f in archivos:
            base = os.path.splitext(f)[0]
            if base.startswith("usuario"):
                num = base.replace("usuario", "")
                if num.isdigit():
                    n = int(num)
                    if n > max_n:
                        max_n = n
            elif base.isdigit():
                n = int(base)
                if n > max_n:
                    max_n = n
        return f"usuario{max_n + 1}"

    def volver_menu(self):
        if self.camera_handler:
            self.camera_handler.stop()
<<<<<<< HEAD
        self.label_placeholder.place(relx=0.5, rely=0.5, anchor='center')  # Mostrar placeholder
=======
        if self.admin_camera_handler:
            self.admin_camera_handler.stop()
            self.admin_camera_handler = None
>>>>>>> 61cfc4eae350694155c74db4a7bfecae3be33e75
        self.mostrar_menu_principal()