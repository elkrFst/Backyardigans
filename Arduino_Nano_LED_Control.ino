/*
  CÓDIGO PARA ARDUINO NANO - Control de 4 LEDs por Serial
  =========================================================
  
  INSTRUCCIONES DE INSTALACIÓN:
  1. Abre Arduino IDE
  2. Copia este código completo
  3. Selecciona Board: "Arduino Nano"
  4. Selecciona Processor: "ATmega328P"
  5. Selecciona el puerto COM donde está conectado el Arduino
  6. Carga el código
  
  COMANDOS:
  - L1ON  → Encender LED 1
  - L1OFF → Apagar LED 1
  - L2ON, L2OFF → LED 2
  - L3ON, L3OFF → LED 3
  - L4ON, L4OFF → LED 4
  
  CONEXIÓN DE LEDs:
  LED 1 → Pin A0 (con resistencia 470Ω)
  LED 2 → Pin A1 (con resistencia 470Ω)
  LED 3 → Pin A2 (con resistencia 470Ω)
  LED 4 → Pin A3 (con resistencia 470Ω)
  
  Todos los LEDs comparten GND común
*/

// Definición de pines para los 4 LEDs
const int LED_PINS[4] = {A0, A1, A2, A3};  // Pines analógicos como digitales

// Buffer para recibir comandos
String comando = "";

void setup() {
  // Inicializar comunicación serial (9600 baud)
  Serial.begin(9600);
  
  // Configurar todos los pines como salida
  for (int i = 0; i < 4; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);  // Apagar todos los LEDs al inicio
  }
  
  Serial.println("[OK] Arduino Nano iniciado - Esperando comandos...");
  Serial.println("[INFO] Comandos: L1ON, L1OFF, L2ON, L2OFF, L3ON, L3OFF, L4ON, L4OFF");
}

void loop() {
  // Leer comando del puerto serial
  if (Serial.available() > 0) {
    char caracter = Serial.read();
    
    // Construir comando hasta recibir salto de línea
    if (caracter == '\n') {
      comando.trim();  // Eliminar espacios en blanco
      
      if (comando.length() > 0) {
        procesarComando(comando);
      }
      
      comando = "";  // Limpiar buffer
    } else {
      comando += caracter;
    }
  }
}

void procesarComando(String cmd) {
  cmd.toUpperCase();  // Convertir a mayúsculas
  
  // Verificar formato: L[1-4]ON o L[1-4]OFF
  if (cmd.length() >= 4) {
    char led_char = cmd[1];  // Obtener número de LED (1-4)
    String accion = cmd.substring(2);  // Obtener ON/OFF
    
    // Validar que sea un número de LED válido
    if (led_char >= '1' && led_char <= '4') {
      int led_num = led_char - '0';  // Convertir char a int
      int pin = LED_PINS[led_num - 1];  // Array está en índice 0-3
      
      // Ejecutar acción
      if (accion == "ON") {
        digitalWrite(pin, HIGH);
        Serial.print("[LED] L");
        Serial.print(led_num);
        Serial.println(" ENCENDIDO");
      }
      else if (accion == "OFF") {
        digitalWrite(pin, LOW);
        Serial.print("[LED] L");
        Serial.print(led_num);
        Serial.println(" APAGADO");
      }
      else {
        Serial.print("[ERROR] Acción desconocida: ");
        Serial.println(accion);
      }
    }
    else {
      Serial.print("[ERROR] Número de LED inválido: ");
      Serial.println(led_char);
    }
  }
  else {
    Serial.print("[ERROR] Comando inválido: ");
    Serial.println(cmd);
    Serial.println("[INFO] Formato correcto: L[1-4]ON o L[1-4]OFF");
  }
}

/*
  SOLUCIÓN DE PROBLEMAS:
  
  ❌ Arduino no responde:
     - Verifica que el cable USB esté conectado
     - Comprueba que hayas seleccionado el puerto correcto en Arduino IDE
     - Intenta cargar un sketch simple (parpadeo) primero
  
  ❌ LEDs no se encienden:
     - Verifica la conexión de los LEDs (largo = +, corto = -)
     - Comprueba que las resistencias estén conectadas
     - Verifica con un tester que los LEDs funcionen
  
  ❌ Serial no conecta:
     - Instala los drivers CH340 (si tu Arduino los necesita)
     - En Ubuntu/Linux: sudo apt-get install arduino
     - En Raspberry Pi: sudo apt-get install serial
  
  ❌ Comandos no funcionan:
     - Abre Serial Monitor en Arduino IDE (9600 baud)
     - Prueba escribir "L1ON" manualmente
     - Verifica que el formato sea exacto (sin espacios extra)
*/
