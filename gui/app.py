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
from gui.admin_window import AdminWindow
from camera.camera_handler import CameraHandler
from recognition.face_recognizer import FaceRecognizer
from database.face_storage import FaceStorage
import threading
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Lockers - Profesional")
        self.root.geometry("800x480")
        self.root.resizable(False, False)  # Evita redimensionar la ventana para mantener alineación
        self.root.configure(bg=colores["fondo"])
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
        self.style.configure('Primary.TButton', font=fuentes['boton'], padding=10)
        self.style.configure('Secondary.TButton', font=fuentes['boton'], padding=10)
        self.style.configure('Small.TButton', font=fuentes['boton_pequeno'], padding=5)

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
        self.face_storage = FaceStorage("rostros_conocidos")
        self.encodings_conocidos = []
        self.nombres_conocidos = []

        self.mostrar_menu_principal()

    def cerrar(self):
        if self.camera_handler:
            self.camera_handler.stop()
        self.root.destroy()

    def crear_fondo(self):
        """Establece un fondo sencillo usando el color de tema.

        La interfaz ahora usa un tono claro, así que no hacen falta adornos
        ni degradados complejos. Se crea un `Label` transparente que ocupa la
        ventana completa y evita que se vean widgets anteriores al limpiar.
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
        self.limpiar_frame()
        # Configurar grid para centrar
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        # Ventana central para agrupar elementos
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0)

        # Título
        ttk.Label(frame, text="Sistema de Acceso a Lockers", font=fuentes["titulo"]).pack(pady=15)

        # Botones principales
        btn_abrir = ttk.Button(frame, text="Abrir Locker", command=self.abrir_locker,
                                style='Primary.TButton')
        btn_abrir.pack(pady=10, ipadx=15, ipady=8)

        btn_registrar = ttk.Button(frame, text="Registrar Locker", command=self.registrar_locker,
                                   style='Secondary.TButton')
        btn_registrar.pack(pady=10, ipadx=15, ipady=8)

        # Botón Admin en esquina inferior derecha
        btn_admin = ttk.Button(self.root, text="Admin", command=self.abrir_admin,
                               style='Small.TButton')
        btn_admin.place(relx=0.95, rely=0.95, anchor="se")

    def abrir_admin(self):
        # Ventana emergente de administración
        AdminWindow(self.root, self.face_storage, self.actualizar_lista_encodings)

    def actualizar_lista_encodings(self):
        self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()

    def abrir_locker(self):
        # Cargar encodings
        self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()
        if not self.encodings_conocidos:
            messagebox.showwarning("Sin registros", "No hay rostros registrados. Registre uno primero.")
            self.mostrar_menu_principal()
            return

        self.limpiar_frame()
        # Configurar grid para layout fijo
        self.root.grid_rowconfigure(0, weight=1)  # video ocupa la mayor parte
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_columnconfigure(0, weight=1)
        # Video
        self.label_video = ttk.Label(self.root, background="black")
        self.label_video.grid(row=0, column=0, sticky='nsew')

        # etiqueta con información adicional del locker
        self.label_locker = ttk.Label(self.root, text="Locker: --", font=fuentes["resultado"])
        self.label_locker.grid(row=1, column=0, pady=2)
        self.label_resultado = ttk.Label(self.root, text="", font=fuentes["resultado"])
        self.label_resultado.grid(row=2, column=0, pady=2)

        btn_volver = ttk.Button(self.root, text="Volver al menú", command=self.volver_menu,
                                 style='Secondary.TButton')
        btn_volver.grid(row=3, column=0, pady=5)

        # Iniciar cámara (index configurable con variable de entorno CAMERA_INDEX)
        cam_index = int(os.environ.get("CAMERA_INDEX", "0"))
        try:
            self.camera_handler = CameraHandler(fuente=cam_index,
                                                resolucion=(640, 480),
                                                usar_picamera=self.usar_picamera)
            self.camera_handler.iniciar()
            # esperar un frame válido antes de iniciar el bucle de reconocimiento
            for _ in range(15):
                valid, _ = self.camera_handler.leer_frame()
                if valid:
                    break
                time.sleep(0.03)
            else:
                raise RuntimeError("La cámara no devolvió imágenes tras iniciar.")
        except RuntimeError as e:
            messagebox.showerror("Error de cámara", str(e))
            self.mostrar_menu_principal()
            return
        threading.Thread(target=self.procesar_abrir, daemon=True).start()

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
                locker_text = f"Locker abierto: {nombre}"  # placeholder vínculo usuario-locker
            else:
                texto = "Acceso denegado"
                locker_text = "Locker abierto: --"
        else:
            texto = "No se detecta rostro"
            locker_text = "Locker abierto: --"
        self.root.after(0, self.actualizar_resultado, texto)
        # actualizar también la etiqueta de locker si existe
        if hasattr(self, 'label_locker') and self.label_locker.winfo_exists():
            self.root.after(0, lambda: self.label_locker.config(text=locker_text))

    def actualizar_resultado(self, texto):
        # la etiqueta puede haber sido destruida si el usuario cambió de pantalla
        if hasattr(self, "label_resultado") and self.label_resultado.winfo_exists():
            try:
                self.label_resultado.config(text=texto)
            except tk.TclError:
                pass

    def registrar_locker(self):
        self.limpiar_frame()
        # Configurar grid para video a pantalla completa
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        # cámara ocupa toda la ventana durante el registro
        self.label_video = ttk.Label(self.root, background="black")
        self.label_video.grid(row=0, column=0, sticky='nsew')

        # botones y cuenta regresiva se superponen sobre el video en la parte inferior
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.place(relx=0.5, rely=0.9, anchor='s')

        self.btn_capturar = ttk.Button(bottom_frame, text="Tomar foto", command=self.iniciar_cuenta_regresiva,
                                      style='Primary.TButton', state="disabled")
        self.btn_capturar.pack(side='left', padx=5)

        self.label_cuenta = ttk.Label(bottom_frame, text="", font=fuentes["cuenta"], foreground="red")
        self.label_cuenta.pack(side='left', padx=5)

        # usar grid en lugar de pack para mantener coherencia con el layout
        # principal (grid) y evitar errores de mezcla de gestores de geometría.
        btn_volver = ttk.Button(self.root, text="Volver", command=self.volver_menu,
                               style='Secondary.TButton')
        btn_volver.grid(row=1, column=0, pady=5, ipadx=15, ipady=6, sticky='s')

        cam_index = int(os.environ.get("CAMERA_INDEX", "0"))
        try:
            self.camera_handler = CameraHandler(fuente=cam_index,
                                                resolucion=(640, 480),
                                                usar_picamera=self.usar_picamera)
            self.camera_handler.iniciar()
            # asegurarnos de que la cámara entregue al menos un frame
            for _ in range(15):
                valid, _ = self.camera_handler.leer_frame()
                if valid:
                    break
                time.sleep(0.03)
            else:
                raise RuntimeError("La cámara no devolvió imágenes tras iniciar.")
        except RuntimeError as e:
            messagebox.showerror("Error de cámara", str(e))
            self.mostrar_menu_principal()
            return
        # habilitar botón de captura ahora que la cámara está activa
        self.btn_capturar.state(['!disabled'])
        self.capturar = False
        threading.Thread(target=self.procesar_registro, daemon=True).start()

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
            # Guardar usando el almacenamiento centralizado
            ruta = self.face_storage.guardar(frame, nombre)
            self.root.after(0, lambda: messagebox.showinfo("Éxito", f"Rostro registrado como {nombre}"))
            self.root.after(0, self.volver_menu)
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