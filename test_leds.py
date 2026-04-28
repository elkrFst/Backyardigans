#!/usr/bin/env python3
"""
Script de prueba para los 4 LEDs
Verifica que la conexión de hardware sea correcta
Ejecutar ANTES de correr la aplicación principal
"""

import time
import sys

try:
    from led_controller import LEDController
except ImportError:
    print("❌ Error: No se encontró 'led_controller.py'")
    print("Asegúrate de que está en la misma carpeta que este script")
    sys.exit(1)


def esperar_tecla():
    """Pausa y espera que el usuario presione Enter"""
    input("\nPresiona ENTER para continuar...")


def prueba_individual():
    """Prueba cada LED de forma individual"""
    print("\n" + "="*70)
    print("🧪 PRUEBA INDIVIDUAL DE LEDS")
    print("="*70)
    
    leds = LEDController()
    
    for locker_num in [1, 2, 3, 4]:
        print(f"\n⏳ Probando LED del Locker {locker_num}...")
        print(f"   GPIO: {leds.PINES_LEDS[locker_num]} | Pin Físico: {locker_num*2 + 9}")
        
        leds.encender_led(locker_num)
        print(f"   ✓ LED encendido. Verifica visualmente que el LED {locker_num} está BRILLANDO")
        
        time.sleep(2)
        
        leds.apagar_led(locker_num)
        print(f"   ✓ LED apagado")
        
        esperar_tecla()
    
    leds.limpiar()
    print("\n✅ Prueba individual completada")


def prueba_secuencial():
    """Prueba secuencial: todos los LEDs se encienden uno por uno"""
    print("\n" + "="*70)
    print("🎬 PRUEBA SECUENCIAL")
    print("="*70)
    
    leds = LEDController()
    
    print("\n⏳ Encendiendo LEDs del 1 al 4 secuencialmente...")
    
    for locker_num in [1, 2, 3, 4]:
        leds.encender_led(locker_num)
        time.sleep(0.5)
    
    print("✓ Todos los LEDs deberían estar ENCENDIDOS")
    esperar_tecla()
    
    print("\n⏳ Apagando LEDs del 1 al 4 secuencialmente...")
    
    for locker_num in [1, 2, 3, 4]:
        leds.apagar_led(locker_num)
        time.sleep(0.5)
    
    print("✓ Todos los LEDs deberían estar APAGADOS")
    
    leds.limpiar()
    print("\n✅ Prueba secuencial completada")


def prueba_parpadeo():
    """Prueba de parpadeo (evento de registro)"""
    print("\n" + "="*70)
    print("💫 PRUEBA DE PARPADEO (Simulación de Registro)")
    print("="*70)
    
    leds = LEDController()
    
    for locker_num in [1, 2, 3, 4]:
        print(f"\n⏳ LED Locker {locker_num} parpadeando (como si se registrara)...")
        leds.parpadear_led(locker_num, duracion=2, velocidad=0.2)
        print(f"✓ Parpadeo completado")
    
    leds.limpiar()
    print("\n✅ Prueba de parpadeo completada")


def prueba_duracion():
    """Prueba de duración (evento de apertura)"""
    print("\n" + "="*70)
    print("⏱️  PRUEBA DE DURACIÓN (Simulación de Apertura)")
    print("="*70)
    
    leds = LEDController()
    
    for locker_num in [1, 2, 3, 4]:
        print(f"\n⏳ LED Locker {locker_num} encendido por 3 segundos (como si se abriera)...")
        leds.encender_led(locker_num)
        
        # Simular apertura de locker (LED encendido 3 segundos)
        for i in range(3, 0, -1):
            print(f"   ⏱️  {i} segundos...", end='\r')
            time.sleep(1)
        
        leds.apagar_led(locker_num)
        print(f"✓ LED apagado después de 3 segundos")
    
    leds.limpiar()
    print("\n✅ Prueba de duración completada")


def menu_principal():
    """Menú principal de pruebas"""
    print("\n" + "="*70)
    print("🧪 PRUEBAS DE HARDWARE - SISTEMA DE 4 LEDS")
    print("="*70)
    print("\nEste script verifica que los LEDs estén conectados correctamente")
    print("IMPORTANTE: Debes poder VER los LEDs parpadeando/encendidos")
    print("\nOpciones disponibles:")
    print("  1 - Prueba Individual (LED por LED)")
    print("  2 - Prueba Secuencial (1→2→3→4)")
    print("  3 - Prueba de Parpadeo (simulación de registro)")
    print("  4 - Prueba de Duración (simulación de apertura)")
    print("  5 - Prueba Completa (todas las anteriores)")
    print("  0 - Salir")
    
    while True:
        try:
            opcion = input("\nSelecciona una opción (0-5): ").strip()
            
            if opcion == "1":
                prueba_individual()
            elif opcion == "2":
                prueba_secuencial()
            elif opcion == "3":
                prueba_parpadeo()
            elif opcion == "4":
                prueba_duracion()
            elif opcion == "5":
                prueba_individual()
                prueba_secuencial()
                prueba_parpadeo()
                prueba_duracion()
            elif opcion == "0":
                print("\n👋 Saliendo...")
                break
            else:
                print("❌ Opción inválida. Intenta de nuevo.")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Prueba interrumpida por el usuario")
            break
        except Exception as e:
            print(f"\n❌ Error durante la prueba: {e}")
            print("Verifica que los LEDs estén conectados correctamente")


if __name__ == "__main__":
    try:
        menu_principal()
        print("\n✅ Todas las pruebas completadas")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        print("\nSoluciones:")
        print("  • Verifica que led_controller.py está en la misma carpeta")
        print("  • Asegúrate de estar en una Raspberry Pi (o que use simulación)")
        print("  • Verifica que los LEDs estén bien conectados")
        sys.exit(1)
