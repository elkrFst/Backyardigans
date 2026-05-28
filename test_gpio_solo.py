#!/usr/bin/env python3
"""
Script de prueba SOLO para GPIO sin interfaz gráfica
Útil para diagnóstico cuando la cámara no está disponible
"""
import sys
import time
sys.path.insert(0, '/home/backyardigans/Desktop/Backyardigans')

from config import GPIO_CONFIG
from core import LockerController

def main():
    print("\n" + "="*60)
    print("PRUEBA DE GPIO (sin interfaz gráfica)")
    print("="*60)
    
    print(f"\nConfigurando:")
    print(f"  habilitado: {GPIO_CONFIG['habilitado']}")
    print(f"  active_high: {GPIO_CONFIG['active_high']}")
    print(f"  pines: {GPIO_CONFIG['pines']}")
    
    # Crear controlador
    print("\nIniciando LockerController...")
    controller = LockerController()
    
    if not controller.activo:
        print("❌ Controlador no está activo")
        return
    
    print("\n" + "="*60)
    print("PRUEBAS DE RELÉS")
    print("="*60)
    
    for locker_num in sorted(GPIO_CONFIG['pines'].keys()):
        print(f"\n[TEST {locker_num}] Activando locker {locker_num}...")
        controller.activar_locker(locker_num)
        
        # Esperar un poco para que se complete la activación
        time.sleep(3)
        
        # Preguntar si continuar
        if locker_num < max(GPIO_CONFIG['pines'].keys()):
            resp = input(f"\n¿Continuar con el próximo relé? (s/n): ").strip().lower()
            if resp not in ('s', 'si', 'y', 'yes'):
                break
    
    print("\n" + "="*60)
    print("LIMPIEZA")
    print("="*60)
    
    controller.desactivar_todos()
    controller.cerrar()
    
    print("\n✅ Prueba completada\n")

if __name__ == '__main__':
    main()
