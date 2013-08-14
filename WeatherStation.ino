void setup() {
  Serial.begin(9600);
  Serial.println("Starting up.");

  bmp085_init();
}

void loop() {
  Serial.print((double) bmp085_get_temperature() / 10);
  Serial.print(" C, ");
  
  Serial.print((double) bmp085_get_pressure() / 100);
  Serial.println(" hPa");

  delay(1000);
}
