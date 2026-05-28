#!/usr/bin/env python3
"""
Script de diagnóstico DIRECTO de GPIO
Sin usar LockerController, solo RPi.GPIO puro
"""
import sys
import time

print("\n" + "="*60)
print("DIAGNÓSTICO DIRECTO DE GPIO")
print("="*60)

# Verificar RPi.GPIO
try:
    import RPi.GPIO as GPIO
    print("[✅] RPi.GPIO importado correctamente")
except ImportError as e:
    print(f"[❌] No se pudo importar RPi.GPIO: {e}")
    sys.exit(1)

# Probar inicialización
try:
    print("\n[PASO 1] Intentando setmode(GPIO.BCM)...")
    GPIO.setmode(GPIO.BCM)
    print("[✅] setmode() exitoso")
except Exception as e:
    print(f"[❌] Error en setmode(): {e}")
    print("    Esto significa que RPi.GPIO no puede acceder al hardware GPIO")
    print("    Posibles causas:")
    print("      - No eres root (necesitas 'sudo')")
    print("      - No estás en una Raspberry Pi real")
    print("      - GPIO está siendo usado por otro proceso")
    sys.exit(1)

# Probar setup de un pin
pin_test = 17
try:
    print(f"\n[PASO 2] Intentando GPIO.setup({pin_test}, GPIO.OUT)...")
    GPIO.setup(pin_test, GPIO.OUT)
    print(f"[✅] Pin {pin_test} configurado como salida")
except Exception as e:
    print(f"[❌] Error configurando pin {pin_test}: {e}")
    GPIO.cleanup()
    sys.exit(1)

# Probar escritura
try:
    print(f"\n[PASO 3] Escribiendo GPIO.output({pin_test}, GPIO.HIGH)...")
    GPIO.output(pin_test, GPIO.HIGH)
    print("[✅] HIGH escrito correctamente")
    time.sleep(0.5)
    
    print(f"\n[PASO 4] Escribiendo GPIO.output({pin_test}, GPIO.LOW)...")
    GPIO.output(pin_test, GPIO.LOW)
    print("[✅] LOW escrito correctamente")
    
except Exception as e:
    print(f"[❌] Error escribiendo en pin {pin_test}: {e}")
    GPIO.cleanup()
    sys.exit(1)

# Limpiar
try:
    print(f"\n[PASO 5] Limpiando GPIO...")
    GPIO.cleanup()
    print("[✅] GPIO limpiado correctamente")
except Exception as e:
    print(f"[⚠️] Error limpiando GPIO: {e}")

print("\n" + "="*60)
print("DIAGNÓSTICO COMPLETADO")
print("="*60)
print("""
Si viste ✅ en todos los pasos:
  → RPi.GPIO funciona perfectamente
  → El problema está en la configuración de active_high o las conexiones

Si viste ❌:
  → RPi.GPIO no puede acceder al hardware
  → Necesitas: sudo (si no lo usaste ya)
  → O hay otro problema con el hardware
""")
