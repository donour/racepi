/**************************************************************************
    Copyright 2025-2026 Donour Sizemore

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

#define REFRESH_RATE_CLAMP_HZ (50)
#define RC_SERIAL_RX_BUFFER_SIZE (256)
#define RC_SERIAL_TX_BUFFER_SIZE (1024)
#define RC_SEND_DELAY_MS ((1000/(REFRESH_RATE_CLAMP_HZ))-1)
#define RC_IDLE_WAIT_MS (10)

float rc_channel_data[RC_META_MAX];
int32_t rc_gps_data[2];    // [0]=latitude, [1]=longitude  (degrees × 1e7)
bool new_data = false;

char tx_buffer[RC_SERIAL_TX_BUFFER_SIZE];
int tick = 0;

void rc_set_data(const int index, const float value) {
    if (index < RC_META_MAX) {
        // tearing could be an issue here because the data array
        // does not lock the memory bus
        rc_channel_data[index] = value;
    }
    new_data = true;
}

void rc_set_gps_data(const int index, const int32_t value_e7) {
    int slot = (index == RC_META_LATITUDE) ? 0 : (index == RC_META_LONGITUDE) ? 1 : -1;
    if (slot >= 0) {
        rc_gps_data[slot]    = value_e7;
    }
    new_data = true;
}

int16_t rc_handler_init() {
    bzero(rc_channel_data, sizeof(rc_channel_data));
    bzero(rc_gps_data, sizeof(rc_gps_data));

    rc_set_data(RC_META_ACCELX, 0.0);
    rc_set_data(RC_META_ACCELY, 0.0);
    rc_set_data(RC_META_ACCELZ, 0.0);
    rc_set_data(RC_META_YAW, 0.0);
    rc_set_data(RC_META_PITCH, 0.0);
    rc_set_data(RC_META_ROLL, 0.0);
    rc_set_data(RC_META_RPM, 9999.9);
    rc_set_data(RC_META_TPS, 0.0);
    rc_set_data(RC_META_BRAKE, 0.0);
    rc_set_data(RC_META_CLUTCH, 0.0);
    rc_set_data(RC_META_STEERING, 0.0);
    rc_set_data(RC_META_SPORT_MODE, 0.0);
    rc_set_data(RC_META_TC_DISABLE, 0.0);
    rc_set_data(RC_META_ENGINE_TEMP, 0.0);
    rc_set_data(RC_META_IAT, 0.0);
    rc_set_data(RC_META_FUEL_LEVEL, 0.0);
    rc_set_data(RC_META_ENGINE_TORQUE, 0.0);
    rc_set_data(RC_META_TC_TORQUE, 0.0);
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
        if (i == RC_META_LATITUDE || i == RC_META_LONGITUDE) {
            // Use integer arithmetic to format 8 decimal places with no float
            // or 64-bit math. value_e7 gives 7 decimal places; 
            int slot = (i == RC_META_LATITUDE) ? 0 : 1;
            int32_t raw = rc_gps_data[slot];
            bool negative = raw < 0;
            if (negative) raw = -raw;
            int32_t deg   = raw / 10000000L;
            int32_t frac7 = raw % 10000000L;
            int     frac8 = random(); // randomize last digit to ensure SS understands this as new data
            p += snprintf(p, end - p, "%s%ld.%07ld%d",
                          negative ? "-" : "", (long)deg, (long)frac7, frac8);
        } else {
            dtostrf(rc_channel_data[i], 7, 2, p);
            p += strlen(p);
        }
    }
    p += snprintf(p, end - p, ",%d],\"t\":%d}}", (1 << RC_META_MAX) - 1, tick++);

    if (p + 2 >= end) {
        debug->println("Buffer overrun\n");
        return;
    }
    *p++ = '\r';
    *p++ = '\n';
    *p = '\0';
    uint32_t t0 = millis();
    spp_serial_write((const uint8_t *)tx_buffer, p - tx_buffer);
    uint32_t dt = millis() - t0;
    if (dt > 5) {
        debug->printf("[SPP write blocked %lu ms]\n", (unsigned long)dt);
    }
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
        // Drain all available RX bytes before attempting TX.
        // Previously this processed one byte per loop iteration,
        // which blocked TX entirely while any RX data was pending.
        while (spp_serial_available()) {
            if (rx_buffer_index >= RC_SERIAL_RX_BUFFER_SIZE) {
                rx_buffer_index = 0;
                bzero(rx_buffer, RC_SERIAL_RX_BUFFER_SIZE);
                debug->println("Buffer overrun\n");
            }

            rx_buffer[rx_buffer_index++] = spp_serial_read();

            if (rx_buffer_index >= 2 &&
                rx_buffer[rx_buffer_index - 2] == '\r' &&
                rx_buffer[rx_buffer_index - 1] == '\n') {
                debug->printf("[RX cmd] %.*s", rx_buffer_index, rx_buffer);
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
        }

        if (enable_data > 0 && new_data) {
            bt_tx_data_sample(debug);
            new_data = false;
            delay(RC_SEND_DELAY_MS);
        } else {
            delay(RC_IDLE_WAIT_MS);
        }
    }
}