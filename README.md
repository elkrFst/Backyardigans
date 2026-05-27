# Smart Locker - Sistema de Reconocimiento Facial

Este proyecto es un sistema de acceso controlado por rostro para **locker automáticos**. El enfoque actual es la aplicación principal, sin dependencias de Arduino ni instrucciones externas.

## Estructura del proyecto

```
Backyardigans/
  main.py
  config.py
  core.py
  ui.py
  README.md
  requirements.txt
  assets/
    fuentes/
    iconos/
  database/
    mysql_face_storage.py
  gui/
    app.py
  recognition/
    face_recognizer.py
  rostros/
  face_recognition_cv2.py
```

### Archivos principales

- `main.py`
  - Punto de entrada de la aplicación.
  - Intenta conectar a MySQL usando los datos de `config.py`.
  - Si falla la conexión, usa una base de datos simulada para demostración.
  - Crea la ventana de Tkinter y arranca la app principal.

- `config.py`
  - Configuración centralizada del sistema.
  - Define colores, fuentes, datos de MySQL, cámara, reconocimiento facial y valores de interfaz.
  - Permite cambiar resolución, modo pantalla completa y umbral de similitud facial.

- `core.py`
  - Contiene la lógica de negocio principal.
  - `Database`: maneja la conexión MySQL y CRUD de usuarios, imágenes y lockers.
  - `FaceRecognizer`: carga imágenes de rostros, crea encodings y compara rostros.
  - `Camera`: controla la cámara con OpenCV en un hilo independiente.
  - `LockerController`: controla los relés de los 4 lockers mediante GPIO en Raspberry Pi.

- `ui.py`
  - Interfaz gráfica principal construida con Tkinter.
  - Administra el menú principal, registro de rostros, acceso por reconocimiento y panel administrativo.
  - Muestra la vista de cámara en tiempo real y los estados del sistema.

- `requirements.txt`
  - Lista de dependencias necesarias para ejecutar la aplicación.

- `face_recognition_cv2.py`
  - Módulo alternativo compatible con `face_recognition`.
  - Usa OpenCV y Haar cascades para detectar rostros cuando `face-recognition` no está instalado.

### Carpetas y módulos secundarios

- `assets/`
  - Incluye recursos visuales del proyecto.
  - `fuentes/`: tipografías utilizadas en la interfaz.
  - `iconos/`: íconos o imágenes de la app.

- `database/`
  - Contiene `mysql_face_storage.py`.
  - `mysql_face_storage.py`: una capa adicional de almacenamiento MySQL para accesos y usuarios.
  - Define tablas de `accesos` y métodos de consulta sobre éstos.

- `gui/`
  - Contiene `app.py`, que es un módulo alternativo/secondary de interfaz.
  - `app.py`: app Tkinter con otro diseño y uso de `CameraHandler` y `FaceRecognizer` separado.
  - Esta carpeta sirve como implementación alternativa de la interfaz gráfica.

- `recognition/`
  - Contiene `face_recognizer.py`.
  - `face_recognizer.py`: otro módulo de reconocimiento facial que puede cargar desde archivos o base de datos.
  - Proporciona métodos de comparación y carga de encodings.

- `rostros/`
  - Carpeta donde se guardan los rostros registrados del usuario.
  - El sistema principal usa esta carpeta para almacenar imágenes de rostros como `locker1.jpg`, `locker2.jpg`, etc.

## Cómo funciona cada módulo

### `main.py`

- Inicializa la GUI.
- Crea la conexión a la base de datos si está disponible.
- Usa `FaceRecognizer` para preparar detección facial.

### `config.py`

- `COLORES`: tema visual de la interfaz.
- `FUENTES`: tipografías usadas en botones, títulos y textos.
- `DB_CONFIG`: credenciales de MySQL.
- `CAMERA_CONFIG`: resolución y FPS de la cámara.
- `FACE_CONFIG`: carpeta de rostros y umbral de similitud.
- `ADMIN_CONFIG`: configuración de administrador y cantidad total de lockers.
- `GPIO_CONFIG`: configuración del control de relés para Raspberry Pi:
  - `habilitado`: activa/desactiva el control GPIO (variable de entorno `GPIO_ENABLED`)
  - `pines`: mapeo de lockers a pines GPIO (1→17, 2→27, 3→22, 4→23)
  - `pulso_duracion`: duración del pulso de apertura (2 segundos por defecto)
  - `active_high`: nivel de activación (False = señal baja)
