#include <Wire.h>

/**
 * Datasheet defines addressess 0xEF and 0xEE, but only the
 * lower 7 bits are used, which results in 0x77.
 */
static const byte BMP085_I2C_ADDRESS = 0x77;
static const byte BMP085_CTRL_REGISTER = 0xF4;
static const byte BMP085_AD_RESULT = 0xF6;
static const byte BMP085_START_UT = 0x2E;
static const byte BMP085_START_UP = 0x34;
static const byte OVERSAMPLING = 3;

/**
 * Calibration coefficients set in factory.
 */
short CALIB_AC1;
short CALIB_AC2;
short CALIB_AC3;
unsigned short CALIB_AC4;
unsigned short CALIB_AC5;
unsigned short CALIB_AC6;
short CALIB_B1;
short CALIB_B2;
short CALIB_MB;
short CALIB_MC;
short CALIB_MD;
long CALC_B5;

void bmp085_init() {
  Wire.begin();

  Serial.println("Reading calibration coefficients.");
  CALIB_AC1 = bmp085_read_short(0xAA);
  CALIB_AC2 = bmp085_read_short(0xAC);
  CALIB_AC3 = bmp085_read_short(0xAE);
  CALIB_AC4 = bmp085_read_short(0xB0);
  CALIB_AC5 = bmp085_read_short(0xB2);
  CALIB_AC6 = bmp085_read_short(0xB4);
  CALIB_B1 = bmp085_read_short(0xB6);
  CALIB_B2 = bmp085_read_short(0xB8);
  CALIB_MB = bmp085_read_short(0xBA);
  CALIB_MC = bmp085_read_short(0xBC);
  CALIB_MD = bmp085_read_short(0xBE);
  /*Serial.println(CALIB_AC1, HEX);
  Serial.println(CALIB_AC2, HEX);
  Serial.println(CALIB_AC3, HEX);
  Serial.println(CALIB_AC4, HEX);
  Serial.println(CALIB_AC5, HEX);
  Serial.println(CALIB_AC6, HEX);
  Serial.println(CALIB_B1, HEX);
  Serial.println(CALIB_B2, HEX);
  Serial.println(CALIB_MB, HEX);
  Serial.println(CALIB_MC, HEX);
  Serial.println(CALIB_MD, HEX);*/
}

void bmp085_request_read(byte address, size_t len) {
  Wire.beginTransmission(BMP085_I2C_ADDRESS);
  Wire.write(address);
  Wire.endTransmission();

  Wire.requestFrom(BMP085_I2C_ADDRESS, len);
  while (Wire.available() < len) {
    // Busy wait
  } 
}

byte bmp085_read_byte(byte address) {
  bmp085_request_read(address, 1);
  return Wire.read();
}

short bmp085_read_short(byte address) {
  bmp085_request_read(address, 2);
  return (short) Wire.read() << 8 | Wire.read();
}

unsigned long bmp085_read_long(byte address) {
  bmp085_request_read(address, 3);
  return (unsigned long) Wire.read() << 16 |  (unsigned long) Wire.read() << 8 | Wire.read();
}

long bmp085_get_ut(void) {
  Wire.beginTransmission(BMP085_I2C_ADDRESS);
  Wire.write(BMP085_CTRL_REGISTER);
  Wire.write(BMP085_START_UT);
  Wire.endTransmission();
  delay(5);
  return bmp085_read_short(BMP085_AD_RESULT);
}

unsigned long bmp085_get_up(void) {
  Wire.beginTransmission(BMP085_I2C_ADDRESS);
  Wire.write(BMP085_CTRL_REGISTER);
  Wire.write(BMP085_START_UP + (OVERSAMPLING << 6));
  Wire.endTransmission();
  delay(26); // IMPROVE
  unsigned long up = bmp085_read_long(BMP085_AD_RESULT);
  return up >> (8 - OVERSAMPLING);
}

long bmp085_get_temperature(void) {
  long ut = bmp085_get_ut();
  long x1 = ((ut - CALIB_AC6) * CALIB_AC5) >> 15;
  long x2 = ((long) CALIB_MC << 11) / (x1 + CALIB_MD);
  CALC_B5 = x1 + x2;
  return (CALC_B5 + 8) >> 4;
}

long bmp085_get_pressure(void) {
  long up = bmp085_get_up();

  long b6 = CALC_B5 - 4000;  

  long x1 = (CALIB_B2 * ((b6 * b6) >> 12)) >> 11;
  long x2 = ((long) CALIB_AC2 * b6) >> 11;
  long x3 = x1 + x2;
  long b3 = ((((long) CALIB_AC1 * 4 + x3) << OVERSAMPLING) + 2) / 4;

  x1 = (CALIB_AC3 * b6) >> 13;
  x2 = (CALIB_B1 * ((b6 ^ 2) >> 12)) >> 16;
  x3 = ((x1 + x2) + 2) >> 2;  
  unsigned long b4 = (CALIB_AC4 * (unsigned long)(x3 + 32768)) >> 15;

  unsigned long b7 = ((unsigned long) up - b3) * (50000 >> OVERSAMPLING);
  long p = 0;
  if (b7 < 0x80000000) {
    p = b7 * 2 / b4;
  } else {
    p = b7 / b4 * 2;
  }

  x1 = (p >> 8) * (p >> 8);
  x1 = (x1 * 3038) >> 16;
  x2 = (-7357 * p) >> 16;
  return p + ((x1 + x2 + 3791) >> 4);
}
