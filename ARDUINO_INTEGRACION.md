# Arduino Nano + LEDs - Guía de Integración

## 📋 Resumen

Tu sistema de LEDs está **controlado por Arduino Nano** en lugar de conectarse directamente a Raspberry Pi. Se comunican por **puerto serial (COM)**.

## 🔧 Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| `arduino_led_controller.py` | Módulo para comunicarse con Arduino por serial |
| `test_arduino_leds.py` | Script de prueba sin afectar la app principal |
| `Arduino_Nano_LED_Control.ino` | Código que cargar en el Arduino |
| `led_controller.py` | ⚠️ NO MODIFICADO - Controla GPIO directo de RPi |

## ⚡ Paso 1: Cargar el código en Arduino Nano

### En Arduino IDE:
1. Abre **Arduino IDE**
2. Copia el contenido de `Arduino_Nano_LED_Control.ino`
3. **Selecciona Board**: `Arduino Nano`
4. **Selecciona Processor**: `ATmega328P`
5. **Selecciona Puerto**: El que veas en Herramientas → Puerto
6. Haz clic en ⬆️ **Cargar**

### Verificación:
- Abre **Herramientas → Monitor Serial**
- Baudrate: **9600**
- Deberías ver: `[OK] Arduino Nano iniciado - Esperando comandos...`

## 🧪 Paso 2: Probar con el Script de Prueba

**NO ejecutes la app principal aún**. Primero prueba:

```bash
python test_arduino_leds.py
```

El script hará:
1. ✅ Detectar puertos seriales disponibles
2. ✅ Conectar al Arduino
3. ✅ Mostrar menú interactivo para pruebas
4. ✅ Encender/apagar LEDs sin tocar la app principal

## 📡 Comunicación Serial

El Arduino recibe **comandos de texto** por puerto serial:

```
L1ON  → Encender LED del Locker 1
L1OFF → Apagar LED del Locker 1
L2ON, L2OFF → LED 2
L3ON, L3OFF → LED 3
L4ON, L4OFF → LED 4
```

Ejemplo en Python:
```python
from arduino_led_controller import obtener_arduino_leds

leds = obtener_arduino_leds(puerto='COM3')  # Cambiar COM3 por tu puerto
leds.encender_led(1)  # Encender LED 1
leds.parpadear_led(2)  # Parpadear LED 2
```

## 🔌 Conexión de Hardware

```
Arduino Nano          Protoboard
┌─────────────────┐
│ 5V  │ GND │ Pin A0 ──→ Resistencia 470Ω ──→ LED 1 ──→ GND
│ Pin A1 ──→ Resistencia 470Ω ──→ LED 2 ──→ GND
│ Pin A2 ──→ Resistencia 470Ω ──→ LED 3 ──→ GND
│ Pin A3 ──→ Resistencia 470Ω ──→ LED 4 ──→ GND
│         │
└─────────────────┘
     ↓ USB
   Raspberry Pi
```

## 🎯 Integración con ui.py

Si deseas integrar Arduino con la app principal, reemplaza:

```python
from led_controller import obtener_leds
```

Con:

```python
from arduino_led_controller import obtener_arduino_leds as obtener_leds
```

Y usa el puerto correcto en `config.py`:

```python
ARDUINO_CONFIG = {
    'puerto': 'COM3',  # Cambiar según tu sistema
    'baudrate': 9600
}
```

## ⚠️ Puertos Seriales por Sistema

| Sistema | Puerto típico |
|---------|---|
| Windows | `COM3`, `COM4`, ... |
| Linux (Raspberry Pi) | `/dev/ttyUSB0`, `/dev/ttyACM0` |
| macOS | `/dev/tty.usbserial-*` |

## 🔍 Solución de Problemas

### ❌ "No se pudo conectar a Arduino"
- Verifica que el Arduino esté conectado por USB
- Ejecuta `test_arduino_leds.py` para detectar el puerto automáticamente
- Instala drivers CH340 si es necesario

### ❌ "Puerto COM no encontrado"
- Abre Arduino IDE → Herramientas → Puerto
- Anota el puerto que aparece
- Úsalo en el script de prueba

### ❌ "LEDs no se encienden"
- Abre Monitor Serial (9600 baud) en Arduino IDE
- Escribe manualmente `L1ON` y presiona Enter
- Si el LED se enciende, el Arduino funciona
- Si no, revisa conexiones de resistencias y LEDs

### ❌ "Comunicación serial lenta"
- Verifica que baudrate sea 9600 en ambos lados
- Reduce la velocidad de parpadeo en código

## 📚 Referencia Rápida

```python
# Inicializar (detecta puerto automáticamente)
leds = obtener_arduino_leds()

# O especificar puerto manualmente
leds = obtener_arduino_leds(puerto='COM3')

# Controlar LEDs
leds.encender_led(1)      # Encender
leds.apagar_led(1)        # Apagar
leds.parpadear_led(1)     # Parpadear 2 segundos
leds.encender_todos()     # Encender todos
leds.apagar_todos()       # Apagar todos

# Verificar estado
estado = leds.estado_leds()
print(estado)  # {'1': True, '2': False, ...}

# Desconectar
leds.desconectar()
```

## ✅ Checklist Final

- [ ] Arduino Nano cargado con `Arduino_Nano_LED_Control.ino`
- [ ] Monitor Serial muestra "Arduino Nano iniciado"
- [ ] Ejecutado `test_arduino_leds.py` correctamente
- [ ] LEDs responden a los comandos de prueba
- [ ] Sé qué puerto COM usa mi Arduino
- [ ] Listo para integrar con aplicación principal

## 🚀 Próximo Paso

Una vez verificado todo, puedes opcionalmente integrar Arduino con `ui.py` editando:

1. Importar en `ui.py`:
   ```python
   from arduino_led_controller import obtener_arduino_leds
   ```

2. En `__init__` de UIApp, cambiar:
   ```python
   self.led_controller = obtener_arduino_leds(puerto='COM3')  # Tu puerto
   ```

El resto del código seguirá funcionando igual (los métodos son idénticos).

---

**Nota**: El archivo `led_controller.py` original **NO fue modificado**. Sigue funcionando para GPIO directo de Raspberry Pi. Arduino usa un módulo completamente separado.
