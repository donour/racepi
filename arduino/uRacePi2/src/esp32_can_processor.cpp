/**************************************************************************
    Copyright 2021-2025 Donour Sizemore

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
#include "freertos/FreeRTOS.h"
#include <driver/gpio.h>
#include <driver/twai.h>
#include <esp_system.h>

int16_t setup_can_driver(uint8_t tx_gpio, uint8_t rx_gpio) {
 twai_general_config_t general_config = {
        .mode = TWAI_MODE_LISTEN_ONLY,
        .tx_io = (gpio_num_t)tx_gpio,
        .rx_io = (gpio_num_t)rx_gpio,
        .clkout_io = (gpio_num_t)TWAI_IO_UNUSED,
        .bus_off_io = (gpio_num_t)TWAI_IO_UNUSED,
        .tx_queue_len = 32,
        .rx_queue_len = 32,
        .alerts_enabled = TWAI_ALERT_NONE,
        .clkout_divider = 0};
    twai_timing_config_t timing_config = TWAI_TIMING_CONFIG_500KBITS();
    twai_filter_config_t filter_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();
    esp_err_t error;

    error = twai_driver_install(&general_config, &timing_config, &filter_config);
    if (error != ESP_OK) {
        return -1;
    }

    // start CAN driver
    error = twai_start();
    if (error != ESP_OK) {
        return -2;
    }

    // TODO: clear receive queue
    //can_clear_receive_queue();

    return 0;
}
