/*
    Copyright 2018 Donour Sizemore

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
*/

#include "esp_log.h"
#include "shock_sampler.h"
#include "driver/gpio.h"

#define GPIO_BUTTON_PIN  (21)
#define GPIO_LED_PIN     (13)

// We use a GPIO button to enable/disable data sampling from the ADCs

static void IRAM_ATTR gpio_button_handler(void* arg) {
  uint32_t gpio_num = (uint32_t) arg;
  recording_active = (gpio_get_level(gpio_num) == 1);
  gpio_set_level(GPIO_LED_PIN, recording_active ? 1 : 0);
}

void gpio_ctrls_init() {
  gpio_config_t gpio_conf;

  // configure start/stop switch
  gpio_conf.intr_type = GPIO_PIN_INTR_DISABLE;
  gpio_conf.mode = GPIO_MODE_INPUT;
  gpio_conf.pull_down_en = 1;
  gpio_conf.pull_up_en = 0;
  gpio_conf.pin_bit_mask =(1ULL << GPIO_BUTTON_PIN);
  gpio_config(&gpio_conf);
  gpio_set_intr_type(GPIO_BUTTON_PIN, GPIO_INTR_ANYEDGE);
  gpio_install_isr_service(ESP_INTR_FLAG_EDGE);
  gpio_isr_handler_add(GPIO_BUTTON_PIN, gpio_button_handler, (void*)GPIO_BUTTON_PIN);

  // configure status LED
  gpio_conf.intr_type = GPIO_PIN_INTR_DISABLE;
  gpio_conf.mode = GPIO_MODE_OUTPUT;
  gpio_conf.pin_bit_mask = (1ULL<< GPIO_LED_PIN);
  gpio_conf.pull_down_en = 0;
  gpio_conf.pull_up_en = 1;
  gpio_config(&gpio_conf);
}



