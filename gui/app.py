import os
import sys
import time

# permitir ejecución directa desde el subdirectorio gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
from gui.styles import colores, fuentes
from camera.camera_handler import CameraHandler
from recognition.face_recognizer import FaceRecognizer
from database.face_storage import FaceStorage
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
        # permitir forzar el uso de Picamera mediante variable de entorno
        # (útil en Raspberry Pi con cámara CSI).
        self.usar_picamera = os.environ.get("USAR_PICAMERA", "").lower() in ("1", "true", "yes")

        self.face_recognizer = FaceRecognizer()
        self.face_storage = FaceStorage("rostros_conocidos")
        self.encodings_conocidos = []
        self.nombres_conocidos = []
        self.modo = None                # 'abrir' o 'registrar' o None
        self.capturar = False           # usado en registro

        self.mostrar_menu_principal()

    def cerrar(self):
        if self.camera_handler:
            self.camera_handler.stop()
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

        # marco central para video con borde suave
        self.frame_central = ttk.Frame(self.root, style='Card.TFrame')
        self.frame_central.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.label_video = ttk.Label(self.frame_central, background="#101828")
        self.label_video.place(relx=0, rely=0, relwidth=1, relheight=1)

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
        self.lbl_acceso.grid(row=1, column=0, padx=10, pady=(0, 15), sticky='ew')

        # botones inferiores
        self.btn_left = ttk.Button(self.root, text="🔓 Abrir Locker", command=self.abrir_locker,
                                   style='Primary.TButton')
        self.btn_right = ttk.Button(self.root, text="📝 Registrar Locker", command=self.registrar_locker,
                                    style='Secondary.TButton')
        self.btn_left.grid(row=2, column=0, sticky='ew', padx=10, pady=10, ipadx=10, ipady=8)
        self.btn_right.grid(row=2, column=1, sticky='ew', padx=10, pady=10, ipadx=10, ipady=8)

    def abrir_admin(self):
        # ya no se utiliza; método mantenido solo para compatibilidad
        pass

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
        """Inicia el handler de cámara y arranca el hilo correspondiente al modo."""
        cam_index = int(os.environ.get("CAMERA_INDEX", "0"))
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
                raise RuntimeError("La cámara no devolvió imágenes tras iniciar.")
        except RuntimeError as e:
            messagebox.showerror("Error de cámara", str(e))
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
            if not ret:
                # si no se pudo leer saltamos, pero damos un pequeño descanso
                time.sleep(0.01)
                continue
            frame_count += 1
            # mostrar siempre el video
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
        # asegurarse de que flag esté inicializada antes del hilo
        self.capturar = False
        # iniciar cámara y registrar
        if self.preparar_camera():
            self.btn_capturar.state(['!disabled'])

    def procesar_registro(self):
        import time
        while self.camera_handler.activo:
            ret, frame = self.camera_handler.leer_frame()
            if not ret:
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
        # Generar nombre automático basado en los archivos existentes
        nombre = self.obtener_nombre_automatico()
        # Verificar rostro
        import face_recognition
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        if locations:
            # detener cámara para que no sobrescriba la captura
            if self.camera_handler:
                self.camera_handler.stop()
            # Guardar usando el almacenamiento centralizado
            ruta = self.face_storage.guardar(frame, nombre)
            # mostrar la foto capturada en el cuadro gris
            self.mostrar_frame(frame)
            # actualizar etiqueta con fecha y hora de registro
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
        # Asegurarse de que la etiqueta siga existiendo antes de intentar mostrar
        if not (hasattr(self, "label_video") and self.label_video.winfo_exists()):
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
        except tk.TclError:
            # pudiera ocurrir si el widget se destruyó mientras se procesaba
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
        self.mostrar_menu_principal()