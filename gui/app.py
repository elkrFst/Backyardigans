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
        # Configuración de base de datos usada por la app (reutilizable)
        self.db_config = {'user': 'root', 'password': '', 'database': 'locker_scan'}
        # Cambia FaceStorage por MySQLFaceStorage para guardar en MySQL
        self.face_storage = MySQLFaceStorage(**self.db_config)
        self.encodings_conocidos = []
        self.nombres_conocidos = []
        self.modo = None                # 'abrir' o 'registrar' o None
        self.capturar = False           # usado en registro
        self.ultimo_registro_acceso = 0  # Throttle de acceso para evitar conteos inflados
        self.stats_frame = None
        self.stats_canvas = None




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
        # Limpiar referencias a widgets que pueden quedar colgando de pantallas previas
        self.stats_canvas = None
        self.stats_frame = None
        self.admin_video_label = None
        self.label_video = None

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
        # darle más espacio al panel de cámara (cuadro más grande)
        self.root.grid_columnconfigure(0, weight=5)
        self.root.grid_columnconfigure(1, weight=2)

        # encabezado + título principal
        header_frame = ttk.Frame(self.root, style='Card.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=(10,5))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        header_frame.grid_columnconfigure(2, weight=0)

        lbl_titulo = ttk.Label(header_frame, text="Smart Locker - Control Facial",
                               style='Header.TLabel')
        lbl_titulo.grid(row=0, column=0, sticky='w', padx=12, pady=10)

        self.lbl_fecha = ttk.Label(header_frame, text="", style='Info.TLabel')
        self.lbl_fecha.grid(row=0, column=1, sticky='e', padx=12, pady=10)
        self.actualizar_header()

        # Botón de acceso rápido a administración de usuarios
        btn_admin = ttk.Button(header_frame, text="Admin", command=self.abrir_admin,
                       style='Small.TButton')
        btn_admin.grid(row=0, column=2, sticky='e', padx=12, pady=10)

        # marco central para video con borde suave y tamaño fijo para acceso
        self.frame_central = ttk.Frame(self.root, style='Card.TFrame')
        self.frame_central.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.frame_central.grid_propagate(False)
        self.frame_central.config(width=920, height=540)

        self.label_video = ttk.Label(self.frame_central, background="#101828", foreground="#f8fafc",
                                     text="Cámara inactiva", anchor='center', font=fuentes['subtitulo'])
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
        self.lbl_acceso.grid(row=1, column=0, padx=10, pady=(0, 8), sticky='ew')

        self.lbl_usuario = ttk.Label(frame_info, text="Usuario: --", style='Info.TLabel', anchor='center', justify='center')
        self.lbl_usuario.grid(row=2, column=0, padx=10, pady=(0, 8), sticky='ew')

        self.lbl_estado = ttk.Label(frame_info, text="Estado: --", style='Info.TLabel', anchor='center', justify='center')
        self.lbl_estado.grid(row=3, column=0, padx=10, pady=(0, 15), sticky='ew')

        # botones inferiores
        self.btn_left = ttk.Button(self.root, text="🔓 Acceder al Locker", command=self.abrir_locker,
                                   style='Primary.TButton')
        self.btn_left.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=10, ipadx=10, ipady=8)

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

        # Encabezado
        header_frame = ttk.Frame(self.root, style='Card.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=(10,5))
        lbl_heading = ttk.Label(header_frame, text="Panel de Administración", style='Header.TLabel')
        lbl_heading.pack(side='left', padx=12, pady=10)
        btn_back = ttk.Button(header_frame, text="Volver", command=self.volver_menu, style='Secondary.TButton')
        btn_back.pack(side='right', padx=12, pady=10)

        # Notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)

        # Pestaña CRUD
        crud_frame = ttk.Frame(notebook)
        notebook.add(crud_frame, text="Gestión de Usuarios")

        # Lista de usuarios
        list_frame = ttk.Frame(crud_frame)
        list_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        self.admin_listbox = tk.Listbox(list_frame, font=fuentes['normal'], bg='white')
        self.admin_listbox.pack(fill='both', expand=True)
        bot_frame = ttk.Frame(list_frame)
        bot_frame.pack(fill='x', pady=5)
        ttk.Button(bot_frame, text="Refrescar", command=self.admin_refrescar_lista, style='Small.TButton').pack(side='left', padx=2)
        ttk.Button(bot_frame, text="Eliminar", command=self.admin_eliminar_usuario, style='Secondary.TButton').pack(side='left', padx=2)

        # Formulario agregar usuario
        form_frame = ttk.LabelFrame(crud_frame, text="Agregar Usuario")
        form_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        ttk.Label(form_frame, text="Nombre de usuario:", style='Info.TLabel').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.admin_entry_nombre = ttk.Entry(form_frame, font=fuentes['normal'])
        self.admin_entry_nombre.grid(row=0, column=1, sticky='ew', padx=10, pady=5)

        ttk.Label(form_frame, text="Contraseña:", style='Info.TLabel').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.admin_entry_contrasena = ttk.Entry(form_frame, show='*', font=fuentes['normal'])
        self.admin_entry_contrasena.grid(row=1, column=1, sticky='ew', padx=10, pady=5)

        ttk.Label(form_frame, text="Rol:", style='Info.TLabel').grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.admin_entry_rol = ttk.Combobox(form_frame, values=['usuario', 'administrador'], state='readonly', font=fuentes['normal'])
        self.admin_entry_rol.set('usuario')
        self.admin_entry_rol.grid(row=2, column=1, sticky='ew', padx=10, pady=5)

        form_frame.grid_columnconfigure(1, weight=1)

        self.admin_video_label = tk.Label(form_frame, text="Cámara inactiva", bg='black', fg='white', font=fuentes['subtitulo'])
        self.admin_video_label.grid(row=3, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)

        # Hacer que el cuadro de admin use todo el espacio disponible y controle el tamaño fijo
        form_frame.grid_rowconfigure(3, weight=1)
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        self.admin_btn_iniciar = ttk.Button(btn_frame, text="Iniciar Cámara", command=self.admin_iniciar_camera, style='Primary.TButton')
        self.admin_btn_iniciar.pack(side='left', padx=5)
        self.admin_btn_detener = ttk.Button(btn_frame, text="Detener Cámara", command=self.admin_detener_camera, style='Secondary.TButton')
        self.admin_btn_detener.pack(side='left', padx=5)
        self.admin_btn_capturar = ttk.Button(btn_frame, text="Capturar Foto", command=self.admin_capturar_foto, style='Primary.TButton', state='disabled')
        self.admin_btn_capturar.pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Guardar Usuario", command=self.admin_guardar_usuario, style='Primary.TButton').pack(side='left', padx=5)

        # Pestaña Estadísticas
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Estadísticas")
        self.stats_frame = stats_frame

        # Botón de refrescar estadísticas
        refresh_frame = ttk.Frame(stats_frame)
        refresh_frame.pack(fill='x', pady=5)
        ttk.Button(refresh_frame, text="Refrescar Estadísticas", command=self.admin_refrescar_estadisticas, style='Secondary.TButton').pack(side='right', padx=10)

        # Gráficos
        self.stats_canvas = None
        self.admin_refrescar_estadisticas()

    def admin_refrescar_estadisticas(self):
        try:
            # Validar que el frame de estadísticas todavía existe
            if not hasattr(self, 'stats_frame') or self.stats_frame is None or not self.stats_frame.winfo_exists():
                print('[admin_refrescar_estadisticas] stats_frame no existe, abortando')
                self.stats_canvas = None
                return

            # Limpiar gráficos anteriores con manejo robusto
            if hasattr(self, 'stats_canvas') and self.stats_canvas:
                try:
                    self.stats_canvas.get_tk_widget().destroy()
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    print(f'[stats] Error limpiando canvas previo: {e}')
                finally:
                    self.stats_canvas = None

            # Obtener datos actualizados
            usuario_total = self.face_storage.contar_usuarios_registrados()
            usuario_hoy = self.face_storage.contar_usuarios_registrados_hoy()
            accesos = [
                self.face_storage.contar_accesos_hoy(),
                self.face_storage.contar_accesos_por_periodo('semana'),
                self.face_storage.contar_accesos_por_periodo('mes'),
                self.face_storage.contar_accesos_por_periodo('anio')
            ]

            try:
                import matplotlib.pyplot as plt
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

                fig = plt.Figure(figsize=(8, 6), dpi=100)
                axs = fig.subplots(2, 1, sharex=False)

                # Accesos por periodos con etiquetas numéricas
                periodos = ['Día', 'Semana', 'Mes', 'Año']
                bars = axs[0].bar(periodos, accesos, color='#4f46e5')
                axs[0].set_title('Accesos por Periodo')
                axs[0].set_ylabel('Accesos')
                axs[0].set_ylim(0, max(accesos) * 1.25 if max(accesos) > 0 else 5)
                for bar, valor in zip(bars, accesos):
                    axs[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, str(valor),
                                ha='center', va='bottom', fontweight='bold')

                # Accesos totales y usuarios activos hoy
                axs[1].bar(['Total usuarios', 'Usuarios registro hoy', 'Accesos hoy'], [usuario_total, usuario_hoy, accesos[0]],
                           color=['#059669', '#f59e0b', '#3b82f6'])
                axs[1].set_title('Resumen de Usuarios y Accesos')
                axs[1].set_ylabel('Cantidad')
                for i, v in enumerate([usuario_total, usuario_hoy, accesos[0]]):
                    axs[1].text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')

                fig.tight_layout(pad=2.0)

                # Verificar frame nuevamente antes de crear canvas
                if not self.stats_frame.winfo_exists():
                    print('[stats] stats_frame desapareció antes de crear canvas')
                    return

                self.stats_canvas = FigureCanvasTkAgg(fig, master=self.stats_frame)
                self.stats_canvas.draw()
                self.stats_canvas.get_tk_widget().pack(fill='both', expand=True)
                
            except ImportError:
                ttk.Label(self.stats_frame, text='Instale matplotlib para ver gráficos', style='Info.TLabel').pack(padx=10, pady=10)
                ttk.Label(self.stats_frame, text=f'Usuarios totales: {usuario_total}', style='Info.TLabel').pack(padx=10, pady=2)
                ttk.Label(self.stats_frame, text=f'Usuarios hoy: {usuario_hoy}', style='Info.TLabel').pack(padx=10, pady=2)
                ttk.Label(self.stats_frame, text=f'Accesos hoy: {accesos[0]}', style='Info.TLabel').pack(padx=10, pady=2)
                return
            
            # Información adicional
            if not hasattr(self, 'info_frame') or self.info_frame is None:
                self.info_frame = ttk.Frame(self.stats_frame)
                self.info_frame.pack(fill='x', pady=10)
            else:
                for widget in self.info_frame.winfo_children():
                    widget.destroy()
            
            ttk.Label(self.info_frame, text=f"Usuarios totales: {usuario_total}", style='Info.TLabel').pack()
            ttk.Label(self.info_frame, text=f"Usuarios que ingresaron hoy: {usuario_hoy}", style='Info.TLabel').pack()
            ttk.Label(self.info_frame, text=f"Accesos hoy: {accesos[0]}", style='Info.TLabel').pack()

        except Exception as e:
            print(f'[admin_refrescar_estadisticas] Error general: {e}')
            import traceback
            traceback.print_exc()


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
            self.admin_btn_capturar.config(state='normal')
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
            # tomar el tamaño actual del label para que llene el cuadro
            ancho = self.admin_video_label.winfo_width() or 640
            alto = self.admin_video_label.winfo_height() or 480
            img = Image.fromarray(rgb).resize((ancho, alto), Image.Resampling.LANCZOS)
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
        if rol not in ('usuario', 'administrador'):
            messagebox.showwarning("Rol inválido", "Seleccione rol usuario o administrador")
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
            self.admin_btn_capturar.config(state='disabled')
            self.admin_video_label.configure(image='', text='Cámara detenida', bg='black')

    def actualizar_lista_encodings(self):
        self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()

    def actualizar_header(self):
        """Actualiza la etiqueta de fecha/hora cada segundo.

        Se usa la hora local del sistema. Si la Pi está configurada a la zona
        de México obtendrá la hora correcta.
        """
        ahora = time.strftime("%d/%m/%Y %H:%M:%S")
        if hasattr(self, 'lbl_fecha') and self.lbl_fecha.winfo_exists():
            try:
                self.lbl_fecha.config(text=ahora)
            except tk.TclError:
                pass
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
        try:
            self.btn_right.grid_forget()
        except AttributeError:
            pass
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
                copia = frame.copy()
                threading.Thread(target=self._reconocer_copia,
                                 args=(copia, comparar_con_encodings),
                                 daemon=True).start()
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
                estado = 'concedido'
            else:
                texto = "Acceso denegado"
                estado = 'denegado'
                nombre = 'desconocido'
        else:
            texto = "Acceso denegado - no se detecta rostro"
            nombre = '--'
            estado = 'sin_rostro'

        usuario_id = None
        if nombre and nombre not in (None, '--', 'desconocido'):
            usuario_id = self.face_storage.obtener_usuario_por_nombre(nombre)

        # Limitar las inserciones de accesos para que no sea un evento por cada frame
        ahora = time.time()
        if ahora - self.ultimo_registro_acceso >= 20.0:
            try:
                self.face_storage.guardar_acceso(usuario_id, None if nombre in (None, '--', 'desconocido') else nombre, estado)
                self.ultimo_registro_acceso = ahora
            except Exception as e:
                print(f"[reconocer_copia] Error guardando acceso: {e}")

        self.root.after(0, self.actualizar_resultado, texto, nombre if nombre else '--', estado)

    def actualizar_resultado(self, texto, usuario='--', estado='--'):
        if hasattr(self, "lbl_acceso") and self.lbl_acceso.winfo_exists():
            try:
                self.lbl_acceso.config(text=texto)
            except tk.TclError:
                pass
        if hasattr(self, "lbl_usuario") and self.lbl_usuario.winfo_exists():
            try:
                self.lbl_usuario.config(text=f"Usuario: {usuario}")
            except tk.TclError:
                pass
        if hasattr(self, "lbl_estado") and self.lbl_estado.winfo_exists():
            try:
                self.lbl_estado.config(text=f"Estado: {estado}")
            except tk.TclError:
                pass

    def registrar_locker(self):
        self.modo = 'registrar'
        # pedir nombre de usuario antes de iniciar registro
        nombre_usuario = simpledialog.askstring("Registro", "Nombre de usuario:", parent=self.root)
        if not nombre_usuario:
            messagebox.showwarning("Registro cancelado", "Debe ingresar un nombre de usuario")
            return
        self.nombre_registro_actual = nombre_usuario.strip()

        # reemplazar botones inferiores por uno de vuelta
        self.btn_left.grid_forget()
        try:
            self.btn_right.grid_forget()
        except AttributeError:
            pass
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
        nombre = getattr(self, 'nombre_registro_actual', None) or self.obtener_nombre_automatico()
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
                    os.makedirs('rostros_conocidos', exist_ok=True)
                    cv2.imwrite(os.path.join('rostros_conocidos', f"{nombre}.jpg"), frame)
                except Exception as e:
                    print(f"[guardar_foto] ERROR al guardar en MySQL: {e}")
                    messagebox.showerror("Error", f"No se pudo guardar usuario: {e}")
                    self.btn_capturar.config(state="normal")
                    return
            else:
                print("[guardar_foto] ERROR al convertir frame a JPEG")
                messagebox.showerror("Error", "No se pudo convertir la imagen")
                self.btn_capturar.config(state="normal")
                return
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
            # Tamaño fijo para cámara de acceso: evita que se mueva al cambiar tamaño de ventana
            target_w = 900
            target_h = 540
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label_video.imgtk = imgtk
            self.label_video.configure(image=imgtk, text='')
            print(f"[mostrar_frame] Frame mostrado en label_video de tamaño {target_w}x{target_h}")
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