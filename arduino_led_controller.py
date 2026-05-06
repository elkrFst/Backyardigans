"""
Controlador para Arduino Nano con 1 LED + sonido PC
"""

import serial
import time
import threading
import winsound  # Solo Windows
# Para Linux/Mac: import os

class ArduinoLED:
    def __init__(self, puerto='COM6', baudrate=9600):
        self.puerto = puerto
        self.baudrate = baudrate
        self.serial = None
        self.conectado = False
        self._intentar_conectar()
    
    def _intentar_conectar(self):
        try:
            self.serial = serial.Serial(self.puerto, self.baudrate, timeout=1)
            time.sleep(2)
            self.conectado = True
            print(f"[OK] Conectado a Arduino en {self.puerto}")
        except Exception as e:
            self.conectado = False
            print(f"[ERROR] No se pudo conectar a Arduino: {e}")
    
    def encender_led(self):
        if self.conectado and self.serial:
            try:
                self.serial.write(b'CARAS\n')
                self.serial.flush()
                print("[LED] ENCENDIDO")
                # Reproducir sonido de confirmación (Windows)
                self._reproducir_sonido()
                return True
            except:
                return False
        return False
    
    def _reproducir_sonido(self):
        """Reproduce sonido de confirmación por los altavoces de la PC"""
        try:
            # Windows: sonido de sistema "Asterisk"
            winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS)
            # Alternativa: beep personalizado
            # winsound.Beep(2000, 200)  # frecuencia 2000Hz, duración 200ms
        except:
            print("[SONIDO] No se pudo reproducir (puede que no sea Windows)")
    
    def apagar_led(self):
        if self.conectado and self.serial:
            try:
                self.serial.write(b'NO\n')
                self.serial.flush()
                print("[LED] APAGADO")
                return True
            except:
                return False
        return False
    
    def parpadear_led(self, duracion=2, velocidad=0.3):
        if not self.conectado:
            return
        tiempo_inicio = time.time()
        while time.time() - tiempo_inicio < duracion:
            self.encender_led()
            time.sleep(velocidad)
            self.apagar_led()
            time.sleep(velocidad)
    
    def limpiar(self):
        if self.serial and self.serial.is_open:
            self.apagar_led()
            self.serial.close()


def obtener_arduino_led(puerto='COM6'):
    return ArduinoLED(puerto)