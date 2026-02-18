/**************************************************************************
    Copyright 2025 Donour Sizemore

    This file is part of RacePi

    RacePi is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2.

    RacePi is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with RacePi.  If not, see <http://www.gnu.org/licenses/>.
**************************************************************************/

#include <string.h>
#include <ArduinoJson.h>
#include "BluetoothSerial.h"

#include "rc_podium_protocol.h"

#define RC_SERIAL_RX_BUFFER_SIZE (256)
#define RC_SERIAL_TX_BUFFER_SIZE (1024)
#define RC_SEND_DELAY_MS (1000/50) // clip the update rate to 50hz
#define RC_IDLE_WAIT_MS (10)

double rc_channel_data[RC_META_MAX];
bool new_data = false;

char tx_buffer[RC_SERIAL_TX_BUFFER_SIZE];
int tick = 0;

void rc_set_data(const int index,const float value) {
    if (index < RC_META_MAX) {
        // tearing could be an issue here because the data array
        // does not lock the memory bus
        rc_channel_data[index] = value;
    }
    new_data = true;    
}

int16_t rc_handler_init() {
    bzero(rc_channel_data, sizeof(rc_channel_data));

    rc_set_data(RC_META_ACCELX, 0.0);
    rc_set_data(RC_META_ACCELY, 0.0);
    rc_set_data(RC_META_ACCELZ, 0.0);
    rc_set_data(RC_META_YAW, 0.0);
    rc_set_data(RC_META_PITCH, 0.0);
    rc_set_data(RC_META_ROLL, 0.0);
    rc_set_data(RC_META_RPM, 9999.9);
    rc_set_data(RC_META_TPS, 0.0);
    rc_set_data(RC_META_BRAKE, 0.0);
    rc_set_data(RC_META_STEERING, 0.0);
    rc_set_data(RC_META_ENGINE_TEMP, 0.0);
    rc_set_data(RC_META_MAP, 0.0);
    rc_set_data(RC_META_IAT, 0.0);
    rc_set_data(RC_META_OIL_TEMP, 0.0);
    rc_set_data(RC_META_FUEL_LEVEL, 0.0);
    rc_set_data(RC_META_ENGINE_TORQUE, 0.0);
    rc_set_data(RC_META_WHEEL_SPEED_LF, 0.0);
    rc_set_data(RC_META_WHEEL_SPEED_RF, 0.0);
    rc_set_data(RC_META_WHEEL_SPEED_LR, 0.0);
    rc_set_data(RC_META_WHEEL_SPEED_RR, 0.0);

    return 0;
}

void bt_tx_data_sample(BluetoothSerial *port, HardwareSerial *debug) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    JsonDocument tx_doc;

    JsonObject s = tx_doc["s"].to<JsonObject>();
    JsonArray s_d = s["d"].to<JsonArray>();
    s_d.add(((uint64_t)tv.tv_sec)*1000 + ((uint64_t)tv.tv_usec)/1000);
    for (int i = 1; i < RC_META_MAX; i++) {
        s_d.add(rc_channel_data[i]);
    }
    s_d.add( (1<<RC_META_MAX) - 1);
    s["t"] = tick++;
    size_t rc = serializeJson(tx_doc, tx_buffer, RC_SERIAL_TX_BUFFER_SIZE);
    if (rc >= RC_SERIAL_TX_BUFFER_SIZE) {
        debug->println("Buffer overrun\n");
        return;
    }
    // debug->print(".");
    // if (tick % 40 == 0) {
    //     debug->println("\n");
    // }
    // debug->print("\r");
    // debug->print(tx_buffer);
    port->printf(tx_buffer);
    port->println("\r\n");
    return;
}

void rc_bt_reader(BluetoothSerial *port, HardwareSerial *debug, void (*rc_enable_callback)(bool)) {
    bool enable_data = false;
    char rx_buffer[RC_SERIAL_RX_BUFFER_SIZE];

    unsigned int rx_buffer_index = 0;
    bzero(rx_buffer, RC_SERIAL_RX_BUFFER_SIZE);

    if (NULL == port || NULL == debug) {
        return;
    }

    while(1) {
        // overran buffer
        if (rx_buffer_index >= RC_SERIAL_RX_BUFFER_SIZE) {
            rx_buffer_index = 0;
            bzero(rx_buffer, RC_SERIAL_RX_BUFFER_SIZE);
            debug->println("Buffer overrun\n");
        }

        if (port->available()) {
            rx_buffer[rx_buffer_index++] = port->read();

            if (rx_buffer_index >= 2 &&
                rx_buffer[rx_buffer_index - 2] == '\r' &&
                rx_buffer[rx_buffer_index - 1] == '\n') {
                if (strstr(rx_buffer, "getMeta")) {
                    debug->println("[Meta request]");
                    port->printf(meta_mesg, tick++);
                }
                if (strstr(rx_buffer, "setTelemetry")) {
                    if (strstr(rx_buffer, "\"rate\":50")) {
                        enable_data = true;
                        if (rc_enable_callback != NULL) {
                            rc_enable_callback(true);
                        }
                        debug->println("[Telemetry enabled]");
                        port->printf(meta_mesg, tick++);
                    } else {
                        enable_data = false;
                        if (rc_enable_callback != NULL) {
                            rc_enable_callback(false);
                        }
                        debug->println("[Telemetry disabled]");
                    }
                }
                rx_buffer_index = 0;
                bzero(rx_buffer, RC_SERIAL_RX_BUFFER_SIZE);
            }
        } else {
            if (enable_data && new_data) {
                bt_tx_data_sample(port, debug);
                new_data = false;
                delay(RC_SEND_DELAY_MS);
            } else {
                delay(RC_IDLE_WAIT_MS);
            }
        }
    }
}