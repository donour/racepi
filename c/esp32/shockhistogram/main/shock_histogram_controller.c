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

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"
#include "shock_sampler.h"
#include "wifi_setup.h"
#include "web_ctrl.h"
#include "tcpip_adapter.h"

void app_main()
{
    //Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    wifi_init();

    // start histogram task
    shock_histogram_init();
    xTaskCreate(sample_shock_channels, "sample_shock", 2048, NULL, configMAX_PRIORITIES-1, NULL);

    // start web controller
    tcpip_adapter_init();
    xTaskCreate(httpd_task, "httpd task", 2048, NULL, configMAX_PRIORITIES-3, NULL);
}
