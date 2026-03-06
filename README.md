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

- Si se ejecuta en una Pi y se desea usar la cámara CSI, pase `usar_picamera=True` al
  constructor de `CameraHandler` o haga la selección en el código.

El código también imprime un mensaje cuando la cámara se abre correctamente y da un error
en caso contrario.

### Interfaz y extras

- Fondo oscuro/degradado con estilo "futurista".
- Botón de **Salir** fijo en la esquina inferior izquierda.
- Mini‑juego tipo dinosaurio (presiona barra espaciadora para hacer saltar al dinosaurio) situado
  en la esquina superior izquierda; funciona en todas las pantallas.