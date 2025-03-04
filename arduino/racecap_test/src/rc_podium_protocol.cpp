#include <Arduino.h>
#include <pthread.h>
#include <string.h>
#include <ArduinoJson.h>
#include "BluetoothSerial.h"

#include "rc_podium_protocol.h"

#define SERIAL_RX_BUFFER_SIZE (256)
#define SERIAL_TX_BUFFER_SIZE (1024)
char tx_buffer[SERIAL_TX_BUFFER_SIZE];
float data_buffer[RC_META_MAX];
int tick = 0;

void rc_set_data(int index, float value) {
    if (index < RC_META_MAX) {
        data_buffer[index] = value;
    }
}

int16_t rc_handler_init() {
    bzero(data_buffer, sizeof(data_buffer));

    rc_set_data(RC_META_UTC, millis());
    rc_set_data(RC_META_LATITUDE, 34.12345);
    rc_set_data(RC_META_LONGITUDE, 123.123456);
    rc_set_data(RC_META_SPEED, 0.0);
    rc_set_data(RC_META_ALTITUDE, 10.0);
    rc_set_data(RC_META_GPSSATS, 14.0);
    rc_set_data(RC_META_GPSQUAL, 1.0);
    rc_set_data(RC_META_GPSDOP, 0.75);
    rc_set_data(RC_META_ACCELX, 0.1);
    rc_set_data(RC_META_ACCELY, 0.2);
    rc_set_data(RC_META_ACCELZ, 0.3);
    rc_set_data(RC_META_YAW, 0.4);
    rc_set_data(RC_META_PITCH, 0.5);
    rc_set_data(RC_META_ROLL, 0.6);
    rc_set_data(RC_META_RPM, 1234.0);
    rc_set_data(RC_META_TPS, 12.34);
    rc_set_data(RC_META_BRAKE, 0.22);
    rc_set_data(RC_META_STEERING, 5.0);
    rc_set_data(RC_META_ENGINE_TEMP, 85.0);
    rc_set_data(RC_META_MAP, 15.0);
    rc_set_data(RC_META_IAT, 75.0);

    return 0;
}

void bt_tx_data_sample(BluetoothSerial *port, HardwareSerial *debug) {
    JsonDocument tx_doc;

    JsonObject s = tx_doc["s"].to<JsonObject>();
    JsonArray s_d = s["d"].to<JsonArray>();
    s_d.add(millis());
    for (int i = 1; i < RC_META_MAX; i++) {
        s_d.add(data_buffer[i]);
    }
    s_d.add( (1<<RC_META_MAX) - 1);
    s["t"] = tick++;
    size_t rc = serializeJson(tx_doc, tx_buffer, SERIAL_TX_BUFFER_SIZE);
    if (rc >= SERIAL_TX_BUFFER_SIZE) {
        debug->println("Buffer overrun\n");
        return;
    }
    // debug->print(".");
    // if (tick % 40 == 0) {
    //     debug->println("\n");
    // }
    debug->print("\r");
    debug->print(tx_buffer);
    port->printf(tx_buffer);
    port->println("\r\n");
    return;
}

void rc_bt_reader(BluetoothSerial *port, HardwareSerial *debug) {
    bool enable_data = false;
    char rx_buffer[SERIAL_RX_BUFFER_SIZE];

    unsigned int rx_buffer_index = 0;
    bzero(rx_buffer, SERIAL_RX_BUFFER_SIZE);

    if (NULL == port || NULL == debug) {
        return;
    }

    while(1) {
        // overran buffer
        if (rx_buffer_index >= SERIAL_RX_BUFFER_SIZE) {
            rx_buffer_index = 0;
            bzero(rx_buffer, SERIAL_RX_BUFFER_SIZE);
            debug->println("Buffer overrun\n");
        }

        if (port->available()) {
            rx_buffer[rx_buffer_index++] = port->read();

            if (rx_buffer_index >= 2 &&
                rx_buffer[rx_buffer_index - 2] == '\r' &&
                rx_buffer[rx_buffer_index - 1] == '\n') {

                debug->print(rx_buffer);
                if (strstr(rx_buffer, "getMeta")) {
                    debug->println(" >>Meta request");
                    port->printf(meta_mesg, tick++);
                }
                if (strstr(rx_buffer, "setTelemetry")) {
                    if (strstr(rx_buffer, "\"rate\":50")) {
                        enable_data = true;
                        debug->println(" >>Telemetry enabled");
                        port->printf(meta_mesg, tick++);
                    } else {
                        enable_data = false;
                        debug->println(" >>Telemetry disabled");
                    }
                }
                rx_buffer_index = 0;
                bzero(rx_buffer, SERIAL_RX_BUFFER_SIZE);
            }
        } else {
            if (enable_data) {
                bt_tx_data_sample(port, debug);
                delay(25);
            } else {
                delay(100);
            }
        }
    }
}