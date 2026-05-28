#!/usr/bin/env python3
"""
Script de prueba para verificar GPIO y relés
"""
import time
import sys
from config import GPIO_CONFIG

try:
    from gpiozero import OutputDevice
    print("[GPIO] gpiozero disponible")
except ImportError:
    print("[ERROR] gpiozero no disponible")
    sys.exit(1)

def test_relay(locker_num, pin, active_high):
    """Prueba un relé individual"""
    print(f"\n{'='*50}")
    print(f"Probando Locker {locker_num} en pin {pin}")
    print(f"active_high={active_high}")
    print(f"{'='*50}")
    
    try:
        # Crear dispositivo
        relay = OutputDevice(pin, active_high=active_high)
        print(f"✅ Dispositivo creado en pin {pin}")
        
        # Test 1: Estado inicial
        print(f"\n[1] Estado inicial:")
        print(f"   relay.is_active = {relay.is_active}")
        print(f"   relay.is_lit = {relay.is_lit}")
        print(f"   (debería estar False/apagado)")
        
        # Test 2: Activar
        print(f"\n[2] ACTIVANDO relé...")
        relay.on()
        print(f"   relay.is_active = {relay.is_active}")
        print(f"   relay.is_lit = {relay.is_lit}")
        print(f"   👉 Verifica físicamente: ¿El LED del relé cambió?")
        input("   Presiona Enter cuando hayas verificado...")
        
        # Esperar
        print(f"\n[3] Esperando 2 segundos...")
        time.sleep(2)
        
        # Test 3: Desactivar
        print(f"\n[4] DESACTIVANDO relé...")
        relay.off()
        print(f"   relay.is_active = {relay.is_active}")
        print(f"   relay.is_lit = {relay.is_lit}")
        print(f"   👉 Verifica físicamente: ¿El LED del relé volvió al estado inicial?")
        input("   Presiona Enter cuando hayas verificado...")
        
        relay.close()
        print(f"\n✅ Test completado para Locker {locker_num}\n")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("PRUEBA DE GPIO Y RELÉS")
    print("="*60)
    
    print(f"\nConfiguración actual:")
    print(f"  habilitado: {GPIO_CONFIG['habilitado']}")
    print(f"  active_high: {GPIO_CONFIG['active_high']}")
    print(f"  pulso_duracion: {GPIO_CONFIG['pulso_duracion']}")
    print(f"  pines: {GPIO_CONFIG['pines']}")
    
    if not GPIO_CONFIG['habilitado']:
        print("\n❌ GPIO está deshabilitado en config.py")
        return
    
    # Probar cada relé
    pines = GPIO_CONFIG['pines']
    active_high = GPIO_CONFIG['active_high']
    
    for locker_num in sorted(pines.keys()):
        pin = pines[locker_num]
        success = test_relay(locker_num, pin, active_high)
        
        if not success:
            print(f"\n❌ Error probando Locker {locker_num}")
            print("Verifica:")
            print("  1. ¿El pin GPIO {pin} está correctamente conectado?")
            print("  2. ¿El relé está alimentado?")
            print("  3. ¿La conexión entre GPIO y relé es correcta?")
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
Si los relés NO se activan:
  1. Verifica que active_high sea el correcto para tu módulo de relé
     - Muchos módulos usan active_high=False (se activan con nivel BAJO)
     - Algunos usan active_high=True (se activan con nivel ALTO)
  
  2. Verifica las conexiones:
     - Pin GPIO → Pin de señal del relé (IN)
     - GND de Raspberry Pi → GND del relé
     - 5V de Raspberry Pi → VCC del relé
  
  3. Si el LED del relé está SIEMPRE encendido:
     - Probablemente active_high es el opuesto al esperado
     - Intenta cambiar active_high a True o False en config.py

Si los relés se activan correctamente:
  ✅ La configuración GPIO es correcta
  """)

if __name__ == '__main__':
    main()
