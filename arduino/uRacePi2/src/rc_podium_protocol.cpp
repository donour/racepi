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
#include <stdio.h>

#include "rc_podium_protocol.h"
#include "spp_serial.h"

#define RC_SERIAL_RX_BUFFER_SIZE (256)
#define RC_SERIAL_TX_BUFFER_SIZE (1024)
#define RC_SEND_DELAY_MS (1000/50) // clip the update rate to 50hz
#define RC_IDLE_WAIT_MS (10)

float rc_channel_data[RC_META_MAX];
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
    rc_set_data(RC_META_IAT, 0.0);
    rc_set_data(RC_META_FUEL_LEVEL, 0.0);
    rc_set_data(RC_META_ENGINE_TORQUE, 0.0);
    rc_set_data(RC_META_WHEEL_SPEED_LF, 0.0);
    rc_set_data(RC_META_WHEEL_SPEED_RF, 0.0);
    rc_set_data(RC_META_WHEEL_SPEED_LR, 0.0);
    rc_set_data(RC_META_WHEEL_SPEED_RR, 0.0);

    return 0;
}

// Serialize telemetry data directly into tx_buffer as JSON.
// Uses dtostrf() for float formatting instead of snprintf %g/%f to avoid
// the implicit float-to-double promotion in varargs, which forces software
// double-precision arithmetic on ESP32 (no double FPU). dtostrf() stays
// in single-precision using the hardware FPU, which is ~10-20x faster.
void bt_tx_data_sample(HardwareSerial *debug) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    uint64_t timestamp_ms = ((uint64_t)tv.tv_sec) * 1000 + ((uint64_t)tv.tv_usec) / 1000;

    char *p = tx_buffer;
    char *end = tx_buffer + RC_SERIAL_TX_BUFFER_SIZE;

    p += snprintf(p, end - p, "{\"s\":{\"d\":[%llu", timestamp_ms);
    for (int i = 1; i < RC_META_MAX && p < end; i++) {
        *p++ = ',';
        dtostrf(rc_channel_data[i], 0, 6, p);
        p += strlen(p);
    }
    p += snprintf(p, end - p, ",%d],\"t\":%d}}", (1 << RC_META_MAX) - 1, tick++);

    if (p + 2 >= end) {
        debug->println("Buffer overrun\n");
        return;
    }
    *p++ = '\r';
    *p++ = '\n';
    *p = '\0';
    spp_serial_write((const uint8_t *)tx_buffer, p - tx_buffer);
}

void rc_bt_reader(HardwareSerial *debug, void (*rc_enable_callback)(bool)) {
    int enable_data = 0;
    char rx_buffer[RC_SERIAL_RX_BUFFER_SIZE];

    unsigned int rx_buffer_index = 0;
    bzero(rx_buffer, RC_SERIAL_RX_BUFFER_SIZE);

    if (NULL == debug) {
        return;
    }

    while(1) {
        // overran buffer
        if (rx_buffer_index >= RC_SERIAL_RX_BUFFER_SIZE) {
            rx_buffer_index = 0;
            bzero(rx_buffer, RC_SERIAL_RX_BUFFER_SIZE);
            debug->println("Buffer overrun\n");
        }

        if (spp_serial_available()) {
            rx_buffer[rx_buffer_index++] = spp_serial_read();

            if (rx_buffer_index >= 2 &&
                rx_buffer[rx_buffer_index - 2] == '\r' &&
                rx_buffer[rx_buffer_index - 1] == '\n') {
                if (strstr(rx_buffer, "getMeta")) {
                    debug->println("[Meta request]");
                    spp_serial_printf(meta_mesg, tick++);
                }
                if (strstr(rx_buffer, "setTelemetry")) {
                    if (strstr(rx_buffer, "\"rate\":50")) {
                        enable_data++;
                        if (enable_data == 1 && rc_enable_callback != NULL) {
                            rc_enable_callback(true);
                        }
                        debug->printf("[Telemetry enabled (%d)]\n", enable_data);
                        spp_serial_printf(meta_mesg, tick++);
                    } else {
                        if (enable_data > 0) enable_data--;
                        if (enable_data == 0 && rc_enable_callback != NULL) {
                            rc_enable_callback(false);
                        }
                        debug->printf("[Telemetry disabled (%d)]\n", enable_data);
                    }
                }
                rx_buffer_index = 0;
                bzero(rx_buffer, RC_SERIAL_RX_BUFFER_SIZE);
            }
        } else {
            if (enable_data > 0 && new_data) {
                bt_tx_data_sample(debug);
                new_data = false;
                delay(RC_SEND_DELAY_MS);
            } else {
                delay(RC_IDLE_WAIT_MS);
            }
        }
    }
}