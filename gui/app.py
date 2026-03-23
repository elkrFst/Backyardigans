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
from database.mysql_face_storage import MySQLFaceStorage
import threading
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Lockers - Profesional")

        # pantalla completa en Raspberry
        self.root.attributes('-fullscreen', True)
        # para desarrollo se puede salir con Esc
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))

        # también fijamos fondo y bloqueamos redimensionado manual
        self.root.configure(bg=colores["fondo"])
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

        # fondo dinámico antes de cualquier widget
        self.crear_fondo()

        # estilos ttk para una apariencia más moderna
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        self.style.configure('TFrame', background=colores['fondo'])
        self.style.configure('TLabel', background=colores['fondo'], foreground=colores['texto'], font=fuentes['normal'])
        self.style.configure('Primary.TButton', font=fuentes['boton'], padding=10,
                             background=colores['boton_principal'], foreground=colores['texto'])
        self.style.configure('Secondary.TButton', font=fuentes['boton'], padding=10,
                             background=colores['boton_secundario'], foreground=colores['texto'])
        self.style.configure('Small.TButton', font=fuentes['boton_pequeno'], padding=5,
                             background=colores['boton_secundario'], foreground=colores['texto'])

        # botón salir persistente
        btn_salir = ttk.Button(self.root, text="Salir", command=self.cerrar, style='Secondary.TButton')
        btn_salir.place(relx=0.0, rely=1.0, anchor='sw', x=10, y=-10)
        btn_salir.persistent = True

        # ya no usamos el mini‑juego; interfaz más limpia

        self.camera_handler = None
        # permitir forzar el uso de Picamera mediante variable de entorno
        # (útil en Raspberry Pi con cámara CSI).
        self.usar_picamera = os.environ.get("USAR_PICAMERA", "").lower() in ("1", "true", "yes")

        self.face_recognizer = FaceRecognizer()
        # Configuración de base de datos usada por la app (reutilizable)
        self.db_config = {'user': 'root', 'password': '', 'database': 'locker_scan'}
        # Cambia FaceStorage por MySQLFaceStorage para guardar en MySQL
        self.face_storage = MySQLFaceStorage(**self.db_config)
        self.encodings_conocidos = []
        self.nombres_conocidos = []
        self.modo = None                # 'abrir' o 'registrar' o None
        self.capturar = False  # Inicializa el flag de captura para registro

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

        # encabezado
        self.lbl_fecha = tk.Label(self.root, font=fuentes["titulo"],
                                  bg=colores["panel"], fg=colores["texto"])
        self.lbl_fecha.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(5,0))
        self.actualizar_header()
        # Botón de acceso rápido a administración de usuarios
        btn_admin = ttk.Button(self.root, text="Admin", command=self.abrir_admin,
                       style='Small.TButton')
        btn_admin.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

        # marco central para imagen (placeholder gris)
        self.frame_central = tk.Frame(self.root, bg="#bbbbbb", bd=2, relief='ridge')
        self.frame_central.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.label_video = ttk.Label(self.frame_central, background="#dddddd")
        self.label_video.place(relx=0, rely=0, relwidth=1, relheight=1)

        # panel de información derecha
        frame_info = tk.Frame(self.root, bg=colores["panel"], bd=0)
        frame_info.grid(row=1, column=1, sticky='nsew', padx=10, pady=10)
        self.lbl_registro = tk.Label(frame_info, text="Fecha y hora de registro",
                                      bg=colores["info_bg"], fg=colores["texto"],
                                      font=fuentes["normal"], wraplength=120, justify='center')
        self.lbl_registro.pack(pady=5, padx=5, fill='x')
        self.lbl_acceso = tk.Label(frame_info, text="",
                                   bg=colores["info_bg"], fg=colores["texto"],
                                   font=fuentes["normal"], wraplength=120, justify='center')
        self.lbl_acceso.pack(pady=5, padx=5, fill='x')

        # botones inferiores
        self.btn_left = ttk.Button(self.root, text="🔓 Abrir Locker", command=self.abrir_locker,
                                   style='Primary.TButton')
        self.btn_right = ttk.Button(self.root, text="📝 Registrar Locker", command=self.registrar_locker,
                                    style='Secondary.TButton')
        self.btn_left.grid(row=2, column=0, sticky='ew', padx=10, pady=10, ipadx=10, ipady=8)
        self.btn_right.grid(row=2, column=1, sticky='ew', padx=10, pady=10, ipadx=10, ipady=8)

    def abrir_admin(self):
        usuario = simpledialog.askstring("Usuario", "Usuario administrador:", parent=self.root)
        contraseña = simpledialog.askstring("Contraseña", "Contraseña:", show='*', parent=self.root)
        if not usuario or not contraseña:
            messagebox.showerror("Acceso denegado", "Credenciales requeridas")
            return

        try:
            auth = self.face_storage.autenticar_usuario(usuario, contraseña)
        except Exception as e:
            messagebox.showerror("Error", f"Error al autenticar: {e}")
            return

        if not auth or auth.get('rol') not in ('administrador', 'admin'):
            messagebox.showerror("Acceso denegado", "Credenciales inválidas o no es administrador")
            return

        try:
            self.mostrar_admin_panel()
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
        self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()

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
                break
            except RuntimeError as e:
                error_msg += f"\nÍndice {cam_index}: {str(e)}"
                self.camera_handler = None
        else:
            messagebox.showerror("Error de cámara", f"No se pudo abrir ninguna cámara.\n{error_msg}")
            self.volver_menu()
            return False
        # arrancar hilo según modo
        if self.modo == 'abrir':
            threading.Thread(target=self.procesar_abrir, daemon=True).start()
        elif self.modo == 'registrar':
            threading.Thread(target=self.procesar_registro, daemon=True).start()
        return True

    def abrir_locker(self):
        # configurar modo de cámara
        self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()
        if not self.encodings_conocidos:
            messagebox.showwarning("Sin registros", "No hay rostros registrados. Registre uno primero.")
            return
        self.modo = 'abrir'
        # reemplazar botones inferiores por uno de vuelta
        self.btn_left.grid_forget()
        self.btn_right.grid_forget()
        self.btn_back = ttk.Button(self.root, text="Volver", command=self.volver_menu,
                                   style='Secondary.TButton')
        self.btn_back.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        # limpiar resultados anteriores
        self.lbl_acceso.config(text="")
        self.lbl_registro.config(text="Fecha y hora de registro")
        # iniciar cámara y reconocimiento
        self.preparar_camera()

    def procesar_abrir(self):
        from recognition.utils import comparar_con_encodings
        import time

        frame_count = 0
        # mantenemos el último texto para no recalcular si no hay detección
        ultimo_resultado = "Esperando..."
        while self.camera_handler.activo:
            ret, frame = self.camera_handler.leer_frame()
            print(f"[procesar_abrir] leer_frame ret={ret}, frame shape={getattr(frame, 'shape', None)}")
            if not ret:
                print("[procesar_abrir] No se pudo leer frame, esperando...")
                time.sleep(0.01)
                continue
            frame_count += 1
            self.root.after(0, self.mostrar_frame, frame)
            if frame_count % 3 == 0:
                # lanzar reconocimiento en hilo separado para no bloquear el bucle
                copia = frame.copy()
                threading.Thread(target=self._reconocer_copia,
                                 args=(copia, comparar_con_encodings),
                                 daemon=True).start()
            # evitar saturar el bucle
            time.sleep(0.03)

    def _reconocer_copia(self, frame, comparar_func):
        """Detecta un rostro en la copia de un frame y actualiza el resultado en la GUI."""
        import face_recognition
        small = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_small)
        encodings = face_recognition.face_encodings(rgb_small, locations)
        if encodings:
            nombre = comparar_func(encodings[0], self.encodings_conocidos,
                                    self.nombres_conocidos, umbral=0.6)
            if nombre:
                texto = f"Acceso concedido a {nombre}"
                locker_text = f"Locker abierto: {nombre}"
            else:
                texto = "Acceso denegado"
                locker_text = "Locker abierto: --"
            self.root.after(0, self.actualizar_resultado, texto)
            # si hay texto de locker usamos la etiqueta si existe
        # si no se detecta rostro no cambiamos nada (mantiene último mensaje)

    def actualizar_resultado(self, texto):
        # actualiza el recuadro de acceso de la derecha
        if hasattr(self, "lbl_acceso") and self.lbl_acceso.winfo_exists():
            try:
                self.lbl_acceso.config(text=texto)
            except tk.TclError:
                pass

    def registrar_locker(self):
        self.modo = 'registrar'
        # reemplazar botones inferiores por uno de vuelta
        self.btn_left.grid_forget()
        self.btn_right.grid_forget()
        self.btn_back = ttk.Button(self.root, text="Volver", command=self.volver_menu,
                                   style='Secondary.TButton')
        self.btn_back.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        # crear controles de captura dentro del panel central (ya definido en mostrar_menu_principal)
        bottom_frame = ttk.Frame(self.frame_central)
        bottom_frame.place(relx=0.5, rely=0.9, anchor='s')
        self.btn_capturar = ttk.Button(bottom_frame, text="Tomar foto",
                                      command=self.iniciar_cuenta_regresiva,
                                      style='Primary.TButton', state="disabled")
        self.btn_capturar.pack(side='left', padx=5)
        self.label_cuenta = ttk.Label(bottom_frame, text="", font=fuentes["cuenta"], foreground="red")
        self.label_cuenta.pack(side='left', padx=5)
        # reiniciar etiquetas info
        self.lbl_registro.config(text="Fecha y hora de registro")
        self.lbl_acceso.config(text="")
        # iniciar cámara y registrar
        if self.preparar_camera():
            self.btn_capturar.state(['!disabled'])

    def procesar_registro(self):
        import time
        while self.camera_handler.activo:
            ret, frame = self.camera_handler.leer_frame()
            print(f"[procesar_registro] leer_frame ret={ret}, frame shape={getattr(frame, 'shape', None)}")
            if not ret:
                print("[procesar_registro] No se pudo leer frame, esperando...")
                time.sleep(0.01)
                continue
            # Dibujar rectángulo guía
            h, w, _ = frame.shape
            cv2.rectangle(frame, (int(w*0.3), int(h*0.2)), (int(w*0.7), int(h*0.8)), (0,255,0), 2)
            if self.capturar:
                self.capturar = False
                self.guardar_foto(frame)
            self.root.after(0, self.mostrar_frame, frame)
            time.sleep(0.03)

    def guardar_foto(self, frame):
        nombre = self.obtener_nombre_automatico()
        import face_recognition
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        if locations:
            if self.camera_handler:
                self.camera_handler.stop()
            # Convertir frame a JPEG en memoria
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                imagen_bytes = buffer.tobytes()
                try:
                    print(f"[guardar_foto] Intentando guardar usuario: {nombre}")
                    usuario_id = self.face_storage.guardar_usuario(nombre, '1234', 'usuario')
                    print(f"[guardar_foto] Usuario guardado con id: {usuario_id}")
                    self.face_storage.guardar_imagen(usuario_id, imagen_bytes)
                    print(f"[guardar_foto] Imagen guardada para usuario id: {usuario_id}")
                except Exception as e:
                    print(f"[guardar_foto] ERROR al guardar en MySQL: {e}")
            else:
                print("[guardar_foto] ERROR al convertir frame a JPEG")
            self.mostrar_frame(frame)
            hilo = time.strftime("%d/%m/%Y %H:%M:%S")
            self.lbl_registro.config(text=hilo)
            # esperar unos segundos antes de volver al menú
            self.root.after(4000, self.volver_menu)
        else:
            self.root.after(0, lambda: messagebox.showerror("Error", "No se detectó rostro. Intente de nuevo."))
            self.root.after(0, lambda: self.btn_capturar.config(state="normal"))

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
        # Log para depuración
        print("[mostrar_frame] Recibido frame para mostrar", type(frame), frame.shape if hasattr(frame, 'shape') else None)
        if not (hasattr(self, "label_video") and self.label_video.winfo_exists()):
            print("[mostrar_frame] label_video no existe o fue destruido")
            return
        try:
            # Convertir a RGB y luego a ImageTk
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            # redimensionar al tamaño actual del widget; evita fijar a 800x480 y elimina
            # la posibilidad de que el contenido se vea 'negro' si el label aún no tiene
            # ese tamaño.
            w = self.label_video.winfo_width() or 800
            h = self.label_video.winfo_height() or 480
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label_video.imgtk = imgtk
            self.label_video.configure(image=imgtk)
            print(f"[mostrar_frame] Frame mostrado en label_video de tamaño {w}x{h}")
        except tk.TclError as e:
            print(f"[mostrar_frame] TclError: {e}")
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
        if self.admin_camera_handler:
            self.admin_camera_handler.stop()
            self.admin_camera_handler = None
        self.mostrar_menu_principal()