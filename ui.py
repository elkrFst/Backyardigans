"""Interfaz gráfica (Tkinter) - Todas las pantallas y widgets"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog
import cv2
from PIL import Image, ImageTk
import threading
from datetime import datetime
import time

from config import COLORES, FUENTES, ADMIN_CONFIG, WINDOW_SIZE, WINDOW_FULLSCREEN
from core import Camera, FaceRecognizer
from arduino_led_controller import obtener_arduino_led  # MODIFICADO: importación correcta


# ============================================================================
# PANTALLAS PRINCIPALES
# ============================================================================
class UIApp:
    """Aplicación principal - Gestiona todas las pantallas"""
    
    def __init__(self, root, db, face_recognizer):
        self.root = root
        self.db = db
        self.face_recognizer = face_recognizer
        self.led_controller = obtener_arduino_led()  # MODIFICADO: crear controlador de LED único
        self.camera = None
        self.encodings_conocidos = []
        self.nombres_conocidos = []
        self.modo = None  # 'abrir' o 'registrar'
        self.led_registro_activo = False  # Rastrear si LED está encendido durante registro
        self.preview_pausado = False  # Control para pausar preview
        self.frame_count = 0  # Contador para procesar solo cada X frames
        self.detect_interval = 5  # Procesar detección cada 5 frames
        
        # Configurar ventana
        self.root.title("Sistema de Lockers - Reconocimiento Facial")
        self.root.geometry(WINDOW_SIZE)
        if WINDOW_FULLSCREEN:
            self.root.attributes('-fullscreen', True)
        self.root.configure(bg=COLORES["fondo"])
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)
        
        # Mostrar ventana inmediatamente
        self.root.update()
        self.root.deiconify()
        
        # Estilos
        self._configurar_estilos()
        
        # Botón Salir persistente
        self.btn_salir = ttk.Button(self.root, text="Salir", command=self.cerrar, style='Secondary.TButton')
        self.btn_salir.place(relx=0.0, rely=1.0, anchor='sw', x=14, y=-12)
        
        self.mostrar_menu_principal()
    
    def _configurar_estilos(self):
        """Configura estilos ttk"""
        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
        except:
            pass
        
        style.configure('TFrame', background=COLORES['fondo'])
        style.configure('TLabel', background=COLORES['fondo'], foreground=COLORES['texto'], font=FUENTES['normal'])
        style.configure('Header.TLabel', background=COLORES['panel'], foreground=COLORES['texto'], font=FUENTES['titulo'])
        style.configure('Subtitle.TLabel', background=COLORES['panel'], foreground=COLORES['subtexto'], font=FUENTES['subtitulo'])
        style.configure('Card.TFrame', background=COLORES['panel'], borderwidth=0, relief='flat')
        style.configure('Info.TLabel', background=COLORES['info_bg'], foreground=COLORES['texto'], font=FUENTES['subtitulo'])
        style.configure('Status.TLabel', background=COLORES['panel_sec'], foreground=COLORES['texto'], font=FUENTES['subtitulo'])
        style.configure('Section.TLabel', background=COLORES['panel'], foreground=COLORES['texto'], font=FUENTES['subtitulo'])
        
        style.configure('Primary.TButton', font=FUENTES['boton'], padding=12, background=COLORES['boton_principal'], foreground=COLORES['texto'])
        style.map('Primary.TButton', background=[('active', COLORES['boton_principal_hover'])])
        
        style.configure('Secondary.TButton', font=FUENTES['boton'], padding=12, background=COLORES['boton_secundario'], foreground=COLORES['texto'])
        style.map('Secondary.TButton', background=[('active', COLORES['boton_secundario_hover'])])
        
        style.configure('Small.TButton', font=FUENTES['boton_pequeno'], padding=8, background=COLORES['boton_secundario'], foreground=COLORES['texto'])
        style.map('Small.TButton', background=[('active', COLORES['boton_secundario_hover'])])
        
        style.configure('TNotebook', background=COLORES['fondo'], borderwidth=0)
        style.configure('TNotebook.Tab', background=COLORES['panel'], foreground=COLORES['texto'], font=FUENTES['boton'], padding=[12, 8])
        style.map('TNotebook.Tab', background=[('selected', COLORES['boton_principal'])], foreground=[('selected', COLORES['texto'])])
    
    def limpiar_frame(self):
        """Elimina todos los widgets excepto persistentes"""
        for widget in self.root.winfo_children():
            if widget != self.btn_salir:
                widget.destroy()
    
    def mostrar_menu_principal(self):
        """Pantalla principal con video y opciones"""
        print("[UI] Iniciando menú principal...")
        self.limpiar_frame()
        self.modo = None
        
        try:
            header = ttk.Frame(self.root, style='Card.TFrame')
            header.pack(fill='x', padx=10, pady=(10, 5))
            
            title_frame = ttk.Frame(header, style='Card.TFrame')
            title_frame.pack(side='left', fill='x', expand=True, padx=(10, 0), pady=10)
            ttk.Label(title_frame, text="Smart Locker", style='Header.TLabel').pack(anchor='w')
            ttk.Label(title_frame, text="Abre tu locker con tu rostro de forma rápida y segura.", style='Subtitle.TLabel').pack(anchor='w', pady=(4, 0))
            
            action_frame = ttk.Frame(header, style='Card.TFrame')
            action_frame.pack(side='right', padx=10, pady=10)
            ttk.Button(action_frame, text="Panel administrador", command=self.abrir_admin, style='Small.TButton').pack()
            
            contenido = ttk.Frame(self.root, style='Card.TFrame')
            contenido.pack(fill='both', expand=True, padx=10, pady=5)
            
            video_frame = ttk.Frame(contenido, style='Card.TFrame')
            video_frame.pack(side='left', fill='both', expand=True, padx=(0, 5), pady=5)
            ttk.Label(video_frame, text="Vista en vivo", style='Section.TLabel').pack(anchor='w', padx=12, pady=(12, 4))
            video_card = ttk.Frame(video_frame, style='Card.TFrame')
            video_card.pack(fill='both', expand=True, padx=10, pady=(0, 10))
            self.label_video = ttk.Label(video_card, background=COLORES['info_bg'], relief='flat')
            self.label_video.pack(fill='both', expand=True, padx=12, pady=12)
            
            info_frame = ttk.Frame(contenido, style='Card.TFrame')
            info_frame.pack(side='right', fill='y', ipadx=10, ipady=10, padx=(5, 0), pady=5)
            ttk.Label(info_frame, text="Estado del sistema", style='Section.TLabel').pack(anchor='w', padx=12, pady=(12, 4))
            
            self.lbl_estado = ttk.Label(info_frame, text="Elige una opción para comenzar.", style='Info.TLabel', justify='left', wraplength=280)
            self.lbl_estado.pack(fill='x', padx=12, pady=(0, 10))
            
            status_card = ttk.Frame(info_frame, style='Card.TFrame')
            status_card.pack(fill='x', padx=12, pady=(0, 10))
            self.lbl_resumen = ttk.Label(status_card, text="Cargando estado de lockers...", style='Status.TLabel', justify='left', wraplength=260)
            self.lbl_resumen.pack(fill='x', padx=10, pady=10)
            
            botones_frame = ttk.Frame(info_frame, style='Card.TFrame')
            botones_frame.pack(fill='x', padx=12, pady=10)
            ttk.Button(botones_frame, text="Abrir mi locker", command=self.iniciar_acceso, style='Primary.TButton').pack(fill='x', pady=6)
            ttk.Button(botones_frame, text="Registrar rostro", command=self.iniciar_registro, style='Secondary.TButton').pack(fill='x', pady=6)
            
            ttk.Label(info_frame, text="Consejo: mantén el rostro centrado y evita sombras.", style='Subtitle.TLabel', wraplength=280, justify='left').pack(fill='x', padx=12, pady=(12, 0))
            
            self._actualizar_resumen_lockers()
            self._iniciar_preview_camara()
            print("[UI] ✅ Menú principal listo")
        except Exception as e:
            print(f"[ERROR] Error creando menú: {e}")
            import traceback
            traceback.print_exc()
    
    def _actualizar_resumen_lockers(self):
        """Actualiza el resumen de estado de lockers"""
        try:
            lockers = self.db.listar_lockers(ADMIN_CONFIG['total_lockers'])
            libres = [l for l in lockers if l['estado'] == 'Libre']
            total = len(lockers)
            self.lbl_resumen.config(text=f"{len(libres)} de {total} lockers disponibles")
        except Exception as e:
            print(f"[ERROR] Resumen lockers: {e}")
            self.lbl_resumen.config(text="No se pudo cargar el estado de lockers")
    
    def _iniciar_preview_camara(self):
        """Muestra preview de cámara"""
        print("[UI] Iniciando preview de cámara...")
        try:
            if self.camera is None:
                print("[UI] Creando instancia de cámara...")
                self.camera = Camera(0)
                print("[UI] Iniciando cámara...")
                self.camera.iniciar()
            
            # Cargar rostros conocidos
            print("[UI] Cargando rostros conocidos...")
            self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()
            print(f"[UI] ✅ {len(self.nombres_conocidos)} rostros cargados")
            
            print("[UI] Iniciando actualización de preview...")
            self._actualizar_preview()
        except Exception as e:
            print(f"[ERROR] Error al iniciar cámara: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Error al iniciar cámara: {e}")
    
    def _actualizar_preview(self):
        """Actualiza el preview de la cámara - OPTIMIZADO"""
        try:
            # No actualizar si preview está pausado o en otro modo
            if not self.camera or self.modo is not None or getattr(self, 'preview_pausado', False):
                # Programar siguiente actualización
                self.root.after(100, self._actualizar_preview)
                return
            
            ret, frame = self.camera.leer_frame()
            if ret and frame is not None:
                # Voltear horizontalmente
                frame = cv2.flip(frame, 1)
                
                # Convertir BGR a RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # OPTIMIZACIÓN: Solo detectar rostros cada X frames
                self.frame_count += 1
                if self.frame_count % self.detect_interval == 0:
                    try:
                        rostros = self.face_recognizer.detectar_rostros(frame)
                        for (top, right, bottom, left) in rostros:
                            cv2.rectangle(frame_rgb, (left, top), (right, bottom), (0, 255, 0), 2)
                    except:
                        pass  # Si falla, simplemente mostrar frame
                
                # Redimensionar imagen UNA SOLA VEZ
                imagen = Image.fromarray(frame_rgb)
                imagen.thumbnail((624, 468), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image=imagen)
                
                self.label_video.config(image=photo)
                self.label_video.image = photo
        except Exception as e:
            print(f"[ERROR] Preview: {e}")
        
        # Aumentar intervalo: 100ms en lugar de 30ms para menos carga
        self.root.after(100, self._actualizar_preview)
    
    def iniciar_acceso(self):
        """Inicia proceso de acceso (abrir locker)"""
        self.modo = 'abrir'
        self.limpiar_frame()
        
        header = ttk.Frame(self.root, style='Card.TFrame')
        header.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Label(header, text="Abrir locker", style='Header.TLabel').pack(side='left', padx=12, pady=10)
        ttk.Button(header, text="Volver", command=self.mostrar_menu_principal, style='Secondary.TButton').pack(side='right', padx=12, pady=10)
        
        self.label_video = ttk.Label(self.root, background=COLORES['info_bg'], relief='flat')
        self.label_video.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.lbl_estado = ttk.Label(self.root, text="Acércate a la cámara. Tu locker se abrirá automáticamente cuando te reconozca.", style='Info.TLabel', justify='center', wraplength=600)
        self.lbl_estado.pack(fill='x', padx=20, pady=(0, 10))
        
        self._reconocer_acceso()
    
    def _reconocer_acceso(self):
        """Loop de reconocimiento facial para acceso - OPTIMIZADO"""
        if self.modo != 'abrir':
            return
        
        try:
            ret, frame = self.camera.leer_frame()
            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Intentar reconocer
                nombre = self.face_recognizer.reconocer(frame, self.encodings_conocidos, self.nombres_conocidos)
                
                if nombre:
                    nombre_limpio = nombre.replace('.jpg', '').replace('.png', '')
                    usuario = self.db.obtener_usuario_por_nombre(nombre_limpio)
                    
                    if usuario:
                        locker_num = int(nombre_limpio.replace('locker', ''))
                        # MODIFICADO: Encender LED único (sin número de locker)
                        self.led_controller.encender_led()
                        self.lbl_estado.config(text=f"¡Perfecto! Se encontró tu locker {locker_num}.")
                        messagebox.showinfo("¡Acceso concedido!", f"Locker {locker_num} abierto.")
                        # MODIFICADO: Apagar LED después de 3 segundos (sin número)
                        self.root.after(3000, lambda: self.led_controller.apagar_led())
                        self.mostrar_menu_principal()
                        return
                else:
                    self.lbl_estado.config(text="Buscando rostro... mantén tu cara frente a la cámara.")
                
                imagen = Image.fromarray(frame_rgb)
                imagen.thumbnail((624, 468), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image=imagen)
                self.label_video.config(image=photo)
                self.label_video.image = photo
        except Exception as e:
            print(f"[ERROR] Reconocimiento: {e}")
            self.lbl_estado.config(text="Error al procesar la cámara. Intenta nuevamente.")
        
        self.root.after(200, self._reconocer_acceso)
    
    def iniciar_registro(self):
        """Inicia proceso de registro de nuevo rostro - asigna automáticamente al locker disponible"""
        lockers = self.db.listar_lockers(ADMIN_CONFIG['total_lockers'])
        lockers_libres = [l for l in lockers if l['estado'] == 'Libre']
        
        if not lockers_libres:
            messagebox.showwarning("Sin lockers libres", "Todos los lockers están ocupados en este momento. Solicita a un administrador que libere uno.")
            return
        
        locker_asignado = lockers_libres[0]['locker']
        nombre_usuario = f"locker{locker_asignado}"
        
        if self.db.obtener_usuario_por_nombre(nombre_usuario):
            messagebox.showerror("Error", f"El locker {locker_asignado} ya está registrado.")
            return
        
        try:
            usuario_id = self.db.guardar_usuario(nombre_usuario, "1234", 'usuario')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo asignar el locker: {e}")
            return
        
        self.modo = 'registrar'
        self.limpiar_frame()
        
        header = ttk.Frame(self.root, style='Card.TFrame')
        header.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Label(header, text="Registrar nuevo rostro", style='Header.TLabel').pack(side='left', padx=12, pady=10)
        ttk.Button(header, text="Volver", command=self.mostrar_menu_principal, style='Secondary.TButton').pack(side='right', padx=12, pady=10)
        
        self.label_video = ttk.Label(self.root, background=COLORES['info_bg'], relief='flat')
        self.label_video.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.lbl_estado = ttk.Label(self.root, text=f"Vamos a configurar tu Locker {locker_asignado}. Mantén la cara centrada y sonríe naturalmente.", style='Info.TLabel', justify='center', wraplength=700)
        self.lbl_estado.pack(fill='x', padx=20, pady=(0, 10))
        
        botones = ttk.Frame(self.root, style='Card.TFrame')
        botones.pack(fill='x', padx=10, pady=(0, 16))
        ttk.Button(botones, text="Capturar rostro", command=self._capturar_registro, style='Primary.TButton').pack(side='left', fill='x', expand=True, padx=6)
        ttk.Button(botones, text="Cancelar", command=self.mostrar_menu_principal, style='Secondary.TButton').pack(side='left', fill='x', expand=True, padx=6)
        
        self.captura_disponible = False
        self._mostrar_registro(nombre_usuario, usuario_id, locker_asignado)
    
    def _mostrar_registro(self, nombre, usuario_id, locker_asignado):
        """Muestra video para captura de registro - OPTIMIZADO"""
        if self.modo != 'registrar':
            # Apagar LED si se sale del modo registro
            if self.led_registro_activo:
                self.led_controller.apagar_led()  # MODIFICADO: sin número
                self.led_registro_activo = False
            return
        
        try:
            ret, frame = self.camera.leer_frame()
            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detectar rostros
                rostros = self.face_recognizer.detectar_rostros(frame)
                for (top, right, bottom, left) in rostros:
                    cv2.rectangle(frame_rgb, (left, top), (right, bottom), (0, 255, 0), 3)
                
                self.captura_disponible = len(rostros) > 0
                locker_num = int(locker_asignado)
                
                if self.captura_disponible:
                    self.lbl_estado.config(text="Rostro detectado. Presiona Capturar rostro cuando estés listo.")
                    # MODIFICADO: Encender LED cuando se detecta un rostro
                    if not self.led_registro_activo:
                        self.led_controller.encender_led()  # MODIFICADO: sin número
                        self.led_registro_activo = True
                else:
                    self.lbl_estado.config(text="No detecto un rostro claro. Ajusta tu posición y prueba otra vez.")
                    # MODIFICADO: Apagar LED cuando no se detecta rostro
                    if self.led_registro_activo:
                        self.led_controller.apagar_led()  # MODIFICADO: sin número
                        self.led_registro_activo = False
                
                imagen = Image.fromarray(frame_rgb)
                imagen.thumbnail((624, 468), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image=imagen)
                self.label_video.config(image=photo)
                self.label_video.image = photo
                
                self.frame_actual_registro = frame
                self.nombre_registro = nombre
                self.usuario_id_registro = usuario_id
                self.locker_asignado = locker_asignado
        except Exception as e:
            print(f"[ERROR] Registro: {e}")
        
        # Intervalo de 100ms
        self.root.after(100, lambda: self._mostrar_registro(nombre, usuario_id, locker_asignado))
    
    def _capturar_registro(self):
        """Captura y guarda el rostro"""
        if not hasattr(self, 'frame_actual_registro') or not self.captura_disponible:
            messagebox.showwarning("Atención", "No se detectó un rostro claro. Ajusta tu posición e inténtalo otra vez.")
            return
        
        try:
            # Asociar rostro
            self.face_recognizer.asociar_rostro(self.nombre_registro, self.frame_actual_registro)
            
            # Guardar imagen en BD
            ret, buffer = cv2.imencode('.jpg', self.frame_actual_registro)
            if ret:
                self.db.guardar_imagen(self.usuario_id_registro, buffer.tobytes())
            
            # MODIFICADO: Parpadear LED al registrar (2 segundos, velocidad 0.3s) - sin número de locker
            threading.Thread(target=self.led_controller.parpadear_led, args=(2, 0.3), daemon=True).start()
            
            # Desmarcar que el LED de registro está activo
            self.led_registro_activo = False
            
            messagebox.showinfo("¡Listo!", f"Locker {self.locker_asignado} está registrado y listo para usar.")
            
            # Recargar rostros conocidos
            self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()
            
            self.mostrar_menu_principal()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")
            # Apagar LED si hay error
            if self.led_registro_activo:
                self.led_controller.apagar_led()  # MODIFICADO: sin número
                self.led_registro_activo = False
    
    def abrir_admin(self):
        """Abre panel de administración con login personalizado"""
        login_win = tk.Toplevel(self.root)
        login_win.title("Acceso administrador")
        login_win.geometry("380x280")
        login_win.resizable(False, False)
        login_win.configure(bg=COLORES['fondo'])

        login_win.transient(self.root)
        login_win.grab_set()

        ttk.Label(login_win, text="Ingreso administrador", style='Header.TLabel').pack(pady=(16, 4))
        ttk.Label(login_win, text="Ingresa tus credenciales para acceder al panel de control.", style='Subtitle.TLabel', wraplength=300, justify='center').pack(padx=16, pady=(0, 12))

        frame = ttk.Frame(login_win, style='Card.TFrame')
        frame.pack(fill='both', expand=True, padx=20, pady=(0, 16))

        # Campo usuario
        ttk.Label(frame, text="Usuario:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        entry_usuario = ttk.Entry(frame, font=FUENTES['normal'])
        entry_usuario.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
        entry_usuario.focus()  # Focus en usuario

        # Campo contraseña
        ttk.Label(frame, text="Contraseña:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        entry_pass = ttk.Entry(frame, font=FUENTES['normal'], show='*')
        entry_pass.grid(row=1, column=1, sticky='ew', padx=10, pady=5)

        frame.grid_columnconfigure(1, weight=1)

        # Función de login
        def login():
            usuario = entry_usuario.get().strip()
            contraseña = entry_pass.get()

            if not usuario or not contraseña:
                messagebox.showwarning("Campos requeridos", "Complete usuario y contraseña", parent=login_win)
                return

            try:
                auth = self.db.autenticar_usuario(usuario, contraseña)
                if not auth or auth.get('rol') not in ('administrador', 'admin'):
                    messagebox.showerror("Acceso denegado", "Credenciales inválidas", parent=login_win)
                    return

                login_win.destroy()
                AdminWindow(self.root, self.db, self.camera, self.face_recognizer)

            except Exception as e:
                messagebox.showerror("Error", f"Error de conexión: {e}", parent=login_win)

        def cancelar():
            login_win.destroy()

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Ingresar", command=login, style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=cancelar, style='Secondary.TButton').pack(side='left', padx=5)

        # Bind Enter para login
        entry_pass.bind('<Return>', lambda e: login())

        # Esperar a que se cierre la ventana
        self.root.wait_window(login_win)
    
    def cerrar(self):
        """Cierra la aplicación"""
        if self.camera:
            self.camera.detener()
        self.db.cerrar()
        # Limpiar LEDs al cerrar
        if hasattr(self, 'led_controller'):
            self.led_controller.limpiar()
        self.root.destroy()


# ============================================================================
# VENTANA DE ADMINISTRACIÓN
# ============================================================================
class AdminWindow(tk.Toplevel):
    """Panel de administración de usuarios"""
    
    def __init__(self, parent, db, camera, face_recognizer):
        super().__init__(parent)
        self.title("Panel de Administración")
        self.geometry("750x450")
        self.configure(bg=COLORES["fondo"])
        self.db = db
        self.camera = camera
        self.face_recognizer = face_recognizer
        
        header = ttk.Frame(self, style='Card.TFrame')
        header.pack(fill='x', padx=10, pady=10)
        title_box = ttk.Frame(header, style='Card.TFrame')
        title_box.pack(side='left', fill='x', expand=True, padx=10, pady=10)
        ttk.Label(title_box, text="Panel de administración", style='Header.TLabel').pack(anchor='w')
        ttk.Label(title_box, text="Gestiona usuarios y lockers con seguridad.", style='Subtitle.TLabel').pack(anchor='w', pady=(4, 0))
        ttk.Button(header, text="Cerrar", command=self.destroy, style='Secondary.TButton').pack(side='right', padx=10, pady=10)
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña: Usuarios
        usuarios_frame = ttk.Frame(notebook)
        notebook.add(usuarios_frame, text="Usuarios")
        self._crear_tab_usuarios(usuarios_frame)
        
        # Pestaña: Lockers
        lockers_frame = ttk.Frame(notebook)
        notebook.add(lockers_frame, text="Lockers")
        self._crear_tab_lockers(lockers_frame)
    
    def _crear_tab_usuarios(self, parent):
        """Crea la pestaña de gestión de usuarios"""
        list_frame = ttk.Frame(parent, style='Card.TFrame')
        list_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(list_frame, text="Usuarios registrados", style='Section.TLabel').pack(anchor='w', pady=(0, 8), padx=4)
        
        self.listbox_usuarios = tk.Listbox(list_frame, font=FUENTES['normal'], bd=0, highlightthickness=1, relief='solid')
        self.listbox_usuarios.pack(fill='both', expand=True, padx=4, pady=2)
        
        btn_frame = ttk.Frame(list_frame, style='Card.TFrame')
        btn_frame.pack(fill='x', pady=8)
        ttk.Button(btn_frame, text="Refrescar", command=self._refrescar_usuarios, style='Small.TButton').pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Eliminar", command=self._eliminar_usuario, style='Secondary.TButton').pack(side='left', padx=2)
        
        form_frame = ttk.LabelFrame(parent, text="Agregar administrador", style='Card.TFrame')
        form_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(form_frame, text="Usuario:", style='Subtitle.TLabel').grid(row=0, column=0, sticky='w', padx=10, pady=8)
        self.entry_usuario = ttk.Entry(form_frame, font=FUENTES['normal'])
        self.entry_usuario.grid(row=0, column=1, sticky='ew', padx=10, pady=8)
        
        ttk.Label(form_frame, text="Contraseña:", style='Subtitle.TLabel').grid(row=1, column=0, sticky='w', padx=10, pady=8)
        self.entry_pass = ttk.Entry(form_frame, show='*', font=FUENTES['normal'])
        self.entry_pass.grid(row=1, column=1, sticky='ew', padx=10, pady=8)
        
        ttk.Label(form_frame, text="Rol:", style='Subtitle.TLabel').grid(row=2, column=0, sticky='w', padx=10, pady=8)
        rol_label = ttk.Label(form_frame, text="administrador", style='Section.TLabel')
        rol_label.grid(row=2, column=1, sticky='w', padx=10, pady=8)
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Button(form_frame, text="Guardar administrador", command=self._guardar_usuario, style='Primary.TButton').grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=12)
        
        self._refrescar_usuarios()
    
    def _crear_tab_lockers(self, parent):
        """Crea la pestaña de gestión de lockers"""
        info_frame = ttk.Frame(parent, style='Card.TFrame')
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Label(info_frame, text="Lockers disponibles", style='Section.TLabel').pack(anchor='w', pady=(0, 8), padx=4)
        
        self.listbox_lockers = tk.Listbox(info_frame, font=FUENTES['normal'], height=10, bd=0, highlightthickness=1, relief='solid')
        self.listbox_lockers.pack(fill='both', expand=True, padx=4, pady=2)
        
        btn_frame = ttk.Frame(info_frame, style='Card.TFrame')
        btn_frame.pack(fill='x', padx=4, pady=10)
        ttk.Button(btn_frame, text="Refrescar", command=self._refrescar_lockers, style='Small.TButton').pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Liberar seleccionado", command=self._liberar_locker_seleccionado, style='Secondary.TButton').pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Asignar locker", command=self._asignar_locker_manual, style='Primary.TButton').pack(side='left', padx=2)
        
        self._refrescar_lockers()
    
    def _refrescar_usuarios(self):
        """Actualiza lista de usuarios"""
        self.listbox_usuarios.delete(0, tk.END)
        usuarios = self.db.listar_usuarios_detallados()
        for u in usuarios:
            self.listbox_usuarios.insert(tk.END, f"{u['nombre_usuario']} ({u['rol']})")
    
    def _refrescar_lockers(self):
        """Actualiza lista de lockers"""
        self.listbox_lockers.delete(0, tk.END)
        lockers = self.db.listar_lockers(ADMIN_CONFIG['total_lockers'])
        for l in lockers:
            estado = f"Locker {l['locker']}: {l['estado']}"
            if l['usuario']:
                estado += f" - {l['usuario']}"
            self.listbox_lockers.insert(tk.END, estado)
    
    def _guardar_usuario(self):
        """Crea nuevo administrador"""
        nombre = self.entry_usuario.get()
        contraseña = self.entry_pass.get()
        rol = 'administrador'
        
        if not nombre or not contraseña:
            messagebox.showwarning("Advertencia", "Completa usuario y contraseña")
            return
        
        try:
            self.db.guardar_usuario(nombre, contraseña, rol)
            messagebox.showinfo("Éxito", "Administrador creado")
            self.entry_usuario.delete(0, tk.END)
            self.entry_pass.delete(0, tk.END)
            self._refrescar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
    
    def _eliminar_usuario(self):
        """Elimina usuario seleccionado"""
        sel = self.listbox_usuarios.curselection()
        if not sel:
            messagebox.showwarning("Advertencia", "Selecciona un usuario")
            return
        
        texto = self.listbox_usuarios.get(sel[0])
        nombre = texto.split(' (')[0]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar {nombre}?"):
            try:
                self.db.eliminar_usuario(nombre)
                self._refrescar_usuarios()
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")
    
    def _liberar_locker_seleccionado(self):
        """Libera el locker seleccionado"""
        sel = self.listbox_lockers.curselection()
        if not sel:
            messagebox.showwarning("Advertencia", "Selecciona un locker")
            return
        
        texto = self.listbox_lockers.get(sel[0])
        locker_num = int(texto.split()[1].rstrip(':'))
        
        if messagebox.askyesno("Confirmar", f"¿Liberar Locker {locker_num}?"):
            try:
                self.db.liberar_locker(locker_num, ADMIN_CONFIG['total_lockers'])
                self._refrescar_lockers()
                messagebox.showinfo("Éxito", f"Locker {locker_num} liberado")
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")
    
    def _asignar_locker_manual(self):
        """Asigna un locker específico manualmente"""
        # Crear ventana para pedir locker y nombre
        dialog = tk.Toplevel(self)
        dialog.title("Asignar Locker")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORES['fondo'])
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Asignar un locker", style='Header.TLabel').pack(pady=(16, 12))
        
        frame = ttk.Frame(dialog, style='Card.TFrame')
        frame.pack(fill='both', expand=True, padx=20, pady=(0, 16))
        
        ttk.Label(frame, text="Locker (1-4):", style='Subtitle.TLabel').grid(row=0, column=0, sticky='w', padx=10, pady=8)
        entry_locker = ttk.Spinbox(frame, from_=1, to=ADMIN_CONFIG['total_lockers'], width=10, font=FUENTES['normal'])
        entry_locker.set(1)
        entry_locker.grid(row=0, column=1, sticky='w', padx=10, pady=8)
        
        ttk.Label(frame, text="Nombre: *OBLIGATORIO", style='Subtitle.TLabel').grid(row=1, column=0, sticky='w', padx=10, pady=8, columnspan=2)
        entry_nombre = ttk.Entry(frame, font=FUENTES['normal'])
        entry_nombre.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=8)
        
        frame.grid_columnconfigure(1, weight=1)
        
        result = {'ok': False}
        
        def confirmar():
            locker_num = int(entry_locker.get())
            nombre_usuario_custom = entry_nombre.get().strip()
            
            if not nombre_usuario_custom:
                messagebox.showwarning("Campo obligatorio", "Debes especificar un nombre para el usuario.", parent=dialog)
                return
            
            result['locker_num'] = locker_num
            result['nombre_custom'] = nombre_usuario_custom
            result['ok'] = True
            dialog.destroy()
        
        def cancelar():
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=12, sticky='ew')
        ttk.Button(btn_frame, text="OK", command=confirmar, style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=cancelar, style='Secondary.TButton').pack(side='left', padx=5)
        
        self.wait_window(dialog)
        
        if not result['ok']:
            return
        
        locker_num = result['locker_num']
        nombre_usuario_custom = result['nombre_custom']
        
        lockers = self.db.listar_lockers(ADMIN_CONFIG['total_lockers'])
        locker_info = lockers[locker_num - 1]
        
        if locker_info['estado'] == 'Ocupado':
            messagebox.showwarning("Locker ocupado", f"Locker {locker_num} ya está ocupado por {locker_info['usuario']}.")
            return
        
        nombre_usuario = nombre_usuario_custom
        
        try:
            if self.db.obtener_usuario_por_nombre(nombre_usuario):
                messagebox.showerror("Error", f"El usuario '{nombre_usuario}' ya existe.")
                return
            
            usuario_id = self.db.guardar_usuario(nombre_usuario, "1234", 'usuario')
            
            self._capturar_locker_manual(locker_num, nombre_usuario, usuario_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear usuario: {e}")
    
    def _capturar_locker_manual(self, locker_num, nombre_usuario, usuario_id):
        """Captura rostro para locker específico"""
        captura_win = tk.Toplevel(self)
        captura_win.title(f"Capturar rostro - Locker {locker_num}")
        captura_win.geometry("750x420")
        captura_win.configure(bg=COLORES['fondo'])
        
        header = ttk.Frame(captura_win, style='Card.TFrame')
        header.pack(fill='x', padx=10, pady=(10, 5))
        title_box = ttk.Frame(header, style='Card.TFrame')
        title_box.pack(side='left', fill='x', expand=True, padx=10, pady=10)
        ttk.Label(title_box, text=f"Capturando rostro para Locker {locker_num}", style='Header.TLabel').pack(anchor='w')
        ttk.Label(title_box, text=f"Usuario: {nombre_usuario}", style='Subtitle.TLabel').pack(anchor='w', pady=(4, 0))
        ttk.Button(header, text="Cerrar", command=captura_win.destroy, style='Secondary.TButton').pack(side='right', padx=10, pady=10)
        
        video_frame = ttk.Frame(captura_win, style='Card.TFrame')
        video_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        label_video = ttk.Label(video_frame, background=COLORES['info_bg'], relief='flat')
        label_video.pack(fill='both', expand=True, padx=12, pady=12)
        
        captura_disponible = [False]
        frame_actual = [None]
        
        status_label = ttk.Label(captura_win, text="Cargando cámara...", style='Info.TLabel', justify='center', wraplength=700)
        status_label.pack(fill='x', padx=20, pady=10)
        
        def actualizar_video():
            try:
                if not captura_win.winfo_exists():
                    return
                    
                ret, frame = self.camera.leer_frame()
                if ret and frame is not None:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    rostros = self.face_recognizer.detectar_rostros(frame)
                    for (top, right, bottom, left) in rostros:
                        cv2.rectangle(frame_rgb, (left, top), (right, bottom), (0, 255, 0), 3)
                    
                    captura_disponible[0] = len(rostros) > 0
                    
                    if captura_disponible[0]:
                        status_label.config(text="✓ Rostro detectado. Presiona 'Capturar rostro' cuando estés listo.")
                    else:
                        status_label.config(text="⊙ No hay rostro detectado. Acércate más a la cámara.")
                    
                    imagen = Image.fromarray(frame_rgb)
                    imagen.thumbnail((624, 468), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image=imagen)
                    label_video.config(image=photo)
                    label_video.image = photo
                    
                    frame_actual[0] = frame
            except Exception as e:
                print(f"[ERROR] Captura manual: {e}")
                status_label.config(text="Error al procesar la cámara")
            
            if captura_win.winfo_exists():
                captura_win.after(100, actualizar_video)
        
        def capturar():
            if not captura_disponible[0] or frame_actual[0] is None:
                messagebox.showwarning("Atención", "No se detectó un rostro claro. Ajusta tu posición e inténtalo otra vez.", parent=captura_win)
                return
            
            try:
                self.face_recognizer.asociar_rostro(nombre_usuario, frame_actual[0])
                
                ret, buffer = cv2.imencode('.jpg', frame_actual[0])
                if ret:
                    self.db.guardar_imagen(usuario_id, buffer.tobytes())
                
                messagebox.showinfo("¡Listo!", f"Locker {locker_num} está configurado y listo para usar.", parent=captura_win)
                self._refrescar_lockers()
                captura_win.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=captura_win)
        
        btn_frame = ttk.Frame(captura_win, style='Card.TFrame')
        btn_frame.pack(fill='x', padx=10, pady=(0, 12))
        ttk.Button(btn_frame, text="Capturar rostro", command=capturar, style='Primary.TButton').pack(side='left', fill='x', expand=True, padx=6)
        ttk.Button(btn_frame, text="Cancelar", command=captura_win.destroy, style='Secondary.TButton').pack(side='left', fill='x', expand=True, padx=6)
        
        actualizar_video()