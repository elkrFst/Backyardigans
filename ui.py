"""Interfaz gráfica (Tkinter) - Todas las pantallas y widgets"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog
import cv2
from PIL import Image, ImageTk
import threading
from datetime import datetime
import time
import pyttsx3
import os
import queue

from config import COLORES, FUENTES, ADMIN_CONFIG, WINDOW_SIZE, WINDOW_FULLSCREEN
from core import Camera, FaceRecognizer, LockerController

# ============================================================================
# ENGINE DE VOZ GLOBAL (para evitar memory leaks de pyttsx3)
# ============================================================================
_tts_engine = None
_tts_lock = threading.Lock()

def _inicializar_tts():
    """Inicializa el engine de texto a voz global"""
    global _tts_engine
    try:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty('rate', 150)
        _tts_engine.setProperty('volume', 1.0)
        print("[TTS] OK Engine de voz inicializado globalmente")
    except Exception as e:
        print(f"[TTS] ERROR inicializando engine: {e}")
        _tts_engine = None

# Inicializar al importar
_inicializar_tts()


# ============================================================================
# PANTALLAS PRINCIPALES
# ============================================================================
class UIApp:
    """Aplicación principal - Gestiona todas las pantallas"""
    
    def __init__(self, root, db, face_recognizer):
        self.root = root
        self.db = db
        self.face_recognizer = face_recognizer
        self.camera = None
        self.locker_controller = LockerController()  # Inicializar controlador de lockers GPIO
        self.encodings_conocidos = []
        self.nombres_conocidos = []
        self.modo = None  # 'abrir' o 'registrar'
        self.preview_pausado = False  # Control para pausar preview
        self.frame_count = 0  # Contador para procesar solo cada X frames
        self.detect_interval = 5  # Procesar detección cada 5 frames
        
        # Lock para síntesis de voz (una sola voz a la vez)
        self.audio_lock = threading.Lock()
        
        # Control de distancia
        self.ultima_advertencia_distancia = 0  # Timestamp de la última advertencia
        self.advertencia_activa = False

        # Guía de voz en menú principal cuando alguien se acerca
        self.ultima_indicacion_menu = 0
        self.intervalo_indicacion_menu = 120
        
        # Configurar ventana
        self.root.title("Sistema de Lockers - Reconocimiento Facial")
        self.root.geometry(WINDOW_SIZE)
        self.root.bind_all('<Escape>', self._salir_pantalla_completa)
        self.root.configure(bg=COLORES["fondo"])
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

        # Estilos
        self._configurar_estilos()

        self.mostrar_menu_principal()
    
    def _configurar_estilos(self):
        """Configura estilos ttk"""
        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
        except:
            pass

        style.configure('TFrame', background=COLORES['fondo'])
        style.configure('App.TFrame', background=COLORES['fondo'])
        style.configure('TLabel', background=COLORES['fondo'], foreground=COLORES['texto'], font=FUENTES['normal'])
        style.configure('Header.TLabel', background=COLORES['panel'], foreground=COLORES['texto'], font=FUENTES['titulo'])
        style.configure('Subtitle.TLabel', background=COLORES['panel'], foreground=COLORES['subtexto'], font=FUENTES['subtitulo'])
        style.configure('Card.TFrame', background=COLORES['panel'], borderwidth=1, relief='solid')
        style.configure('InnerCard.TFrame', background=COLORES['panel_sec'], borderwidth=0, relief='flat')
        style.configure('Video.TFrame', background=COLORES['video_bg'], borderwidth=2, relief='solid')
        style.configure('Info.TLabel', background=COLORES['panel_sec'], foreground=COLORES['texto'], font=FUENTES['subtitulo'], padding=8)
        style.configure('Status.TLabel', background=COLORES['panel_sec'], foreground=COLORES['texto'], font=FUENTES['subtitulo'], padding=6)
        style.configure('Section.TLabel', background=COLORES['panel'], foreground=COLORES['texto'], font=FUENTES['resultado'])
        style.configure('Badge.TLabel', background=COLORES['exito'], foreground=COLORES['texto'], font=FUENTES['boton_pequeno'], padding=[8, 3])
        style.configure('WarningBadge.TLabel', background=COLORES['alerta'], foreground=COLORES['texto'], font=FUENTES['boton_pequeno'], padding=[8, 3])
        style.configure('Video.TLabel', background=COLORES['video_bg'], foreground=COLORES['muted'], font=FUENTES['subtitulo'], padding=10)

        style.configure('Primary.TButton', font=FUENTES['boton'], padding=[12, 10], background=COLORES['boton_principal'], foreground=COLORES['texto'], borderwidth=0)
        style.map('Primary.TButton', background=[('active', COLORES['boton_principal_hover']), ('pressed', COLORES['boton_principal_hover'])])

        style.configure('Secondary.TButton', font=FUENTES['boton'], padding=[12, 10], background=COLORES['boton_secundario'], foreground=COLORES['texto'], borderwidth=0)
        style.map('Secondary.TButton', background=[('active', COLORES['boton_secundario_hover']), ('pressed', COLORES['boton_secundario_hover'])])

        style.configure('Small.TButton', font=FUENTES['boton_pequeno'], padding=[10, 7], background=COLORES['panel_suave'], foreground=COLORES['texto'], borderwidth=0)
        style.map('Small.TButton', background=[('active', COLORES['boton_principal'])])
        
        style.configure('TEntry', fieldbackground=COLORES['info_bg'], foreground=COLORES['texto'], insertcolor=COLORES['texto'], borderwidth=1)
        style.configure('TSpinbox', fieldbackground=COLORES['info_bg'], foreground=COLORES['texto'], arrowsize=12)
        style.configure('TNotebook', background=COLORES['fondo'], borderwidth=0)
        style.configure('TNotebook.Tab', background=COLORES['panel'], foreground=COLORES['texto'], font=FUENTES['boton_pequeno'], padding=[12, 7])
        style.map('TNotebook.Tab', background=[('selected', COLORES['boton_principal'])], foreground=[('selected', COLORES['texto'])])

    def _salir_pantalla_completa(self, event=None):
        """Quita pantalla completa de la ventana activa y de la ventana principal."""
        try:
            if event is not None:
                event.widget.winfo_toplevel().attributes('-fullscreen', False)
            self.root.attributes('-fullscreen', False)
            for ventana in self.root.winfo_children():
                if isinstance(ventana, tk.Toplevel) and ventana.winfo_exists():
                    ventana.attributes('-fullscreen', False)
        except tk.TclError:
            pass

    def _preparar_ventana_fullscreen(self, ventana):
        """Aplica pantalla completa y permite salir con Esc."""
        ventana.bind('<Escape>', lambda event: ventana.attributes('-fullscreen', False))
        if WINDOW_FULLSCREEN:
            ventana.after(100, lambda: ventana.winfo_exists() and ventana.attributes('-fullscreen', True))
    
    def _hablar(self, texto):
        """Pronuncia un texto usando síntesis de voz global en un hilo separado"""
        def hablar_thread():
            global _tts_engine
            if _tts_engine is None:
                print("[TTS] ADVERTENCIA Engine no inicializado")
                return
            
            try:
                with _tts_lock:
                    _tts_engine.say(texto)
                    _tts_engine.runAndWait()
            except Exception as e:
                print(f"[TTS] Error al hablar: {e}")
        
        # Ejecutar en hilo separado para no bloquear la UI
        hilo = threading.Thread(target=hablar_thread, daemon=True)
        hilo.start()
    
    def _emitir_pitido(self, frecuencia=800, duracion=200):
        """Emite un pitido en un hilo separado para no bloquear la UI."""
        def beep_thread():
            try:
                # Usar enfoque multiplataforma: bell character para Linux/Mac, paplay para audio si disponible
                if os.name == 'nt':  # Windows
                    import winsound
                    winsound.Beep(frecuencia, duracion)
                else:  # Linux/Mac
                    # Usar bell character (simple)
                    for _ in range(1):
                        print('\a', end='', flush=True)
            except Exception as e:
                print(f"[TTS] Error en pitido: {e}")
        threading.Thread(target=beep_thread, daemon=True).start()
    
    def _advertir_distancia(self):
        """Advierte al usuario cuando está demasiado cerca de la cámara."""
        tiempo_actual = time.time()
        if tiempo_actual - self.ultima_advertencia_distancia > 2:
            self._hablar("Aléjate de la cámara")
            self._emitir_pitido()
            self.ultima_advertencia_distancia = tiempo_actual

    def _indicar_opciones_menu_si_corresponde(self):
        """Guía al usuario en el menú principal como máximo una vez cada 2 minutos."""
        tiempo_actual = time.time()
        if tiempo_actual - self.ultima_indicacion_menu < self.intervalo_indicacion_menu:
            return

        self.ultima_indicacion_menu = tiempo_actual
        self._hablar("Presione registrar locker para empezar. Presione abrir locker si ya tiene uno registrado.")
    
    def _esta_demasiado_cerca(self, frame, rostros):
        """Calcula si el rostro está demasiado cerca usando el tamaño del bounding box."""
        if not rostros or frame is None:
            return False
        alto, ancho = frame.shape[:2]
        for (top, right, bottom, left) in rostros:
            altura_rostro = bottom - top
            ancho_rostro = right - left
            area_rostro = altura_rostro * ancho_rostro
            area_frame = alto * ancho
            if altura_rostro > alto * 0.55 or ancho_rostro > ancho * 0.55 or area_rostro > area_frame * 0.24:
                return True
        return False

    def _obtener_locker_de_usuario(self, nombre_usuario):
        """Devuelve el número de locker asociado a un usuario registrado."""
        nombre_limpio = nombre_usuario.replace('.jpg', '').replace('.png', '')
        if nombre_limpio.startswith('locker'):
            try:
                return int(nombre_limpio.replace('locker', '', 1))
            except ValueError:
                pass

        try:
            lockers = self.db.listar_lockers(ADMIN_CONFIG['total_lockers'])
            for locker in lockers:
                if locker.get('usuario') == nombre_limpio:
                    return locker.get('locker')
        except Exception as e:
            print(f"[ERROR] Buscando locker para {nombre_limpio}: {e}")

        return None
    
    def limpiar_frame(self):
        """Elimina todos los widgets"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def mostrar_menu_principal(self):
        """Pantalla principal con video y opciones"""
        print("[UI] Iniciando menú principal...")
        self.limpiar_frame()
        self.modo = None
        
        try:
            shell = ttk.Frame(self.root, style='App.TFrame')
            shell.pack(fill='both', expand=True, padx=14, pady=10)

            header = ttk.Frame(shell, style='Card.TFrame')
            header.pack(fill='x', pady=(0, 10))
            
            title_frame = ttk.Frame(header, style='Card.TFrame')
            title_frame.pack(side='left', fill='x', expand=True, padx=14, pady=10)
            ttk.Label(title_frame, text="Smart Locker", style='Header.TLabel').pack(anchor='w')
            ttk.Label(title_frame, text="Acceso seguro mediante reconocimiento facial", style='Subtitle.TLabel').pack(anchor='w', pady=(2, 0))
            
            action_frame = ttk.Frame(header, style='Card.TFrame')
            action_frame.pack(side='right', padx=14, pady=10)
            ttk.Button(action_frame, text="Panel administrador", command=lambda: (self._hablar('Panel administrador'), self.abrir_admin()), style='Small.TButton').pack()
            
            contenido = ttk.Frame(shell, style='App.TFrame')
            contenido.pack(fill='both', expand=True)
            
            video_frame = ttk.Frame(contenido, style='Card.TFrame')
            video_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
            ttk.Label(video_frame, text="Vista en vivo", style='Section.TLabel').pack(anchor='w', padx=12, pady=(10, 4))
            ttk.Label(video_frame, text="Colocate frente a la camara para continuar", style='Subtitle.TLabel').pack(anchor='w', padx=12, pady=(0, 8))
            video_card = ttk.Frame(video_frame, style='Video.TFrame')
            video_card.pack(fill='both', expand=True, padx=12, pady=(0, 12))
            self.label_video = ttk.Label(video_card, text="Esperando senal de camara...", style='Video.TLabel', anchor='center', justify='center')
            self.label_video.pack(fill='both', expand=True, padx=8, pady=8)
            
            info_frame = ttk.Frame(contenido, style='Card.TFrame')
            info_frame.pack(side='right', fill='y', ipadx=8, ipady=6)
            ttk.Label(info_frame, text="Estado del sistema", style='Section.TLabel').pack(anchor='w', padx=12, pady=(10, 6))
            
            self.lbl_estado = ttk.Label(info_frame, text="Elige una opción para comenzar.", style='Info.TLabel', justify='left', wraplength=240)
            self.lbl_estado.config(text="Sistema listo. Elige una opcion para comenzar.", wraplength=250)
            self.lbl_estado.pack(fill='x', padx=12, pady=(0, 8))
            
            status_card = ttk.Frame(info_frame, style='InnerCard.TFrame')
            status_card.pack(fill='x', padx=12, pady=(0, 8))
            ttk.Label(status_card, text="Reconocimiento facial", style='Status.TLabel').pack(fill='x', padx=8, pady=(8, 2))
            ttk.Label(status_card, text="Listo", style='Badge.TLabel').pack(anchor='w', padx=8, pady=(0, 6))
            ttk.Label(status_card, text="Rostro centrado", style='Status.TLabel').pack(fill='x', padx=8, pady=(0, 2))
            ttk.Label(status_card, text="Verificando con camara", style='WarningBadge.TLabel').pack(anchor='w', padx=8, pady=(0, 6))
            ttk.Label(status_card, text="Iluminacion adecuada", style='Status.TLabel').pack(fill='x', padx=8, pady=(0, 2))
            ttk.Label(status_card, text="Buena luz recomendada", style='Badge.TLabel').pack(anchor='w', padx=8, pady=(0, 8))

            self.lbl_resumen = ttk.Label(info_frame, text="Cargando estado de lockers...", style='Status.TLabel', justify='left', wraplength=250)
            self.lbl_resumen.pack(fill='x', padx=12, pady=(0, 8))
            
            botones_frame = ttk.Frame(info_frame, style='Card.TFrame')
            botones_frame.pack(fill='x', padx=12, pady=(0, 8))
            ttk.Button(botones_frame, text="Abrir mi locker", command=lambda: (self._hablar('Abrir mi locker'), self.iniciar_acceso()), style='Primary.TButton').pack(fill='x', pady=(0, 6))
            ttk.Button(botones_frame, text="Registrar rostro", command=lambda: (self._hablar('Registrar rostro'), self.iniciar_registro()), style='Secondary.TButton').pack(fill='x')
            
            steps_card = ttk.Frame(info_frame, style='InnerCard.TFrame')
            steps_card.pack(fill='x', padx=12, pady=(0, 10))
            ttk.Label(steps_card, text="Pasos de uso", style='Status.TLabel').pack(anchor='w', padx=8, pady=(8, 2))
            ttk.Label(steps_card, text="1. Mira a la camara\n2. Registra tu rostro si es tu primera vez\n3. Abre tu locker si ya estas registrado", style='Subtitle.TLabel', wraplength=250, justify='left').pack(fill='x', padx=8, pady=(0, 8))
            
            self._actualizar_resumen_lockers()
            self.root.update_idletasks()
            if WINDOW_FULLSCREEN:
                self.root.attributes('-fullscreen', True)
                self.root.update()
            self._iniciar_preview_camara()
            print("[UI] OK Menu principal listo")
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
            print(f"[UI] OK {len(self.nombres_conocidos)} rostros cargados")
            
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
                        if rostros:
                            self._indicar_opciones_menu_si_corresponde()
                        for (top, right, bottom, left) in rostros:
                            cv2.rectangle(frame_rgb, (left, top), (right, bottom), (0, 255, 0), 2)
                    except:
                        pass  # Si falla, simplemente mostrar frame
                
                # Redimensionar imagen UNA SOLA VEZ
                imagen = Image.fromarray(frame_rgb)
                imagen.thumbnail((520, 300), Image.Resampling.LANCZOS)
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
        
        # Cargar rostros conocidos
        self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()
        
        if not self.encodings_conocidos:
            messagebox.showwarning("Sin rostros registrados", "No hay rostros registrados. Regístrate primero.")
            self.mostrar_menu_principal()
            return
        
        if not self.camera:
            self.camera = Camera(0)
            self.camera.iniciar()
        
        shell = ttk.Frame(self.root, style='App.TFrame')
        shell.pack(fill='both', expand=True, padx=14, pady=10)

        header = ttk.Frame(shell, style='Card.TFrame')
        header.pack(fill='x', pady=(0, 10))
        ttk.Label(header, text="Abrir mi locker", style='Header.TLabel').pack(side='left', padx=14, pady=10)
        ttk.Button(header, text="Volver", command=lambda: (self._hablar('Volver'), self.mostrar_menu_principal()), style='Secondary.TButton').pack(side='right', padx=14, pady=10)
        
        self.lbl_estado = ttk.Label(self.root, text="Acércate a la cámara. Tu locker se abrirá cuando te reconozca.", style='Info.TLabel', justify='center', wraplength=620)
        self.lbl_estado.config(text="Acercate a la camara. Tu locker se abrira cuando te reconozca.", wraplength=680)
        self.lbl_estado.pack(fill='x', pady=(0, 10))
        
        # Contenedor principal: video a la izquierda + botones a la derecha
        contenedor = ttk.Frame(shell, style='App.TFrame')
        contenedor.pack(fill='both', expand=True)
        
        # Video a la izquierda
        video_frame = ttk.Frame(contenedor, style='Video.TFrame')
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.label_video = ttk.Label(video_frame, text="Buscando senal de camara...", style='Video.TLabel', anchor='center')
        self.label_video.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Botones a la derecha (vertical)
        botones = ttk.Frame(contenedor, style='Card.TFrame')
        botones.pack(side='right', fill='y', ipadx=8, ipady=8)
        ttk.Label(botones, text="Verificacion", style='Section.TLabel').pack(anchor='w', padx=10, pady=(8, 4))
        ttk.Label(botones, text="Mantente centrado y evita sombras fuertes.", style='Subtitle.TLabel', wraplength=220, justify='left').pack(fill='x', padx=10, pady=(0, 10))
        ttk.Button(botones, text="Cancelar", command=lambda: (self._hablar('Cancelar'), self.mostrar_menu_principal()), style='Secondary.TButton').pack(fill='x', padx=10, pady=4)
        
        self._reconocer_acceso()
    
    def _reconocer_acceso(self):
        """Loop de reconocimiento facial para acceso - OPTIMIZADO"""
        if self.modo != 'abrir':
            return
        
        try:
            ret, frame = self.camera.leer_frame()
            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detectar rostros para verificar distancia
                rostros = self.face_recognizer.detectar_rostros(frame)
                
                # Verificar distancia usando la proporción del rostro
                distancia_ok = not self._esta_demasiado_cerca(frame, rostros)
                if not distancia_ok:
                    self._advertir_distancia()
                    self.advertencia_activa = True
                    self.lbl_estado.config(text="Advertencia: Alejate mas de la camara, estas muy cerca.")
                elif self.advertencia_activa:
                    self.advertencia_activa = False
                    self.ultima_advertencia_distancia = 0
                
                # Intentar reconocer solo si la distancia es correcta
                if distancia_ok:
                    nombre = self.face_recognizer.reconocer(frame, self.encodings_conocidos, self.nombres_conocidos)
                    
                    if nombre:
                        nombre_limpio = nombre.replace('.jpg', '').replace('.png', '')
                        usuario = self.db.obtener_usuario_por_nombre(nombre_limpio)
                        
                        if usuario:
                            locker_num = self._obtener_locker_de_usuario(nombre_limpio)
                            if locker_num is None:
                                self.lbl_estado.config(text="Rostro reconocido, pero no se encontró un locker asignado.")
                            else:
                                # ========== ACTIVAR RELÉ DEL LOCKER ==========
                                self.locker_controller.activar_locker(locker_num)
                                # ============================================

                                self.lbl_estado.config(text=f"Perfecto. Se encontro tu locker {locker_num}.")
                                self._hablar(f"Locker {locker_num} abierto")
                                messagebox.showinfo("Acceso concedido", f"Locker {locker_num} abierto.")
                                self.mostrar_menu_principal()
                                return
                    else:
                        self.lbl_estado.config(text="Buscando rostro... mantén tu cara frente a la cámara.")
                
                imagen = Image.fromarray(frame_rgb)
                imagen.thumbnail((560, 280), Image.Resampling.LANCZOS)
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
        
        # NO guardar el usuario aquí - solo mostrar pantalla de captura
        # El usuario se guardará cuando se capture exitosamente el rostro
        
        self.modo = 'registrar'
        self.limpiar_frame()
        
        shell = ttk.Frame(self.root, style='App.TFrame')
        shell.pack(fill='both', expand=True, padx=14, pady=10)

        header = ttk.Frame(shell, style='Card.TFrame')
        header.pack(fill='x', pady=(0, 10))
        ttk.Label(header, text="Registrar rostro", style='Header.TLabel').pack(side='left', padx=14, pady=10)
        ttk.Button(header, text="Volver", command=lambda: (self._hablar('Volver'), self.mostrar_menu_principal()), style='Secondary.TButton').pack(side='right', padx=14, pady=10)
        
        self.lbl_estado = ttk.Label(self.root, text=f"Locker {locker_asignado}: mantén la cara centrada.", style='Info.TLabel', justify='center', wraplength=620)
        self.lbl_estado.config(text=f"Locker {locker_asignado}: centra tu rostro y manten buena iluminacion.", wraplength=680)
        self.lbl_estado.pack(fill='x', pady=(0, 10))
        
        # Contenedor principal: video a la izquierda + botones a la derecha
        contenedor = ttk.Frame(shell, style='App.TFrame')
        contenedor.pack(fill='both', expand=True)
        
        # Video a la izquierda
        video_frame = ttk.Frame(contenedor, style='Video.TFrame')
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.label_video = ttk.Label(video_frame, text="Preparando captura...", style='Video.TLabel', anchor='center')
        self.label_video.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Botones a la derecha (vertical)
        botones = ttk.Frame(contenedor, style='Card.TFrame')
        botones.pack(side='right', fill='y', ipadx=8, ipady=8)
        ttk.Label(botones, text="Nuevo usuario", style='Section.TLabel').pack(anchor='w', padx=10, pady=(8, 4))
        ttk.Label(botones, text="Cuando el sistema detecte tu rostro, presiona capturar.", style='Subtitle.TLabel', wraplength=220, justify='left').pack(fill='x', padx=10, pady=(0, 10))
        ttk.Button(botones, text="Capturar rostro", command=lambda: (self._hablar('Capturar rostro'), self._capturar_registro()), style='Primary.TButton').pack(fill='x', padx=10, pady=(0, 6))
        ttk.Button(botones, text="Cancelar", command=lambda: (self._hablar('Cancelar'), self.mostrar_menu_principal()), style='Secondary.TButton').pack(fill='x', padx=10, pady=4)
        
        self.captura_disponible = False
        self.nombre_registro = nombre_usuario
        self.locker_asignado = locker_asignado
        self._mostrar_registro(nombre_usuario, locker_asignado)
    
    def _mostrar_registro(self, nombre, locker_asignado):
        """Muestra video para captura de registro - OPTIMIZADO"""
        if self.modo != 'registrar':
            return
        
        try:
            ret, frame = self.camera.leer_frame()
            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detectar rostros
                rostros = self.face_recognizer.detectar_rostros(frame)
                for (top, right, bottom, left) in rostros:
                    cv2.rectangle(frame_rgb, (left, top), (right, bottom), (0, 255, 0), 3)
                
                # Verificar distancia
                self.captura_disponible = False
                if self._esta_demasiado_cerca(frame, rostros):
                    self._advertir_distancia()
                    self.advertencia_activa = True
                    self.lbl_estado.config(text="Advertencia: Alejate mas de la camara, estas muy cerca.")
                elif rostros:
                    self.captura_disponible = True
                    if self.advertencia_activa:
                        self.advertencia_activa = False
                        self.ultima_advertencia_distancia = 0
                        self.lbl_estado.config(text="Distancia perfecta. Presiona Capturar rostro cuando estes listo.")
                    else:
                        self.lbl_estado.config(text="Rostro detectado. Presiona Capturar rostro cuando estés listo.")
                else:
                    self.captura_disponible = False
                    self.lbl_estado.config(text="No detecto un rostro claro. Ajusta tu posición y prueba otra vez.")
                
                imagen = Image.fromarray(frame_rgb)
                imagen.thumbnail((560, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image=imagen)
                self.label_video.config(image=photo)
                self.label_video.image = photo
                
                self.frame_actual_registro = frame
        except Exception as e:
            print(f"[ERROR] Registro: {e}")
        
        # Intervalo de 100ms
        self.root.after(100, lambda: self._mostrar_registro(nombre, locker_asignado))
    
    def _capturar_registro(self):
        """Captura y guarda el rostro"""
        if not hasattr(self, 'frame_actual_registro') or not self.captura_disponible:
            messagebox.showwarning("Atención", "No se detectó un rostro claro. Ajusta tu posición e inténtalo otra vez.")
            return
        
        try:
            # Asociar rostro antes de crear el usuario para evitar registros incompletos.
            encoding = self.face_recognizer.asociar_rostro(self.nombre_registro, self.frame_actual_registro)
            if encoding is None:
                messagebox.showwarning("Atención", "No se pudo extraer el rostro. Ajusta tu posición e inténtalo otra vez.")
                return

            # Ahora sí guardar el usuario en BD (solo cuando se captura con éxito)
            usuario_id = self.db.guardar_usuario(self.nombre_registro, "1234", 'usuario')
            if not usuario_id:
                messagebox.showerror("Error", "No se pudo guardar el usuario en la base de datos.")
                return
            
            # Guardar imagen en BD
            ret, buffer = cv2.imencode('.jpg', self.frame_actual_registro)
            if ret:
                self.db.guardar_imagen(usuario_id, buffer.tobytes())
            self.locker_controller.activar_locker(self.locker_asignado)

            messagebox.showinfo("Listo", f"Locker {self.locker_asignado} esta registrado, abierto y listo para usar.")
            
            # Recargar rostros conocidos
            self.encodings_conocidos, self.nombres_conocidos = self.face_recognizer.cargar_todos()
            
            self.mostrar_menu_principal()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")
    
    def abrir_admin(self):
        """Abre panel de administración con login personalizado"""
        login_win = tk.Toplevel(self.root)
        login_win.title("Acceso administrador")
        login_win.geometry("420x230")
        login_win.resizable(False, False)
        login_win.configure(bg=COLORES['fondo'])
        self._preparar_ventana_fullscreen(login_win)

        login_win.transient(self.root)
        login_win.grab_set()

        ttk.Label(login_win, text="Panel administrador", style='Header.TLabel').pack(pady=(12, 2))
        ttk.Label(login_win, text="Acceso restringido para gestion de usuarios y lockers.", style='Subtitle.TLabel', wraplength=320, justify='center').pack(padx=12, pady=(0, 8))

        frame = ttk.Frame(login_win, style='Card.TFrame')
        frame.pack(fill='both', expand=True, padx=18, pady=(0, 12))

        # Campo usuario
        ttk.Label(frame, text="Usuario:", style='Subtitle.TLabel').grid(row=0, column=0, sticky='w', padx=10, pady=6)
        entry_usuario = ttk.Entry(frame, font=FUENTES['normal'])
        entry_usuario.grid(row=0, column=1, sticky='ew', padx=10, pady=6)
        entry_usuario.focus()  # Focus en usuario

        # Campo contraseña
        ttk.Label(frame, text="Contraseña:").grid(row=1, column=0, sticky='w', padx=8, pady=4)
        entry_pass = ttk.Entry(frame, font=FUENTES['normal'], show='*')
        entry_pass.grid(row=1, column=1, sticky='ew', padx=10, pady=6)

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
                AdminWindow(self.root, self.db, self.camera, self.face_recognizer, self.locker_controller)

            except Exception as e:
                messagebox.showerror("Error", f"Error de conexión: {e}", parent=login_win)

        def cancelar():
            login_win.destroy()

        # Botones
        btn_frame = ttk.Frame(frame, style='Card.TFrame')
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)

        ttk.Button(btn_frame, text="Ingresar", command=lambda: (self._hablar('Ingresar'), login()), style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=lambda: (self._hablar('Cancelar'), cancelar()), style='Secondary.TButton').pack(side='left', padx=5)

        # Bind Enter para login
        entry_pass.bind('<Return>', lambda e: login())

        # Esperar a que se cierre la ventana
        self.root.wait_window(login_win)
    
    def cerrar(self):
        """Cierra la aplicación"""
        if self.camera:
            self.camera.detener()
        self.locker_controller.cerrar()  # Limpiar GPIO
        self.db.cerrar()
        self.root.destroy()
    
    def salir(self):
        """Alias para cerrar la aplicación"""
        self.cerrar()


