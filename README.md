# Backyardigans solaaskhvashdb

## Uso de la cámara

El programa está preparado para funcionar tanto con una **Raspberry Pi Camera** como con la cámara
USB/integrada del portátil. Por defecto se intenta abrir la cámara con índice `0` a través de OpenCV.

- Para forzar un índice distinto (por ejemplo si la laptop reporta más de una cámara) se puede exportar
  la variable de entorno `CAMERA_INDEX`:

  ```bash
  set CAMERA_INDEX=0        # Windows
  export CAMERA_INDEX=1     # Linux/macOS
  ```

- Si se ejecuta en una Pi y se desea usar la cámara CSI, active el soporte mediante la
  variable de entorno `USAR_PICAMERA` (valores admitidos: `1`, `true`, `yes`).
  El programa automáticamente pasará esta opción a `CameraHandler` en las pantallas
  de apertura y registro.

El código también imprime un mensaje cuando la cámara se abre correctamente y da un error
en caso contrario.

### Interfaz y extras

- Diseño más claro y moderno con fondo gris suave.
- Botón de **Salir** fijo en la esquina inferior izquierda.
- La cámara ocupa toda la ventana durante el registro de un nuevo usuario.
- En la pantalla de apertura se muestra, debajo del video, un área para indicar
  qué locker se abrió y a qué persona se le concedió acceso.
- El mini‑juego ha sido eliminado para una experiencia más limpia.
