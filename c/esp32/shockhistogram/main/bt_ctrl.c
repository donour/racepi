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

#include "string.h"
#include "bt_ctrl.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_gap_bt_api.h"
#include "esp_bt_device.h"
#include "esp_spp_api.h"

#define TAG             "[bt_ctrl]"
#define SPP_SERVER_NAME "SPP_SERVER"

static const esp_spp_mode_t esp_spp_mode = ESP_SPP_MODE_CB;
static const esp_spp_sec_t  sec_mask     = ESP_SPP_SEC_AUTHENTICATE;
static const esp_spp_role_t role_slave   = ESP_SPP_ROLE_SLAVE;

static void handle_input(esp_spp_cb_param_t *param) {
  if (! strncmp("zero",(char*) param->data_ind.data, param->data_ind.len)) {
    ESP_LOGI(TAG, "Zero");
  }
  if (! strncmp("Test123",(char*) param->data_ind.data, param->data_ind.len)) {
    ESP_LOGI(TAG, "test");
  }
}

static void esp_spp_cb(esp_spp_cb_event_t event, esp_spp_cb_param_t *param)
{
    switch (event) {

    case ESP_SPP_INIT_EVT:
      ESP_LOGI(TAG, "ESP_SPP_INIT_EVT");
      esp_bt_dev_set_device_name(BT_DEVICE_NAME);
      esp_bt_gap_set_scan_mode(ESP_BT_SCAN_MODE_CONNECTABLE_DISCOVERABLE);
      esp_spp_start_srv(sec_mask,role_slave, 0, SPP_SERVER_NAME);
      break;
    case ESP_SPP_DISCOVERY_COMP_EVT:
      ESP_LOGI(TAG, "ESP_SPP_DISCOVERY_COMP_EVT");
      break;
    case ESP_SPP_OPEN_EVT:
      ESP_LOGI(TAG, "ESP_SPP_OPEN_EVT");
      break;
    case ESP_SPP_CLOSE_EVT:
      ESP_LOGI(TAG, "ESP_SPP_CLOSE_EVT");
      break;
    case ESP_SPP_START_EVT:
      ESP_LOGI(TAG, "ESP_SPP_START_EVT");
      break;
    case ESP_SPP_CL_INIT_EVT:
      ESP_LOGI(TAG, "ESP_SPP_CL_INIT_EVT");
      break;
    case ESP_SPP_DATA_IND_EVT:
      handle_input(param);
      break;
    case ESP_SPP_CONG_EVT:
      ESP_LOGI(TAG, "ESP_SPP_CONG_EVT");
      break;
    case ESP_SPP_WRITE_EVT:
      ESP_LOGI(TAG, "ESP_SPP_WRITE_EVT");
      break;
    case ESP_SPP_SRV_OPEN_EVT:
      ESP_LOGI(TAG, "ESP_SPP_SRV_OPEN_EVT");
      break;
    default:
      break;
    }
}

void bt_ctrl_init() {
  esp_err_t rc;
  
  esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
  if ((rc = esp_bt_controller_init(&bt_cfg)) != ESP_OK) {
    ESP_LOGE(TAG, "%s initialize controller failed: %s\n", __func__, esp_err_to_name(rc));
    return;
  }
  if ((rc = esp_bt_controller_enable(ESP_BT_MODE_CLASSIC_BT)) != ESP_OK) {
    ESP_LOGE(TAG, "%s enable controller failed: %s\n", __func__, esp_err_to_name(rc));
    return;
  }
  if ((rc = esp_bluedroid_init()) != ESP_OK) {
    ESP_LOGE(TAG, "%s initialize bluedroid failed: %s\n", __func__, esp_err_to_name(rc));
    return;
  }
  if ((rc = esp_bluedroid_enable()) != ESP_OK) {
    ESP_LOGE(TAG, "%s enable bluedroid failed: %s\n", __func__, esp_err_to_name(rc));
    return;
  }
  
  if ((rc = esp_spp_register_callback(esp_spp_cb)) != ESP_OK) {
    ESP_LOGE(TAG, "%s spp register failed: %s\n", __func__, esp_err_to_name(rc));
    return;
  }
  if ((rc = esp_spp_init(esp_spp_mode)) != ESP_OK) {
    ESP_LOGE(TAG, "%s spp init failed: %s\n", __func__, esp_err_to_name(rc));
    return;
  }
  #if (BT_SPP_INCLUDED)
    esp_bt_sp_param_t param_type = ESP_BT_SP_IOCAP_MODE;
    esp_bt_io_cap_t iocap = ESP_BT_IO_CAP_IO;
    esp_bt_gap_set_security_param(param_type, &iocap, sizeof(uint8_t));
#endif ///BT_SPP_INCLUDED
}
