#define trigPin 5
#define echoPin 6
#define ledPin 13
#define buzzerPin 10
#define vibrationPin 4

String input = "";
int prevDistance = 0;
unsigned long prevTime = 0;

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(vibrationPin, INPUT);
}

void loop() {
  int vibrationState = digitalRead(vibrationPin);

  // Read risk level sent from Python (HIGH, LOW, NONE)
  if (Serial.available()) {
    input = Serial.readStringUntil('\n');
    input.trim();
  }

  // If system is active (vibrating)
  if (vibrationState == HIGH) {
    long duration;
    int distance;

    // Measure distance using ultrasonic sensor
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    duration = pulseIn(echoPin, HIGH);
    distance = duration * 0.034 / 2;  // in cm

    unsigned long currentTime = millis();
    float timeDiff = (currentTime - prevTime) / 1000.0;  // in seconds
    float relativeSpeed = 0;
    if (timeDiff > 0) {
      relativeSpeed = (prevDistance - distance) / timeDiff;  // cm/s
    }

    prevDistance = distance;
    prevTime = currentTime;

    // Time-To-Collision (TTC) calculation
    float ttc = 1000;
    if (relativeSpeed > 0) {
      ttc = distance / relativeSpeed;
    }

    // Alert logic
    if (ttc < 2.0) {
      digitalWrite(ledPin, HIGH);
      digitalWrite(buzzerPin, HIGH);
    } else if (input == "HIGH") {
      digitalWrite(ledPin, HIGH);
      digitalWrite(buzzerPin, HIGH);
    } else if (input == "LOW" && distance > 0 && distance < 100 && relativeSpeed > 10) {
      digitalWrite(ledPin, HIGH);
      digitalWrite(buzzerPin, HIGH);
    } else if (input == "LOW") {
      digitalWrite(ledPin, HIGH);
      digitalWrite(buzzerPin, LOW);
    } else {
      digitalWrite(ledPin, LOW);
      digitalWrite(buzzerPin, LOW);
    }

    // Send formatted data back to Python GUI
    Serial.print("RISK:");
    Serial.print(input);
    Serial.print(",DIST:");
    Serial.print(distance);
    Serial.print(",STATUS:");
    Serial.println("ON");

  } else {
    // System inactive
    digitalWrite(ledPin, LOW);
    digitalWrite(buzzerPin, LOW);

    // Send "OFF" state
    Serial.println("RISK:NONE,DIST:0,STATUS:OFF");
  }

  delay(300);
}
