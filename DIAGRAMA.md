# Diagrama de Flujo - Smart Locker

## Estructura Simplificada ✅

```
Proyecto
├── main.py              ← PUNTO DE ENTRADA
├── config.py           ← CONFIGURACIÓN CENTRALIZADA
├── core.py             ← LÓGICA (BD, Rostros, Cámara)
├── ui.py               ← INTERFAZ GRÁFICA (Todo)
├── requirements.txt    ← DEPENDENCIAS
├── README.md           ← INSTRUCCIONES
├── FLUJO.txt          ← ESTE DOCUMENTO
└── rostros/           ← ALMACENA ROSTROS CALIBRADOS
```

## Flujo Principal

```
main.py
   ↓
   Inicializa:
   • Database (MySQL)
   • FaceRecognizer
   • Camera
   ↓
   UIApp (Tkinter) ← MENÚ PRINCIPAL
   ↓
   ┌─────────────────────────────────┐
   │                                 │
   │  🔓 Abrir Locker  📝 Registrar  │
   │       Admin Panel               │
   │                                 │
   └─────────────────────────────────┘
        ↓           ↓           ↓
    ACCESO      REGISTRO    ADMIN
```

---

## ¿Cómo Funciona Cada Acción?

### 1️⃣ ABRIR LOCKER (Reconocer rostro)

```python
iniciar_acceso()
    ↓
_reconocer_acceso() [Loop cada 30ms]
    ├─ Captura frame de cámara
    ├─ Compara con rostros conocidos
    ├─ Si coincide → Acceso concedido
    └─ Si no → Continúa reconociendo
```

**Resultado:** Abre locker asignado ✅

---

### 2️⃣ REGISTRAR ROSTRO (Nuevo usuario)

```python
iniciar_registro()
    ↓
    Pide nombre + contraseña
    ↓
    Crea usuario en BD (MySQL)
    ↓
_mostrar_registro() [Loop captura]
    ├─ Muestra video en tiempo real
    ├─ Detecta rostro (rectángulo verde)
    ├─ Usuario presiona "Capturar"
    │   ├─ Guarda imagen en carpeta "rostros/"
    │   ├─ Guarda encoding en memoria
    │   └─ Guarda en BD (MySQL)
    └─ Vuelve a menú
```

**Resultado:** Usuario registrado y listo para acceder ✅

---

### 3️⃣ ADMIN PANEL (Gestión)

```python
abrir_admin()
    ↓
    Valida usuario + contraseña
    ↓
    Abre AdminWindow (ventana emergente)
    ├─ Pestaña 1: Usuarios
    │  ├─ Listar usuarios
    │  ├─ Agregar nuevo
    │  └─ Eliminar
    ├─ Pestaña 2: Lockers
    │  ├─ Ver estado (libre/ocupado)
    │  └─ Liberar locker
    └─ Pestaña 3: Estadísticas
       └─ Ver accesos
```

**Resultado:** Control total del sistema ✅

---

## Módulos Internos

### `config.py` - Constantes Globales

```python
COLORES = {...}           # Tema visual
FUENTES = {...}           # Tipografías
DB_CONFIG = {...}         # Conexión MySQL
CAMERA_CONFIG = {...}     # Parámetros cámara
FACE_CONFIG = {...}       # Umbral similitud
ADMIN_CONFIG = {...}      # Configuración admin
```

---

### `core.py` - Lógica de Negocio

#### **Database Class** (MySQL)
```python
DB = Database(**DB_CONFIG)

DB.guardar_usuario(nombre, contraseña, rol)
DB.autenticar_usuario(nombre, contraseña) → Dict
DB.listar_usuarios_detallados() → List
DB.obtener_usuario_por_nombre(nombre) → Dict
DB.eliminar_usuario(nombre)
DB.listar_lockers() → List
DB.liberar_locker(numero)
DB.guardar_imagen(usuario_id, bytes)
```