- `WINDOW_SIZE` / `WINDOW_FULLSCREEN`: define el tamaño de la ventana Tkinter.

### `core.py`

- La clase `Database` gestiona usuarios, guardado de imágenes, y estado de lockers.
- La clase `FaceRecognizer` carga imágenes de `rostros/`, extrae encodings y reconoce caras.
- La clase `Camera` arranca un hilo que captura frames de la webcam de manera continua.
- La clase `LockerController` controla los relés de los 4 lockers:
  - Inicializa los 4 pines GPIO configurados en `GPIO_CONFIG`
  - Ejecuta pulsos de 2 segundos en un thread separado para no bloquear la interfaz
  - Se activa automáticamente cuando se reconoce un rostro y se abre el locker correspondiente

### `ui.py`

- Construye la interfaz principal con botones, tarjetas de estado y vista de cámara.
- `iniciar_acceso`: arranca el reconocimiento de rostro para abrir un locker.
- `iniciar_registro`: captura un nuevo rostro y lo guarda en la base de datos y en la carpeta `rostros/`.
- `abrir_admin`: muestra el panel de administración protegido por login.
- El panel administrativo permite liberar lockers y ver el estado actual.

## Uso

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta la aplicación:
   ```bash
   python main.py
   ```
3. Usa la cámara para registrar y abrir lockers.

## Flujo de Reconocimiento y Activación de Lockers

### Cuando se reconoce un rostro exitosamente:

1. **Captura**: La aplicación captura el rostro mediante la cámara en tiempo real.
2. **Comparación**: Se compara el rostro capturado con los rostros almacenados usando encodings.
3. **Identificación**: Si la similitud es mayor al umbral, se identifica al usuario (ej: `locker1`).
4. **Extracción de número**: Se extrae el número del locker (ej: 1 de `locker1`).
5. **Activación GPIO**: Se envía un pulso de 2 segundos al relé del locker correspondiente:
   - El pin GPIO se activa (señal baja porque `active_high=False`)
   - Esto abre el solenoide/actuador del locker
   - Tras 2 segundos, el pin se desactiva automáticamente
6. **Confirmación**: Se muestra un mensaje de éxito al usuario.

### Configuración de Hardware:

Los 4 relés están conectados a los siguientes pines GPIO:
- Locker 1: GPIO 17
- Locker 2: GPIO 27
- Locker 3: GPIO 22
- Locker 4: GPIO 23

Cada relé se activa con una señal baja (active_high=False), lo que es estándar para relés en Raspberry Pi.

### Habilitación en Raspberry Pi:

Para activar el control GPIO en Raspberry Pi, establece la variable de entorno antes de ejecutar:

```bash
export GPIO_ENABLED=1
python main.py
```

Sin esta variable, el sistema se ejecuta en **modo simulación** (útil para desarrollo en Windows/Linux sin Raspberry Pi).

## Estructura de datos relevante

- Los rostros se guardan como archivos de imagen en `rostros/`.
- La base de datos MySQL guarda usuarios, contraseñas, roles y registros de imagen.
- El sistema asume un máximo de 4 lockers y asigna el siguiente locker libre automáticamente.

## Notas finales

- Esta versión está limpia de Arduino y documentaciones externas.
- El proyecto actual se enfoca en la aplicación Tkinter, el reconocimiento facial, la gestión de lockers y el control GPIO.
- El control GPIO con gpiozero es totalmente compatible con Raspberry Pi y se ejecuta en modo simulación en otros SO.
- Si necesitas una versión más ligera, `face_recognition_cv2.py` permite que el sistema funcione sin `face-recognition` ni `dlib`.
- Los pulsos de apertura se ejecutan en threads separados para no bloquear la interfaz principal.
- El sistema está optimizado para ejecutarse en Raspberry Pi con pantalla táctil de 7 pulgadas.

