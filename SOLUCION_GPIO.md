# 🔧 Guía de Resolución de Problemas GPIO y Relés

## ✅ Lo que ya arreglamos:

1. **GPIO habilitado** - Cambié `GPIO_CONFIG['habilitado']` de `os.environ.get(...)` a `True` en `config.py`
2. **eSpeak instalado** - Los errores de TTS deberían desaparecer

## 🔴 Problema: Los relés no abren las cerraduras

**Síntomas:**
- Los LEDs de los relés están SIEMPRE encendidos (verdes)
- O los relés nunca se activan/desactivan

### Causa probable: Configuración de `active_high` invertida

En `config.py`, tenemos:
```python
'active_high': False    # Los relés se activan con señal baja
```

Esto DEBERÍA significar que:
- Cuando gpiozero hace `relay.on()` → envía nivel LOW → relé se ACTIVA
- Cuando gpiozero hace `relay.off()` → envía nivel HIGH → relé se DESACTIVA

**PERO** algunos módulos de relé funcionan al revés.

---

## 🛠️ SOLUCIÓN: Invertir la lógica

Si los LEDs están siempre encendidos, prueba cambiar `active_high` de `False` a `True`:

### Opción 1: Cambiar en config.py
```python
GPIO_CONFIG = {
    'habilitado': True,
    'pines': { ... },
    'pulso_duracion': 2.0,
    'active_high': True  # ← CAMBIAR DE False A True
}
```

### Opción 2: Invertir la lógica en core.py
Si no quieres cambiar config.py, modifica el método `_pulso_locker`:

En la función `_pulso_locker`, **inviértete la lógica**:
```python
def _pulso_locker(self, locker_num):
    """Ejecuta el pulso de apertura del locker"""
    try:
        relé = self.relés[locker_num]
        duracion = GPIO_CONFIG['pulso_duracion']
        
        print(f"[GPIO] 🔓 Activando locker {locker_num} por {duracion}s")
        
        # SOLUCIÓN: Usa off() en lugar de on() si active_high está invertido
        if hasattr(relé, 'off'):  # ← CAMBIAR DE 'on' A 'off'
            relé.off()
        
        time.sleep(duracion)
        
        if hasattr(relé, 'on'):   # ← CAMBIAR DE 'off' A 'on'
            relé.on()
        
        print(f"[GPIO] 🔒 Locker {locker_num} desactivado")
    except Exception as e:
        print(f"[ERROR] Pulsando locker {locker_num}: {e}")
```

---

## 🔍 PRUEBA RÁPIDA

1. **Copia el script de prueba** y ejecútalo:
   ```bash
   sudo python3 test_gpio_rpi.py
   ```

2. Observa el LED del relé cuando dice "ACTIVANDO":
   - Si el LED **se apaga** → Necesitas invertir la lógica
   - Si el LED **se enciende** → La lógica es correcta (pero comprueba las conexiones)
   - Si no cambia nada → Problema de conexión física

---

## 📋 CHECKLIST de conexiones físicas

Verifica que tienes:

1. **Alimentación del módulo de relé:**
   - VCC (+5V) del relé → +5V de Raspberry Pi (pin 2 o 4)
   - GND del relé → GND de Raspberry Pi (pin 6, 9, 14, 20, 25, 30, 34, 39)

2. **Conexión de señal:**
   - IN (o señal) del relé → GPIO pin (17, 27, 22 o 23)

3. **Conexión de las cerraduras:**
   - COM (común) → 12V positivo
   - NO (normalmente abierto) → a la cerradura
   - O COM → GND, NO → a la cerradura (depende del tipo)

---

## 🚀 Pasos para resolver:

### Paso 1: Intenta invertir `active_high`
1. Abre `config.py`
2. Cambia `'active_high': False` a `'active_high': True`
3. Guarda y ejecuta:
   ```bash
   python3 main.py
   ```
4. Prueba a abrir un locker
5. Si funciona ✅ → ¡Listo!
6. Si no funciona ❌ → Vuelve a cambiar a `False` e intenta Paso 2

### Paso 2: Si invertir `active_high` no funciona
Probablemente hay un problema físico:
1. Desconecta la Raspberry Pi
2. Verifica todas las conexiones (foto sería útil)
3. Comprueba continuidad con multímetro si tienes
4. Reconecta y prueba de nuevo

### Paso 3: Si aún no funciona
- Verifica que `GPIO_CONFIG['habilitado']` está en `True`
- Comprueba que no hay otro código que esté desactivando los GPIO
- Considera usar relés simulados (MockRelay) para probar la app sin hardware

---

## 📌 NOTA IMPORTANTE

Si los relés están **SIEMPRE** encendidos (LED verde constante), probablemente:

1. **El relé está incorrectamente alimentado** → Revisar alimentación
2. **`active_high` está invertido** → Cambiar en `config.py`
3. **El pin GPIO tiene un pull-up/pull-down conflictivo** → Menos probable pero posible

La manera más fácil de probar es invertir `active_high` y ver si el comportamiento del LED cambia.

---

## 💡 Comandos útiles

**Ver qué GPIO están siendo usados:**
```bash
gpio readall  # Si tienes gpio-admin instalado
```

**Instalar herramienta GPIO (opcional):**
```bash
sudo apt install wiringpi
gpio readall
```

**Ver logs de la app:**
```bash
python3 main.py 2>&1 | grep "GPIO\|activando"
```

---

Avísame qué resulta al invertir `active_high` o si necesitas más ayuda con las conexiones físicas.