#### **FaceRecognizer Class** (face_recognition)
```python
FACE = FaceRecognizer()

FACE.cargar_todos() → (encodings, nombres)
FACE.asociar_rostro(nombre, imagen_bgr) → encoding
FACE.reconocer(imagen_bgr, encodings, nombres) → nombre_coincidencia
FACE.detectar_rostros(imagen_bgr) → [(top, right, bottom, left), ...]
```

#### **Camera Class** (OpenCV)
```python
CAM = Camera(indice=0)

CAM.iniciar()              # Inicia thread de captura
CAM.leer_frame() → (ret, frame)
CAM.detener()             # Para la captura
```

---

### `ui.py` - Interfaz Gráfica

#### **UIApp Class** (Ventana principal)
```python
app = UIApp(root, db, face_recognizer)

app.mostrar_menu_principal()      # Menú inicial
app.iniciar_acceso()              # Reconocer rostro
app.iniciar_registro(nombre)      # Registrar nuevo
app.abrir_admin()                 # Panel de admin
app._actualizar_preview()         # Loop de video
app.cerrar()                      # Cierra todo
```

#### **AdminWindow Class** (Ventana emergente)
```python
admin = AdminWindow(parent, db)

# Tabs automáticas:
# 1. Usuarios (CRUD)
# 2. Lockers (ver/liberar)
# 3. Estadísticas
```

---

## Flujo de Datos - Ejemplo: Acceso

```
Usuario en frente → Cámara
        ↓
    OpenCV captura
        ↓
    face_recognition compara
        ↓
    ¿Coincide con "usuario1.jpg"?
        ├─ SÍ → BD: obtener_usuario_por_nombre("usuario1")
        │       ↓
        │       Mensaje: "Bienvenido usuario1"
        │       ↓
        │       Locker abierto ✅
        │
        └─ NO → Continúa reconociendo
```

---

## Flujo de Datos - Ejemplo: Registro

```
Usuario ingresa nombre "Juan"
        ↓
    BD: guardar_usuario("Juan", "pass123", "usuario")
        ↓
        usuario_id = 42
        ↓
    Sistema muestra cámara
        ↓
    Usuario presiona "Capturar"
        ↓
    Frame → rostros/Juan.jpg ✅
        ↓
    face_recognition genera encoding
        ↓
    BD: guardar_imagen(usuario_id=42, bytes_imagen)
        ↓
    Listo para usar 🚀
```

---

## Thread Safety 🔒

```python
# Cámara captura en Thread independiente
Camera._captura_loop()  [daemon=True]
    ├─ Captura cada 30ms
    └─ Almacena en self.ultimo_frame (thread-safe con Lock)

# UI lee frames sin bloqueos
UIApp.leer_frame()
    └─ Usa Lock para acceso seguro
```

---

## Seguridad ⚠️

- **Contraseñas:** Guardadas en MySQL (idealmente hashear con bcrypt)
- **Admin:** Solo usuarios con rol='admin' pueden acceder
- **Rostros:** Almacenados en carpeta local (encripción opcional)

---

## Instalación Rápida

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar config.py (MySQL, cámara)
# 3. Ejecutar
python main.py
```

---

## ¿Cómo Agregar Funciones Nuevas?

### Ejemplo: Agregar notificación por email

```python
# En core.py:
from smtplib import SMTP

class Notificador:
    def enviar_email(self, destinatario, asunto, contenido):
        # ...

# En ui.py:
notificador = Notificador()
notificador.enviar_email("admin@locker.com", "Acceso concedido", f"Usuario: {nombre}")
```

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| Cámara no abre | Cambiar `CAMERA_CONFIG['indice']` en config.py |
| BD no conecta | Verificar MySQL está corriendo, credenciales en config.py |
| Rostro no se reconoce | Aumentar `FACE_CONFIG['umbral_similitud']` |
| Interfaz lenta | Reducir resolución en `CAMERA_CONFIG` |

---

## Próximas Mejoras 🚀

- [ ] Agregar BCrypt para hashear contraseñas
- [ ] Exportar logs de acceso a Excel
- [ ] Push notifications a móvil
- [ ] Doble factor de autenticación
- [ ] API REST para integración

---

**Creado:** 2026
**Estado:** ✅ Funcional y refactorizado
