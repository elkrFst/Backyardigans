import tkinter as tk
from tkinter import messagebox
from gui.styles import colores, fuentes
from gui.admin_window import AdminWindow
from camera.camera_handler import CameraHandler
from recognition.face_recognizer import FaceRecognizer
from database.face_storage import FaceStorage
import threading

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Lockers - Profesional")
        self.root.geometry("900x700")
        self.root.configure(bg=colores["fondo"])
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.camera_handler = None
        self.face_recognizer = FaceRecognizer()
        self.face_storage = FaceStorage("rostros_conocidos")
        self.encodings_conocidos = []
        self.nombres_conocidos = []

        self.mostrar_menu_principal()

    def cerrar(self):
        if self.camera_handler:
            self.camera_handler.stop()
        self.root.destroy()

    def limpiar_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def mostrar_menu_principal(self):
        self.limpiar_frame()
        # Título
        tk.Label(self.root, text="Sistema de Acceso a Lockers", font=fuentes["titulo"],
                 bg=colores["fondo"], fg=colores["texto"]).pack(pady=30)

        # Botones principales
        btn_abrir = tk.Button(self.root, text="Abrir Locker", command=self.abrir_locker,
                              font=fuentes["boton"], bg=colores["boton_principal"], fg="white",
                              relief="flat", padx=30, pady=15, cursor="hand2")
        btn_abrir.pack(pady=20)

        btn_registrar = tk.Button(self.root, text="Registrar Locker", command=self.registrar_locker,
                                  font=fuentes["boton"], bg=colores["boton_secundario"], fg="white",
                                  relief="flat", padx=30, pady=15, cursor="hand2")
        btn_registrar.pack(pady=20)

        # Botón Admin en esquina inferior derecha
        btn_admin = tk.Button(self.root, text="Admin", command=self.abrir_admin,
                              font=fuentes["boton_pequeno"], bg=colores["admin"], fg="white",
                              relief="flat", padx=15, pady=5, cursor="hand2")
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
        # Video
        self.label_video = tk.Label(self.root, bg="black")
        self.label_video.pack(pady=10)

        self.label_resultado = tk.Label(self.root, text="", font=fuentes["resultado"],
                                         bg=colores["fondo"], fg=colores["texto"])
        self.label_resultado.pack(pady=10)

        btn_volver = tk.Button(self.root, text="Volver al menú", command=self.volver_menu,
                               font=fuentes["boton"], bg=colores["volver"], fg="white",
                               relief="flat", padx=20, pady=10, cursor="hand2")
        btn_volver.pack(pady=10)

        # Iniciar cámara
        self.camera_handler = CameraHandler(resolucion=(640, 480))
        self.camera_handler.iniciar()
        threading.Thread(target=self.procesar_abrir, daemon=True).start()

    def procesar_abrir(self):
        from recognition.utils import comparar_con_encodings
        frame_count = 0
        ultimo_resultado = "Esperando..."
        while self.camera_handler.activo:
            ret, frame = self.camera_handler.leer_frame()
            if not ret:
                continue
            frame_count += 1
            if frame_count % 3 == 0:
                # Reducir y convertir
                small = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
                rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                # Detectar
                import face_recognition
                locations = face_recognition.face_locations(rgb_small)
                encodings = face_recognition.face_encodings(rgb_small, locations)
                if encodings:
                    nombre = comparar_con_encodings(encodings[0], self.encodings_conocidos,
                                                    self.nombres_conocidos, umbral=0.6)
                    if nombre:
                        ultimo_resultado = f"Acceso concedido a {nombre}"
                    else:
                        ultimo_resultado = "Acceso denegado"
                else:
                    ultimo_resultado = "No se detecta rostro"
                # Actualizar GUI
                self.root.after(0, self.actualizar_resultado, ultimo_resultado)
            # Mostrar video (con rectángulos opcionales)
            self.root.after(0, self.mostrar_frame, frame)

    def actualizar_resultado(self, texto):
        self.label_resultado.config(text=texto)

    def registrar_locker(self):
        self.limpiar_frame()
        # Pedir nombre
        tk.Label(self.root, text="Ingrese su nombre:", font=fuentes["normal"],
                 bg=colores["fondo"], fg=colores["texto"]).pack(pady=10)
        self.entry_nombre = tk.Entry(self.root, font=fuentes["normal"], width=30)
        self.entry_nombre.pack(pady=5)

        self.label_video = tk.Label(self.root, bg="black")
        self.label_video.pack(pady=10)

        self.btn_capturar = tk.Button(self.root, text="Tomar foto", command=self.iniciar_cuenta_regresiva,
                                      font=fuentes["boton"], bg=colores["capturar"], fg="white",
                                      relief="flat", padx=20, pady=10, cursor="hand2", state="disabled")
        self.btn_capturar.pack(pady=5)

        self.label_cuenta = tk.Label(self.root, text="", font=fuentes["cuenta"], bg=colores["fondo"], fg="red")
        self.label_cuenta.pack()

        btn_volver = tk.Button(self.root, text="Volver", command=self.volver_menu,
                               font=fuentes["boton"], bg=colores["volver"], fg="white",
                               relief="flat", padx=20, pady=10, cursor="hand2")
        btn_volver.pack(pady=10)

        self.camera_handler = CameraHandler(resolucion=(640, 480))
        self.camera_handler.iniciar()
        self.capturar = False
        threading.Thread(target=self.procesar_registro, daemon=True).start()

    def procesar_registro(self):
        while self.camera_handler.activo:
            ret, frame = self.camera_handler.leer_frame()
            if not ret:
                continue
            # Dibujar rectángulo guía
            h, w, _ = frame.shape
            cv2.rectangle(frame, (int(w*0.3), int(h*0.2)), (int(w*0.7), int(h*0.8)), (0,255,0), 2)
            if self.capturar:
                self.capturar = False
                self.guardar_foto(frame)
            self.root.after(0, self.mostrar_frame, frame)

    def guardar_foto(self, frame):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            self.root.after(0, lambda: messagebox.showerror("Error", "Debe ingresar un nombre"))
            self.root.after(0, lambda: self.btn_capturar.config(state="normal"))
            return
        # Verificar rostro
        import face_recognition
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        if locations:
            # Guardar
            filename = f"rostros_conocidos/{nombre}.jpg"
            cv2.imwrite(filename, frame)
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
        # Convertir a RGB y luego a ImageTk
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.label_video.imgtk = imgtk
        self.label_video.configure(image=imgtk)

    def volver_menu(self):
        if self.camera_handler:
            self.camera_handler.stop()
        self.mostrar_menu_principal()