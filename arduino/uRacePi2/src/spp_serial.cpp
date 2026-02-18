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

#include "spp_serial.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include <Arduino.h>
#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_bt_device.h"
#include "esp_gap_bt_api.h"
#include "esp_spp_api.h"
#include "esp_log.h"

static const char *TAG = "spp_serial";

#define SPP_SERVER_NAME "SPP_SERVER"
#define RX_RING_BUF_SIZE 512
#define TX_FMT_BUF_SIZE  3072

static uint32_t spp_handle = 0;
static volatile bool spp_connected = false;

static uint8_t  rx_ring[RX_RING_BUF_SIZE];
static volatile size_t rx_head = 0;
static volatile size_t rx_tail = 0;

static void rx_ring_push(const uint8_t *data, size_t len) {
    for (size_t i = 0; i < len; i++) {
        size_t next = (rx_head + 1) % RX_RING_BUF_SIZE;
        if (next == rx_tail) {
            break; // buffer full, drop remaining bytes
        }
        rx_ring[rx_head] = data[i];
        rx_head = next;
    }
}

static void gap_callback(esp_bt_gap_cb_event_t event, esp_bt_gap_cb_param_t *param) {
    switch (event) {
        case ESP_BT_GAP_AUTH_CMPL_EVT:
            if (param->auth_cmpl.stat == ESP_BT_STATUS_SUCCESS) {
                ESP_LOGI(TAG, "authentication success: %s", param->auth_cmpl.device_name);
            } else {
                ESP_LOGE(TAG, "authentication failed, status: %d", param->auth_cmpl.stat);
            }
            break;
        case ESP_BT_GAP_PIN_REQ_EVT:
            {
                esp_bt_pin_code_t pin = {'1', '2', '3', '4'};
                esp_bt_gap_pin_reply(param->pin_req.bda, true, 4, pin);
            }
            break;
        default:
            break;
    }
}

static void spp_callback(esp_spp_cb_event_t event, esp_spp_cb_param_t *param) {
    switch (event) {
        case ESP_SPP_INIT_EVT:
            ESP_LOGI(TAG, "ESP_SPP_INIT_EVT");
            esp_spp_start_srv(ESP_SPP_SEC_NONE, ESP_SPP_ROLE_SLAVE, 0, SPP_SERVER_NAME);
            break;
        case ESP_SPP_SRV_OPEN_EVT:
            ESP_LOGI(TAG, "ESP_SPP_SRV_OPEN_EVT handle=%lu", (unsigned long)param->srv_open.handle);
            spp_handle = param->srv_open.handle;
            spp_connected = true;
            break;
        case ESP_SPP_OPEN_EVT:
            ESP_LOGI(TAG, "ESP_SPP_OPEN_EVT handle=%lu", (unsigned long)param->open.handle);
            spp_handle = param->open.handle;
            spp_connected = true;
            break;
        case ESP_SPP_DATA_IND_EVT:
            rx_ring_push(param->data_ind.data, param->data_ind.len);
            break;
        case ESP_SPP_CLOSE_EVT:
            ESP_LOGI(TAG, "ESP_SPP_CLOSE_EVT");
            spp_handle = 0;
            spp_connected = false;
            break;
        default:
            break;
    }
}

void spp_serial_init(const char *device_name) {
    esp_err_t ret;

    // Use Arduino's btStart() which checks controller state and
    // handles init/enable idempotently.
    if (!btStart()) {
        ESP_LOGE(TAG, "btStart failed");
        return;
    }

    ret = esp_bluedroid_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "bluedroid init failed: %s", esp_err_to_name(ret));
        return;
    }

    ret = esp_bluedroid_enable();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "bluedroid enable failed: %s", esp_err_to_name(ret));
        return;
    }

    esp_bt_gap_register_callback(gap_callback);

    ret = esp_spp_register_callback(spp_callback);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "spp register callback failed: %s", esp_err_to_name(ret));
        return;
    }

    ret = esp_spp_init(ESP_SPP_MODE_CB);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "spp init failed: %s", esp_err_to_name(ret));
        return;
    }

    esp_bt_dev_set_device_name(device_name);
    esp_bt_gap_set_scan_mode(ESP_BT_CONNECTABLE, ESP_BT_GENERAL_DISCOVERABLE);

    ESP_LOGI(TAG, "SPP initialized as \"%s\"", device_name);
}

void spp_serial_write(const uint8_t *data, size_t len) {
    if (spp_connected && spp_handle != 0 && len > 0) {
        esp_spp_write(spp_handle, len, (uint8_t *)data);
    }
}

void spp_serial_printf(const char *fmt, ...) {
    static char buf[TX_FMT_BUF_SIZE];
    va_list args;
    va_start(args, fmt);
    int len = vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    if (len > 0) {
        spp_serial_write((const uint8_t *)buf, (size_t)len);
    }
}

int spp_serial_available() {
    return (rx_head + RX_RING_BUF_SIZE - rx_tail) % RX_RING_BUF_SIZE;
}

int spp_serial_read() {
    if (rx_head == rx_tail) {
        return -1;
    }
    uint8_t byte = rx_ring[rx_tail];
    rx_tail = (rx_tail + 1) % RX_RING_BUF_SIZE;
    return byte;
}

bool spp_serial_connected() {
    return spp_connected;
}
