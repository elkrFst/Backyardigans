"""
Controlador para Arduino Nano con 4 LEDs y sonido PC
"""

import serial
import time
import winsound  # Solo Windows
# Para Linux/Mac: import os

class ArduinoLED:
    def __init__(self, puerto='COM4', baudrate=9600):
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
    
    def enviar_comando(self, led_num, accion):
        if not self.conectado or not self.serial:
            return False

        if led_num not in (1, 2, 3, 4):
            print(f"[ERROR] LED inválido: {led_num}")
            return False

        comando = f"L{led_num}{accion}\n".encode('ascii')
        try:
            self.serial.write(comando)
            self.serial.flush()
            print(f"[LED] Enviado comando: {comando.strip().decode()}")
            return True
        except Exception as e:
            print(f"[ERROR] No se pudo enviar comando al Arduino: {e}")
            return False

    def encender_led(self, led_num=1):
        resultado = self.enviar_comando(led_num, "ON")
        if resultado:
            self._reproducir_sonido()
        return resultado

    def _reproducir_sonido(self):
        """Reproduce sonido de confirmación por los altavoces de la PC"""
        try:
            # Windows: sonido de sistema "Asterisk"
            winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS)
            # Alternativa: beep personalizado
            # winsound.Beep(2000, 200)  # frecuencia 2000Hz, duración 200ms
        except:
            print("[SONIDO] No se pudo reproducir (puede que no sea Windows)")
    
    def apagar_led(self, led_num=1):
        return self.enviar_comando(led_num, "OFF")
    
    def parpadear_led(self, led_num=1, duracion=2, velocidad=0.3):
        if not self.conectado:
            return
        tiempo_inicio = time.time()
        while time.time() - tiempo_inicio < duracion:
            self.encender_led(led_num)
            time.sleep(velocidad)
            self.apagar_led(led_num)
            time.sleep(velocidad)
    
    def limpiar(self):
        if self.serial and self.serial.is_open:
            self.serial.close()


def obtener_arduino_led(puerto='COM4', baudrate=9600):
    return ArduinoLED(puerto, baudrate)