# ============================================================================
# VENTANA DE ADMINISTRACIÓN
# ============================================================================
class AdminWindow(tk.Toplevel):
    """Panel de administración de usuarios"""
    
    def __init__(self, parent, db, camera, face_recognizer, locker_controller=None):
        super().__init__(parent)
        self.title("Panel de Administración")
        self.geometry(WINDOW_SIZE)
        self.configure(bg=COLORES["fondo"])
        self._preparar_ventana_fullscreen(self)
        self.db = db
        self.camera = camera
        self.face_recognizer = face_recognizer
        self.locker_controller = locker_controller
        
        header = ttk.Frame(self, style='Card.TFrame')
        header.pack(fill='x', padx=4, pady=4)
        title_box = ttk.Frame(header, style='Card.TFrame')
        title_box.pack(side='left', fill='x', expand=True, padx=5, pady=4)
        ttk.Label(title_box, text="Panel de administración", style='Header.TLabel').pack(anchor='w')
        ttk.Label(title_box, text="Usuarios y lockers.", style='Subtitle.TLabel').pack(anchor='w', pady=(1, 0))
        ttk.Button(header, text="Cerrar", command=lambda: (self._hablar_admin('Cerrar'), self.destroy()), style='Secondary.TButton').pack(side='right', padx=5, pady=4)
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Pestaña: Usuarios
        usuarios_frame = ttk.Frame(notebook)
        notebook.add(usuarios_frame, text="Usuarios")
        self._crear_tab_usuarios(usuarios_frame)
        
        # Pestaña: Lockers
        lockers_frame = ttk.Frame(notebook)
        notebook.add(lockers_frame, text="Lockers")
        self._crear_tab_lockers(lockers_frame)
    
    def _hablar_admin(self, texto):
        """Pronuncia un texto usando síntesis de voz (versión para AdminWindow)"""
        def hablar_thread():
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.setProperty('volume', 1.0)
                engine.say(texto)
                engine.runAndWait()
                del engine
            except Exception as e:
                print(f"[TTS] Error al hablar: {e}")
        
        # Ejecutar en hilo separado para no bloquear la UI
        hilo = threading.Thread(target=hablar_thread, daemon=True)
        hilo.start()

    def _preparar_ventana_fullscreen(self, ventana):
        """Aplica pantalla completa y permite salir con Esc."""
        ventana.bind('<Escape>', lambda event: ventana.attributes('-fullscreen', False))
        if WINDOW_FULLSCREEN:
            ventana.after(100, lambda: ventana.winfo_exists() and ventana.attributes('-fullscreen', True))

    def _esta_demasiado_cerca(self, frame, rostros):
        """Calcula si el rostro está demasiado cerca usando el tamaño del bounding box."""
        if not rostros or frame is None:
            return False
        alto, ancho = frame.shape[:2]
        for (top, right, bottom, left) in rostros:
            altura_rostro = bottom - top
            ancho_rostro = right - left
            area_rostro = altura_rostro * ancho_rostro
            area_frame = alto * ancho
            if altura_rostro > alto * 0.55 or ancho_rostro > ancho * 0.55 or area_rostro > area_frame * 0.24:
                return True
        return False
    
    def _crear_tab_usuarios(self, parent):
        """Crea la pestaña de gestión de usuarios"""
        list_frame = ttk.Frame(parent, style='Card.TFrame')
        list_frame.pack(side='left', fill='both', expand=True, padx=4, pady=4)
        
        ttk.Label(list_frame, text="Usuarios registrados", style='Section.TLabel').pack(anchor='w', pady=(0, 2), padx=2)
        
        self.listbox_usuarios = tk.Listbox(
            list_frame,
            font=FUENTES['normal'],
            bd=0,
            highlightthickness=1,
            relief='solid',
            bg=COLORES['info_bg'],
            fg=COLORES['texto'],
            selectbackground=COLORES['boton_principal'],
            selectforeground=COLORES['texto'],
            highlightbackground=COLORES['borde']
        )
        self.listbox_usuarios.pack(fill='both', expand=True, padx=2, pady=1)
        
        btn_frame = ttk.Frame(list_frame, style='Card.TFrame')
        btn_frame.pack(fill='x', pady=2, padx=2)
        ttk.Button(btn_frame, text="Refrescar", command=lambda: (self._hablar_admin('Refrescar'), self._refrescar_usuarios()), style='Small.TButton').pack(side='left', padx=1)
        ttk.Button(btn_frame, text="Eliminar", command=lambda: (self._hablar_admin('Eliminar'), self._eliminar_usuario()), style='Secondary.TButton').pack(side='left', padx=1)
        
        form_frame = ttk.LabelFrame(parent, text="Agregar administrador", style='Card.TFrame')
        form_frame.pack(side='right', fill='both', expand=True, padx=4, pady=4)
        
        ttk.Label(form_frame, text="Usuario:", style='Subtitle.TLabel').grid(row=0, column=0, sticky='w', padx=4, pady=3)
        self.entry_usuario = ttk.Entry(form_frame, font=FUENTES['normal'])
        self.entry_usuario.grid(row=0, column=1, sticky='ew', padx=4, pady=3)
        
        ttk.Label(form_frame, text="Contraseña:", style='Subtitle.TLabel').grid(row=1, column=0, sticky='w', padx=4, pady=3)
        self.entry_pass = ttk.Entry(form_frame, show='*', font=FUENTES['normal'])
        self.entry_pass.grid(row=1, column=1, sticky='ew', padx=4, pady=3)
        
        ttk.Label(form_frame, text="Rol:", style='Subtitle.TLabel').grid(row=2, column=0, sticky='w', padx=4, pady=3)
        rol_label = ttk.Label(form_frame, text="administrador", style='Section.TLabel')
        rol_label.grid(row=2, column=1, sticky='w', padx=4, pady=3)
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Button(form_frame, text="Guardar administrador", command=lambda: (self._hablar_admin('Guardar administrador'), self._guardar_usuario()), style='Primary.TButton').grid(row=3, column=0, columnspan=2, sticky='ew', padx=4, pady=4)
        
        self._refrescar_usuarios()
    
    def _crear_tab_lockers(self, parent):
        """Crea la pestaña de gestión de lockers"""
        info_frame = ttk.Frame(parent, style='Card.TFrame')
        info_frame.pack(fill='both', expand=True, padx=4, pady=4)
        ttk.Label(info_frame, text="Lockers disponibles", style='Section.TLabel').pack(anchor='w', pady=(0, 2), padx=2)
        
        self.listbox_lockers = tk.Listbox(
            info_frame,
            font=FUENTES['normal'],
            height=7,
            bd=0,
            highlightthickness=1,
            relief='solid',
            bg=COLORES['info_bg'],
            fg=COLORES['texto'],
            selectbackground=COLORES['boton_principal'],
            selectforeground=COLORES['texto'],
            highlightbackground=COLORES['borde']
        )
        self.listbox_lockers.pack(fill='both', expand=True, padx=2, pady=1)
        
        btn_frame = ttk.Frame(info_frame, style='Card.TFrame')
        btn_frame.pack(fill='x', padx=2, pady=2)
        ttk.Button(btn_frame, text="Refrescar", command=lambda: (self._hablar_admin('Refrescar'), self._refrescar_lockers()), style='Small.TButton').pack(side='left', padx=1)
        ttk.Button(btn_frame, text="Liberar", command=lambda: (self._hablar_admin('Liberar seleccionado'), self._liberar_locker_seleccionado()), style='Secondary.TButton').pack(side='left', padx=1)
        ttk.Button(btn_frame, text="Asignar y capturar", command=self._asignar_locker_manual, style='Primary.TButton').pack(side='left', padx=1)
        
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
            messagebox.showinfo("Exito", "Administrador creado")
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
                messagebox.showinfo("Exito", f"Locker {locker_num} liberado")
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")
    
    def _asignar_locker_manual(self):
        """Asigna un locker específico manualmente"""
        # Crear ventana para pedir locker y nombre
        dialog = tk.Toplevel(self)
        dialog.title("Asignar Locker")
        dialog.geometry("360x220")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORES['fondo'])
        self._preparar_ventana_fullscreen(dialog)
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Asignar locker", style='Header.TLabel').pack(pady=(8, 4))
        
        frame = ttk.Frame(dialog, style='Card.TFrame')
        frame.pack(fill='both', expand=True, padx=16, pady=(0, 10))
        
        ttk.Label(frame, text="Locker (1-4):", style='Subtitle.TLabel').grid(row=0, column=0, sticky='w', padx=8, pady=5)
        entry_locker = ttk.Spinbox(frame, from_=1, to=ADMIN_CONFIG['total_lockers'], width=10, font=FUENTES['normal'])
        entry_locker.set(1)
        entry_locker.grid(row=0, column=1, sticky='w', padx=8, pady=5)
        
        ttk.Label(frame, text="Nombre de referencia:", style='Subtitle.TLabel').grid(row=1, column=0, sticky='w', padx=8, pady=5, columnspan=2)
        entry_nombre = ttk.Entry(frame, font=FUENTES['normal'])
        entry_nombre.grid(row=2, column=0, columnspan=2, sticky='ew', padx=8, pady=5)
        
        frame.grid_columnconfigure(1, weight=1)
        
        result = {'ok': False}
        
        def confirmar():
            locker_num = int(entry_locker.get())
            nombre_usuario_custom = entry_nombre.get().strip() or f"Locker {locker_num}"
            
            result['locker_num'] = locker_num
            result['nombre_custom'] = nombre_usuario_custom
            result['ok'] = True
            dialog.destroy()
        
        def cancelar():
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=6, sticky='ew')
        ttk.Button(btn_frame, text="OK", command=confirmar, style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=cancelar, style='Secondary.TButton').pack(side='left', padx=5)
        
        self.wait_window(dialog)
        
        if not result['ok']:
            return
        
        locker_num = result['locker_num']
        nombre_usuario_custom = result['nombre_custom']
        
        lockers = self.db.listar_lockers(ADMIN_CONFIG['total_lockers'])
        locker_info = lockers[locker_num - 1]
        
        nombre_usuario = f"locker{locker_num}"

        if locker_info['estado'] == 'Ocupado' or self.db.obtener_usuario_por_nombre(nombre_usuario):
            messagebox.showwarning("Locker ocupado", f"Locker {locker_num} ya está ocupado por {locker_info['usuario']}.")
            return

        self._capturar_locker_manual(locker_num, nombre_usuario, nombre_usuario_custom)
    
    def _capturar_locker_manual(self, locker_num, nombre_usuario, nombre_referencia):
        """Captura rostro para locker específico"""
        if self.camera is None:
            try:
                self.camera = Camera(0)
                self.camera.iniciar()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo iniciar la cámara: {e}", parent=self)
                return

        captura_win = tk.Toplevel(self)
        captura_win.title(f"Capturar rostro - Locker {locker_num}")
        captura_win.geometry(WINDOW_SIZE)
        captura_win.configure(bg=COLORES['fondo'])
        self._preparar_ventana_fullscreen(captura_win)
        captura_win.transient(self)
        captura_win.grab_set()
        
        header = ttk.Frame(captura_win, style='Card.TFrame')
        header.pack(fill='x', padx=6, pady=(6, 3))
        title_box = ttk.Frame(header, style='Card.TFrame')
        title_box.pack(side='left', fill='x', expand=True, padx=8, pady=6)
        ttk.Label(title_box, text=f"Capturando rostro para Locker {locker_num}", style='Header.TLabel').pack(anchor='w')
        ttk.Label(title_box, text=f"Referencia: {nombre_referencia}", style='Subtitle.TLabel').pack(anchor='w', pady=(2, 0))
        ttk.Button(header, text="Cerrar", command=captura_win.destroy, style='Secondary.TButton').pack(side='right', padx=8, pady=6)
        
        video_frame = ttk.Frame(captura_win, style='Card.TFrame')
        video_frame.pack(fill='both', expand=True, padx=6, pady=3)
        
        label_video = ttk.Label(video_frame, background=COLORES['info_bg'], relief='flat')
        label_video.pack(fill='both', expand=True, padx=6, pady=6)
        
        captura_disponible = [False]
        frame_actual = [None]
        
        status_label = ttk.Label(captura_win, text="Cargando cámara...", style='Info.TLabel', justify='center', wraplength=700)
        status_label.pack(fill='x', padx=10, pady=4)
        
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
                    
                    demasiado_cerca = self._esta_demasiado_cerca(frame, rostros)
                    captura_disponible[0] = bool(rostros) and not demasiado_cerca

                    if demasiado_cerca:
                        status_label.config(text="Aléjate más de la cámara, estás muy cerca.")
                    elif captura_disponible[0]:
                        status_label.config(text="Rostro detectado. Presiona 'Capturar rostro' cuando estes listo.")
                    else:
                        status_label.config(text="No hay rostro detectado. Acercate mas a la camara.")
                    
                    imagen = Image.fromarray(frame_rgb)
                    imagen.thumbnail((620, 240), Image.Resampling.LANCZOS)
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
                encoding = self.face_recognizer.asociar_rostro(nombre_usuario, frame_actual[0])
                if encoding is None:
                    messagebox.showwarning("Atención", "No se pudo extraer el rostro. Ajusta tu posición e inténtalo otra vez.", parent=captura_win)
                    return

                usuario_id = self.db.guardar_usuario(nombre_usuario, "1234", 'usuario')
                
                ret, buffer = cv2.imencode('.jpg', frame_actual[0])
                if ret:
                    self.db.guardar_imagen(usuario_id, buffer.tobytes())

                if self.locker_controller:
                    self.locker_controller.activar_locker(locker_num)
                
                messagebox.showinfo("Listo", f"Locker {locker_num} esta configurado, abierto y listo para usar.", parent=captura_win)
                self._refrescar_lockers()
                captura_win.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=captura_win)
        
        btn_frame = ttk.Frame(captura_win, style='Card.TFrame')
        btn_frame.pack(fill='x', padx=6, pady=(0, 6))
        ttk.Button(btn_frame, text="Capturar rostro", command=capturar, style='Primary.TButton').pack(side='left', fill='x', expand=True, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=captura_win.destroy, style='Secondary.TButton').pack(side='left', fill='x', expand=True, padx=4)
        
        actualizar_video()
