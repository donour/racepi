#include <Arduino.h>
#include "BluetoothSerial.h"
#include "rc_podium_protocol.h"

BluetoothSerial SerialBT;

#define SERIAL_CONSOLE_BAUDRATE (115200)
static const char BLUETOOTH_DEVICE_BROADCAST_NAME[] = "rc_test";

void rc_bt_task(void *arg) {
  rc_bt_reader(&SerialBT, &Serial);
}

void setup() {
  rc_handler_init();

  Serial.begin(SERIAL_CONSOLE_BAUDRATE);
  Serial.write(0); Serial.flush();
  Serial.print("*** Racecapture Test (platformIO) ***\n");

  SerialBT.begin(BLUETOOTH_DEVICE_BROADCAST_NAME); 
  SerialBT.write(0); SerialBT.flush();
  Serial.print("Bluetooth setup success!");

  xTaskCreate(
    rc_bt_task,
    "bt_reader_task",
    4096,
    NULL, 
    2, 
    NULL
  );
  
}

void loop() {
  delay(1000);
}

