# Smart Locker - Sistema de Reconocimiento Facial

Control de acceso a **4 lockers fijos** usando reconocimiento facial.

## Estructura

```
main.py                - Punto de entrada
config.py              - Configuración centralizada
core.py                - Lógica: Base de datos, Reconocimiento, Cámara
ui.py                  - Interfaz gráfica (Tkinter)
led_controller.py      - Control de 4 LEDs (Raspberry Pi GPIO)
test_leds.py           - Script para probar los LEDs
requirements.txt       - Dependencias
CONEXION_LEDS.txt      - Instrucciones completas de conexión
DIAGRAMAS_LEDS.txt     - Diagramas visuales de conexión
rostros/               - Almacena rostros (máximo 4)
```

## Funcionalidades

- ✅ **4 Lockers fijos** (locker1, locker2, locker3, locker4)
- ✅ **Registro automático** - Asigna al primer locker libre (solo usuarios normales)
- ✅ **Reconocimiento facial** - Abre locker específico
- ✅ **Admin panel** - Liberar/asignar lockers específicos (admins no consumen lockers)
- ✅ **Máximo 4 rostros** - Un rostro por locker (solo para usuarios normales)
- ✅ **Separación de roles** - Admins gestionan el sistema sin ocupar lockers
- ✅ **Control de 4 LEDs** - Simulación visual de lockers (Raspberry Pi GPIO)

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

### Flujo de Uso

1. **Admin Login**: Los administradores acceden al panel de control sin ocupar lockers
2. **Registrar Usuario**: Presiona "Registrar Nuevo Locker" → Se asigna automáticamente al primer locker libre (solo usuarios normales)
3. **Acceder**: Presiona "Abrir Locker" → Se reconoce el rostro y abre el locker correspondiente
4. **Admin Panel**: Panel de administración para liberar/asignar lockers específicos

## Configuración

Edita `config.py` para:
- Credenciales MySQL
- Resolución de cámara
- Índice de cámara (0 = integrada)
- Umbral de similitud de rostros

## 🔌 Control de LEDs (Simulación de Lockers)

El sistema integra control de **4 LEDs** conectados a los GPIO de Raspberry Pi 5:

### Hardware Necesario
- 4x LEDs (cualquier color)
- 4x Resistencias 470Ω-1kΩ
- Cables jumper y breadboard
- Raspberry Pi 5 con GPIO habilitado

### Conexión Rápida
```
GPIO 17 (Pin 11) → Resistencia → LED 1 → GND
GPIO 27 (Pin 13) → Resistencia → LED 2 → GND
GPIO 22 (Pin 15) → Resistencia → LED 3 → GND
GPIO 23 (Pin 16) → Resistencia → LED 4 → GND
```

### Comportamiento de LEDs
- 📍 **Al Registrar**: LED parpadea 2 segundos
- 📍 **Al Abrir**: LED se enciende por 3 segundos
- 📍 **Modo Simulación**: Si no está en Raspberry Pi, se simula en consola

### Prueba Rápida
```bash
python3 test_leds.py
```

Para instrucciones **completas y detalladas**, consulta:
- 📄 `CONEXION_LEDS.txt` - Instrucciones paso a paso
- 📄 `DIAGRAMAS_LEDS.txt` - Diagramas visuales y esquemas

## Características

- ✅ Reconocimiento facial con face_recognition
- ✅ Base de datos MySQL
- ✅ Admin panel para gestión de usuarios
- ✅ Control de lockers (libre/ocupado)
- ✅ Registro de accesos
- ✅ Interfaz limpia y moderna

