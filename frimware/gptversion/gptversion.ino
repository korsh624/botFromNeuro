// Motor Shield L298P
const int ENA = 5; 
const int IN1 = 4;

const int ENB = 6; 
const int IN3 = 7;

#define BUFFER_SIZE 20
char inputBuffer[BUFFER_SIZE];
byte bufferIndex = 0;

unsigned long lastPacketTime = 0;
const unsigned long timeoutMs = 200; // если 200мс нет команд — стоп

void setup() {
  Serial.begin(115200);   // увеличили скорость!
  
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);

  stopMotors();
}

void loop() {
  readSerial();

  // failsafe
  if (millis() - lastPacketTime > timeoutMs) {
    stopMotors();
  }
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      inputBuffer[bufferIndex] = '\0';
      parseCommand(inputBuffer);
      bufferIndex = 0;
      lastPacketTime = millis();
    } 
    else {
      if (bufferIndex < BUFFER_SIZE - 1) {
        inputBuffer[bufferIndex++] = c;
      }
    }
  }
}

void parseCommand(char* data) {
  int leftPWM, rightPWM;
  if (sscanf(data, "%d,%d", &leftPWM, &rightPWM) == 2) {
    driveMotors(leftPWM, rightPWM);
  }
}

void driveMotors(int leftPWM, int rightPWM) {

  leftPWM  = constrain(leftPWM,  -255, 255);
  rightPWM = constrain(rightPWM, -255, 255);

  // Левый мотор
  if (leftPWM >= 0) {
    digitalWrite(IN1, HIGH);
    analogWrite(ENA, leftPWM);
  } else {
    digitalWrite(IN1, LOW);
    analogWrite(ENA, -leftPWM);
  }

  // Правый мотор
  if (rightPWM >= 0) {
    digitalWrite(IN3, HIGH);
    analogWrite(ENB, rightPWM);
  } else {
    digitalWrite(IN3, LOW);
    analogWrite(ENB, -rightPWM);
  }
}

void stopMotors() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}
