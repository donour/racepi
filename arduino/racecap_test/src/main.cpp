#include <Arduino.h>
#include "BluetoothSerial.h"
#include "rc_podium_protocol.h"

BluetoothSerial SerialBT;

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth Classic is not enabled for this build. 
#endif

#define SERIAL_CONSOLE_BAUDRATE (115200)
static const char BLUETOOTH_DEVICE_BROADCAST_NAME[] = "rc_test";

void bt_callback(esp_spp_cb_event_t event, esp_spp_cb_param_t *param){
  if (event == ESP_SPP_WRITE_EVT) {
    return;
  }
  if(event == ESP_SPP_CLOSE_EVT ){
    // This is a little heavy handed, but I've had trouble
    // initiating subsequent connections after SPP close, so
    // I just reboot the module.
    ESP.restart();    
  }
  if (event == ESP_SPP_SRV_OPEN_EVT) {
    return;
  
  }
  if (event == ESP_SPP_OPEN_EVT) {
    Serial.println("BT open");
    SerialBT.write((uint8_t *)meta_mesg, strlen(meta_mesg));
  } else{
    Serial.printf("BT evt %d\n",event);

  }
}

void rc_bt_task(void *arg) {
  rc_bt_reader(&SerialBT, &Serial);
}

void setup() {
  rc_handler_init();

  Serial.begin(SERIAL_CONSOLE_BAUDRATE);
  Serial.write(0); Serial.flush();
  Serial.print("*** Racecapture Test (platformIO) ***\n");

  //SerialBT.register_callback(bt_callback);
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
  // bool send_meta = false;
  // while (SerialBT.available()) {
  //   char c = SerialBT.read();
  //   Serial.write(c);
  //   send_meta = true;
  // }
  // if (send_meta) {
  //   send_meta_mesg();
  // }

  // put your main code here, to run repeatedly:
  delay(1000/50);
  // SerialBT.write((uint8_t *)meta_mesg, strlen(meta_mesg));
  // SerialBT.write((uint8_t *)data_mesg, strlen(data_mesg));

}

