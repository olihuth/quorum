#include <LiquidCrystal.h>

// LCD configuration (RS=12, E=11, D4=5, D5=4, D6=6, D7=2)
LiquidCrystal lcd(12, 11, 5, 4, 6, 2);

// Sensors
const int pingPin = 13;
const int ldrPin = A0;

// LCD backlight PWM
const int backlightPin = 3;

// Voting buttons
const int upvotePin = 7;
const int downvotePin = 8;

// Voting counters
int upvotes = 0;
int downvotes = 0;

// Button states
int lastUpState = HIGH;
int lastDownState = HIGH;

unsigned long lastUpPress = 0;
unsigned long lastDownPress = 0;

const unsigned long debounceDelay = 200;
const int PRESENCE_THRESHOLD_CM = 100;
const char* TOTEM_ID = "totem-metro-se-01";
const int TARGET_BILL_ID = 1;
const char* TARGET_BILL_LABEL = "PL 2338/2023";

// Sensor readings
long duration = 0;
int distance = 0;
int lightLevel = 0;
int brightness = 0;

// Read distance in centimeters from a 3-pin PING))) ultrasonic sensor.
int readUltrasonicDistanceCm() {
  pinMode(pingPin, OUTPUT);
  digitalWrite(pingPin, LOW);
  delayMicroseconds(2);
  digitalWrite(pingPin, HIGH);
  delayMicroseconds(5);
  digitalWrite(pingPin, LOW);

  pinMode(pingPin, INPUT);
  duration = pulseIn(pingPin, HIGH, 30000);
  if (duration == 0) {
    return 0;
  }
  return (int)(duration / 58);
}

// Map LDR reading (0..1023) to PWM backlight duty cycle when citizen is present.
int computeAdaptiveBacklight(int rawLdr, bool citizenPresent) {
  if (!citizenPresent) {
    return 30;  // Standby energy-saving dim mode
  }
  return constrain(map(rawLdr, 0, 1023, 80, 255), 80, 255);
}

// Print an ASCII-safe 16-character row (avoids HD44780 glyph corruption).
void printPaddedRow(int row, const String& text) {
  lcd.setCursor(0, row);
  String out = text;
  if (out.length() > 16) {
    out = out.substring(0, 16);
  }
  while (out.length() < 16) {
    out += ' ';
  }
  lcd.print(out);
}

void renderStandbyScreen() {
  printPaddedRow(0, "     Quorum     ");
  printPaddedRow(1, "Aproxime p/votar");
}

void renderVotingScreen() {
  String line2 = "Sim:" + String(upvotes) + "  Nao:" + String(downvotes);
  printPaddedRow(0, String(TARGET_BILL_LABEL));
  printPaddedRow(1, line2);
}

void renderVoteConfirmation() {
  printPaddedRow(0, "Voto registrado!");
  printPaddedRow(1, "Obrigado cidadao");
}

void emitVoteTelemetry(const char* choice) {
  Serial.print("{\"event\":\"vote\",\"totem_id\":\"");
  Serial.print(TOTEM_ID);
  Serial.print("\",\"bill_id\":");
  Serial.print(TARGET_BILL_ID);
  Serial.print(",\"choice\":\"");
  Serial.print(choice);
  Serial.print("\",\"distance_cm\":");
  Serial.print(distance);
  Serial.print(",\"light_level\":");
  Serial.print(lightLevel);
  Serial.print(",\"backlight_pwm\":");
  Serial.print(brightness);
  Serial.print(",\"upvotes\":");
  Serial.print(upvotes);
  Serial.print(",\"downvotes\":");
  Serial.print(downvotes);
  Serial.println("}");
}

void setup() {
  pinMode(backlightPin, OUTPUT);

  pinMode(upvotePin, INPUT_PULLUP);
  pinMode(downvotePin, INPUT_PULLUP);

  Serial.begin(9600);

  lcd.begin(16, 2);

  // Initial welcome
  lcd.setCursor(0, 0);
  lcd.print("     Quorum");
  printPaddedRow(1, "Inicializando...");
  analogWrite(backlightPin, 128);
  delay(800);
}

void loop() {
  distance = readUltrasonicDistanceCm();
  lightLevel = analogRead(ldrPin);
  bool citizenPresent = (distance > 0 && distance <= PRESENCE_THRESHOLD_CM);

  brightness = computeAdaptiveBacklight(lightLevel, citizenPresent);
  analogWrite(backlightPin, brightness);

  int currentUpState = digitalRead(upvotePin);
  int currentDownState = digitalRead(downvotePin);
  unsigned long now = millis();

  if (!citizenPresent) {
    renderStandbyScreen();
    lastUpState = currentUpState;
    lastDownState = currentDownState;
    delay(150);
    return;
  }

  renderVotingScreen();

  if (lastUpState == HIGH && currentUpState == LOW && (now - lastUpPress) > debounceDelay) {
    lastUpPress = now;
    upvotes++;
    emitVoteTelemetry("favor");
    renderVoteConfirmation();
    delay(1200);
  } else if (lastDownState == HIGH && currentDownState == LOW && (now - lastDownPress) > debounceDelay) {
    lastDownPress = now;
    downvotes++;
    emitVoteTelemetry("against");
    renderVoteConfirmation();
    delay(1200);
  }

  lastUpState = currentUpState;
  lastDownState = currentDownState;
  delay(100);
}
