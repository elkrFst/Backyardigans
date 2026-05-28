#!/usr/bin/env python3
"""
Script de prueba de GPIO usando RPi.GPIO (alternativa a gpiozero)
"""
import time
import sys
from config import GPIO_CONFIG

try:
    import RPi.GPIO as GPIO
    print("[GPIO] RPi.GPIO disponible")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except ImportError:
    print("[ERROR] RPi.GPIO no disponible")
    sys.exit(1)
except RuntimeError as e:
    print(f"[ERROR] {e}")
    print("Intenta ejecutar con: sudo python3 test_gpio_rpi.py")
    sys.exit(1)

def test_relay(locker_num, pin):
    """Prueba un relé individual"""
    print(f"\n{'='*50}")
    print(f"Probando Locker {locker_num} en pin GPIO {pin}")
    print(f"{'='*50}")
    
    try:
        # Configurar pin como salida
        GPIO.setup(pin, GPIO.OUT)
        
        # Estado inicial (LOW = apagado)
        GPIO.output(pin, GPIO.LOW)
        print(f"✅ Pin {pin} configurado como salida (inicial: LOW)")
        
        # Test 1: Estado inicial
        estado = GPIO.input(pin)
        print(f"\n[1] Estado inicial: {estado} (LOW=0, HIGH=1)")
        print(f"    👉 El LED del relé debería estar APAGADO")
        
        input("    Presiona Enter cuando hayas verificado...")
        
        # Test 2: Activar (HIGH)
        print(f"\n[2] ACTIVANDO relé (HIGH)...")
        GPIO.output(pin, GPIO.HIGH)
        estado = GPIO.input(pin)
        print(f"    Estado: {estado}")
        print(f"    👉 El LED del relé debería estar ENCENDIDO")
        
        input("    Presiona Enter cuando hayas verificado...")
        time.sleep(1)
        
        # Test 3: Desactivar (LOW)
        print(f"\n[3] DESACTIVANDO relé (LOW)...")
        GPIO.output(pin, GPIO.LOW)
        estado = GPIO.input(pin)
        print(f"    Estado: {estado}")
        print(f"    👉 El LED del relé debería estar APAGADO")
        
        input("    Presiona Enter cuando hayas verificado...")
        
        print(f"\n✅ Test completado para Locker {locker_num}\n")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("PRUEBA DE GPIO Y RELÉS (RPi.GPIO)")
    print("="*60)
    
    print(f"\nPines configurados:")
    pines = GPIO_CONFIG['pines']
    for locker_num, pin in sorted(pines.items()):
        print(f"  Locker {locker_num}: GPIO {pin}")
    
    try:
        # Probar cada relé
        for locker_num in sorted(pines.keys()):
            pin = pines[locker_num]
            success = test_relay(locker_num, pin)
            
            if not success:
                print(f"\n❌ Error probando Locker {locker_num}")
                break
            
            # Preguntar si continuar
            if locker_num < max(pines.keys()):
                cont = input(f"\n¿Continuar con el próximo relé? (s/n): ").lower()
                if cont not in ('s', 'si', 'y', 'yes'):
                    break
        
        print("\n" + "="*60)
        print("DIAGNÓSTICO:")
        print("="*60)
        print("""
IMPORTANTE - Nota sobre active_high vs RPi.GPIO:
  
  En gpiozero:
    - active_high=False → on() envía LOW (relé activo con BAJO)
    - active_high=True → on() envía HIGH (relé activo con ALTO)
  
  En RPi.GPIO directo:
    - Siempre enviamos HIGH/LOW manualmente
    - Necesitas conocer la lógica del módulo de relé
  
Si el LED del relé está SIEMPRE encendido:
  - El problema es probablemente que el relé está siendo activado 
    constantemente por otro factor (alimentación, conexión)
  - O active_high en config.py tiene la lógica invertida
  
Soluciones:
  1. Si con HIGH el relé se apaga, invierte la lógica en core.py
  2. Verifica que los pines GPIO no tengan pull-ups/downs conflictivos
  3. Comprueba alimentación correcta del módulo relé (5V/GND)
        """)
    
    finally:
        # Limpiar GPIO
        GPIO.cleanup()
        print("\n✅ GPIO limpiado")

if __name__ == '__main__':
    main()
