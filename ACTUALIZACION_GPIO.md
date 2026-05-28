# 🔧 ACTUALIZACIÓN - Guía de Resolución de Problemas GPIO y Relés

## ✅ CAMBIOS REALIZADOS:

1. **GPIO habilitado** ✅ - `GPIO_CONFIG['habilitado'] = True` en `config.py`
2. **eSpeak instalado** ✅ - Errores de TTS resueltos
3. **RPi.GPIO agregado** ✅ - Ahora intenta usar RPi.GPIO directo (MÁS COMPATIBLE)
4. **Errores pyttsx3 corregidos** ✅ - Se limpian correctamente
5. **Fallback automático** ✅ - Si RPi.GPIO falla, usa gpiozero; si todo falla, usa MockRelay

---

## 🚀 NUEVA JERARQUÍA DE GPIO:

El código ahora intenta (en orden):
1. **RPi.GPIO** ← Más compatible, acceso directo
2. **gpiozero** ← Si RPi.GPIO no disponible  
3. **MockRelay** ← Si nada funciona (simulación)

---

## 🧪 PROBAR SOLO GPIO (sin cámara):

```bash
cd /home/backyardigans/Desktop/Backyardigans
sudo python3 test_gpio_solo.py
```

**Ventajas:**
- No necesita cámara
- Prueba cada relé individualmente
- Interactivo
- Perfecto para diagnóstico

---

## 🛠️ SI LOS RELÉS NO FUNCIONAN:

### Paso 1: Invertir `active_high`

**Opción A - Script automático:**
```bash
python3 config_gpio.py
```

**Opción B - Manual:**
En `config.py`, sección `GPIO_CONFIG`:
```python
'active_high': True  # Cambiar de False a True (o viceversa)
```

### Paso 2: Ejecutar app y probar
```bash
python3 main.py
```

### Paso 3: Si aún no funciona
Verifica conexiones físicas:
- VCC (5V) → Pin 2 o 4 de Raspberry Pi
- GND → Pin 6, 9, 14, 20, 25, 30, 34 o 39 de Raspberry Pi
- IN (relé) → GPIO pin (17, 27, 22 o 23)

---

## 📊 Archivos nuevos/modificados:

| Archivo | Estado |
|---------|--------|
| `core.py` | ✅ Agregada `RPiGPIORelay`, mejorada `LockerController` |
| `config.py` | ✅ GPIO habilitado |
| `ui.py` | ✅ pyttsx3 limpiado correctamente |
| `test_gpio_solo.py` | ✨ NUEVO - Prueba GPIO sin cámara |
| `config_gpio.py` | ✨ NUEVO - Helper para cambiar `active_high` |
| `test_gpio_rpi.py` | Disponible |

---

## 💡 Lógica de `active_high`:

**Si `active_high = False` (relé activo en LOW):**
- `relay.on()` → Envía LOW → Relé se ACTIVA
- `relay.off()` → Envía HIGH → Relé se DESACTIVA

**Si `active_high = True` (relé activo en HIGH):**
- `relay.on()` → Envía HIGH → Relé se ACTIVA
- `relay.off()` → Envía LOW → Relé se DESACTIVA

---

## 📌 IMPORTANTE:

El código ahora **intenta automáticamente** usar RPi.GPIO si está disponible. Si ves:

```
[GPIO] ✅ RPi.GPIO disponible
[GPIO] ✅ Relé locker 1 configurado en pin 17 (RPi.GPIO)
```

✅ Significa que está usando RPi.GPIO directamente (BUENO)

Si ves:

```
[GPIO] ⚠️ Funcionando en modo mixto (algunos relés reales, algunos simulados)
[GPIO-SIM] 🔓 Relé 1 ACTIVADO (simulado)
```

❌ Significa que está usando MockRelay (problema de hardware/permisos)

---

## 🎯 PRÓXIMOS PASOS:

1. Ejecuta: `sudo python3 test_gpio_solo.py`
2. Observa si los LEDs cambian
3. Si no: Invierte `active_high` con `python3 config_gpio.py`
4. Prueba de nuevo

**Avísame qué se ve en los logs.**
