// 計測まわり
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include "Adafruit_BME680.h"
// データ送信まわり
#include <Bridge.h>
#include <HttpClient.h>
#include <Arduino_JSON.h>

#define SEALEVELPRESSURE_HPA (1008.2)
#define HTTP_URL "your url"

Adafruit_BME680 bme; // I2C
const int STATUS_LED = 13;

void setup() {
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);
  Bridge.begin();
  digitalWrite(STATUS_LED, HIGH);
  delay(3000);

  if (!bme.begin()) {
    digitalWrite(STATUS_LED, LOW);
    Serial.println("Could not find a valid BME680 sensor, check wiring!");
    while (1);
  }

  // Set up oversampling and filter initialization
  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(320, 150); // 320*C for 150 ms
}

void exec() {
  if (! bme.performReading()) {
    Serial.println("Failed to perform reading :(");
    for(int i = 0; i < 10; i++) {
       digitalWrite(STATUS_LED, HIGH);
       delay(1000);
       digitalWrite(STATUS_LED, LOW);
       delay(1000);
    }
    return;
  }

  // データ作成
  JSONVar json;
  json["temperature"] = bme.temperature;
  json["pressure"] = bme.pressure / 100.0;
  json["humidity"] = bme.humidity;
  json["gas_resistance"] = bme.gas_resistance / 1000.0;
  json["elevation"] = bme.readAltitude(SEALEVELPRESSURE_HPA);

  String jsonStr = JSON.stringify(json);
  int str_len = jsonStr.length() + 1; 
  char char_array[str_len];
  jsonStr.toCharArray(char_array, str_len); 

  // HTTP通信
  HttpClient client;
  client.noCheckSSL();
  client.setHeader("Content-Type: application/json");

  client.post(HTTP_URL, char_array);
  String payload = client.readString();
  Serial.println(payload);

  client.close();
}

void loop() {
  exec();
  delay(5 * 60 * 1000UL); // 5分(ms)
}
