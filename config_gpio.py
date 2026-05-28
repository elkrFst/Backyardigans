#!/usr/bin/env python3
"""
Helper script para cambiar configuración de GPIO sin editar archivos
"""
import os
import sys

config_file = '/home/backyardigans/Desktop/Backyardigans/config.py'

def read_config():
    """Lee el archivo config.py"""
    with open(config_file, 'r') as f:
        return f.read()

def write_config(content):
    """Escribe el archivo config.py"""
    with open(config_file, 'w') as f:
        f.write(content)

def get_active_high():
    """Obtiene el valor actual de active_high"""
    content = read_config()
    if "'active_high': True" in content:
        return True
    elif "'active_high': False" in content:
        return False
    return None

def set_active_high(value):
    """Cambia el valor de active_high"""
    content = read_config()
    
    if value:
        # Cambiar a True
        content = content.replace("'active_high': False", "'active_high': True")
        print("✅ active_high cambiado a True")
    else:
        # Cambiar a False
        content = content.replace("'active_high': True", "'active_high': False")
        print("✅ active_high cambiado a False")
    
    write_config(content)

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("CONFIGURADOR RÁPIDO DE GPIO")
    print("="*60)
    
    current = get_active_high()
    
    if current is None:
        print("\n❌ No se pudo determinar el valor actual de active_high")
        sys.exit(1)
    
    print(f"\nValor actual: active_high = {current}")
    print("\nOpciones:")
    print("  1. Cambiar a True")
    print("  2. Cambiar a False")
    print("  3. Salir sin cambios")
    
    choice = input("\nElige una opción (1-3): ").strip()
    
    if choice == '1':
        if current != True:
            set_active_high(True)
        else:
            print("⚠️  Ya está en True")
    elif choice == '2':
        if current != False:
            set_active_high(False)
        else:
            print("⚠️  Ya está en False")
    elif choice == '3':
        print("Sin cambios")
    else:
        print("❌ Opción inválida")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("INSTRUCCIONES:")
    print("="*60)
    print("""
1. Inicia la app:
   python3 main.py

2. Prueba a abrir un locker desde la interfaz

3. Observa el LED del relé:
   - ¿Se enciende/apaga correctamente? → ✅ Config correcta
   - ¿Hace lo opuesto? → Vuelve a cambiar active_high
   - ¿No cambia? → Problema de conexión física
    """)
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
