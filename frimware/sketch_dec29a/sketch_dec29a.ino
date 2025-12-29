// Motor Shield L298P — стандартные выводы (можно изменить, если на твоем шилде по-другому)
const int ENA = 5; // PWM мотор A
const int IN1 = 4;

const int ENB = 6; // PWM мотор B
const int IN3 = 7;

void setup() {
  Serial.begin(9600);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);

  stopMotors();
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');

    int comma = line.indexOf(',');
    if (comma > 0) {
      int leftPWM  = line.substring(0, comma).toInt();
      int rightPWM = line.substring(comma + 1).toInt();

      driveMotors(leftPWM, rightPWM);
    }
  }
}

void driveMotors(int leftPWM, int rightPWM) {
  // мотор A (левый)
  if (leftPWM >= 0) {
    digitalWrite(IN1, HIGH);
    analogWrite(ENA, leftPWM);
  } else {
    digitalWrite(IN1, LOW);
    analogWrite(ENA, -leftPWM);
  }

  // мотор B (правый)
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
