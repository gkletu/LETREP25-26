int piezoPin = 2;   // ADC1 channel
int sensorValue = 0;


void setup() {
  Serial.begin(115200);

}

void loop() {
  sensorValue = analogRead(piezoPin);
  Serial.println(sensorValue);
}
