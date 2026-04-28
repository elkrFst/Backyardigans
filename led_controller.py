"""Control de LEDs para Raspberry Pi 5 - Simulación de lockers"""
import time
import platform

# Detectar plataforma e importar las librerías apropiadas
ES_RASPBERRY = platform.machine().startswith('arm')

if ES_RASPBERRY:
    try:
        import RPi.GPIO as GPIO
        LEDS_DISPONIBLES = True
    except ImportError:
        print("[WARNING] RPi.GPIO no disponible, usando modo simulación")
        LEDS_DISPONIBLES = False
else:
    # En desarrollo (Windows), simular sin hardware
    LEDS_DISPONIBLES = False
    print("[INFO] No es Raspberry Pi, usando modo simulación de LEDs")


class LEDController:
    """Control de 4 LEDs para simular los 4 lockers"""
    
    # Pines GPIO de Raspberry Pi 5 asignados a cada locker
    PINES_LEDS = {
        1: 17,   # Locker 1 - GPIO 17 (pin 11)
        2: 27,   # Locker 2 - GPIO 27 (pin 13)
        3: 22,   # Locker 3 - GPIO 22 (pin 15)
        4: 23    # Locker 4 - GPIO 23 (pin 16)
    }
    
    def __init__(self):
        """Inicializar controlador de LEDs"""
        self.leds_disponibles = LEDS_DISPONIBLES
        self.leds_activos = {}  # Rastrear qué LEDs están encendidos
        
        if self.leds_disponibles:
            try:
                # Usar numeración de pines GPIO (no física)
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                # Configurar todos los pines como salida
                for locker_num, pin in self.PINES_LEDS.items():
                    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
                    self.leds_activos[locker_num] = False
                    print(f"[OK] LED Locker {locker_num} configurado en GPIO {pin}")
                    
            except Exception as e:
                print(f"[ERROR] No se pudo inicializar GPIO: {e}")
                self.leds_disponibles = False
        else:
            # Modo simulación
            for locker_num in self.PINES_LEDS.keys():
                self.leds_activos[locker_num] = False
                print(f"[SIMULACIÓN] LED Locker {locker_num} en modo simulación")
    
    def encender_led(self, locker_num):
        """Encender LED del locker especificado"""
        if locker_num not in self.PINES_LEDS:
            print(f"[ERROR] Locker {locker_num} inválido (1-4)")
            return False
        
        if self.leds_disponibles:
            try:
                pin = self.PINES_LEDS[locker_num]
                GPIO.output(pin, GPIO.HIGH)
                self.leds_activos[locker_num] = True
                print(f"[GPIO] LED Locker {locker_num} (GPIO {pin}) ENCENDIDO")
                return True
            except Exception as e:
                print(f"[ERROR] No se pudo encender LED {locker_num}: {e}")
                return False
        else:
            # Simulación
            self.leds_activos[locker_num] = True
            print(f"[SIMULACIÓN] 💡 LED Locker {locker_num} ENCENDIDO")
            return True
    
    def apagar_led(self, locker_num):
        """Apagar LED del locker especificado"""
        if locker_num not in self.PINES_LEDS:
            print(f"[ERROR] Locker {locker_num} inválido (1-4)")
            return False
        
        if self.leds_disponibles:
            try:
                pin = self.PINES_LEDS[locker_num]
                GPIO.output(pin, GPIO.LOW)
                self.leds_activos[locker_num] = False
                print(f"[GPIO] LED Locker {locker_num} (GPIO {pin}) APAGADO")
                return True
            except Exception as e:
                print(f"[ERROR] No se pudo apagar LED {locker_num}: {e}")
                return False
        else:
            # Simulación
            self.leds_activos[locker_num] = False
            print(f"[SIMULACIÓN] 🔴 LED Locker {locker_num} APAGADO")
            return True
    
    def parpadear_led(self, locker_num, duracion=2, velocidad=0.3):
        """Parpadear LED (suceso importante: registro o acceso)"""
        if locker_num not in self.PINES_LEDS:
            return False
        
        print(f"[EVENTO] Parpadeando LED Locker {locker_num}")
        inicio = time.time()
        
        while time.time() - inicio < duracion:
            self.encender_led(locker_num)
            time.sleep(velocidad)
            self.apagar_led(locker_num)
            time.sleep(velocidad)
        
        # Dejar apagado al final
        self.apagar_led(locker_num)
        return True
    
    def encender_todos(self):
        """Encender todos los LEDs (prueba de hardware)"""
        print("[TEST] Encendiendo todos los LEDs...")
        for locker_num in self.PINES_LEDS.keys():
            self.encender_led(locker_num)
    
    def apagar_todos(self):
        """Apagar todos los LEDs"""
        print("[TEST] Apagando todos los LEDs...")
        for locker_num in self.PINES_LEDS.keys():
            self.apagar_led(locker_num)
    
    def prueba_todos(self):
        """Prueba secuencial de todos los LEDs (útil para verificación)"""
        print("[TEST] Iniciando prueba de LEDs...")
        for locker_num in [1, 2, 3, 4]:
            self.encender_led(locker_num)
            time.sleep(1)
            self.apagar_led(locker_num)
            time.sleep(0.5)
        print("[TEST] Prueba completada")
    
    def estado_leds(self):
        """Retornar estado actual de todos los LEDs"""
        return self.leds_activos.copy()
    
    def limpiar(self):
        """Limpiar y apagar todo (llamar al cerrar la aplicación)"""
        print("[CLEANUP] Apagando LEDs y liberando GPIO...")
        self.apagar_todos()
        
        if self.leds_disponibles:
            try:
                GPIO.cleanup()
                print("[OK] GPIO limpiado correctamente")
            except Exception as e:
                print(f"[WARNING] Error al limpiar GPIO: {e}")


# Crear instancia global
led_controller = None

def inicializar_leds():
    """Inicializar el controlador de LEDs globalmente"""
    global led_controller
    if led_controller is None:
        led_controller = LEDController()
    return led_controller

def obtener_leds():
    """Obtener instancia del controlador de LEDs"""
    global led_controller
    if led_controller is None:
        led_controller = LEDController()
    return led_controller
