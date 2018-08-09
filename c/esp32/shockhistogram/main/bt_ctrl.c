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
#include "cJSON.h"
#include "shock_sampler.h"

#define TAG             "[bt_ctrl]"
#define SPP_SERVER_NAME "SPP_SERVER"

static const esp_spp_mode_t esp_spp_mode = ESP_SPP_MODE_CB;
static const esp_spp_sec_t  sec_mask     = ESP_SPP_SEC_AUTHENTICATE;
static const esp_spp_role_t role_slave   = ESP_SPP_ROLE_SLAVE;

static char* create_histogram_json() {
  int x_axis[CONFIG_NUM_HISTOGRAM_BUCKETS];
  int shock_positions_mm[CORNER_COUNT];
  
  populate_normalized_histogram();
  get_current_shock_positions_mm(shock_positions_mm);
  cJSON *root = cJSON_CreateObject();
  cJSON_AddItemToObject(root, "name", cJSON_CreateString("RacePi Shock Histogram"));

  // write each corners data
  for (int corner = 0; corner < CORNER_COUNT; corner++) {
    char *header="unknown";
    switch(corner) {
        case 0:
          header="LF";
          break;
        case 1:
          header="RF";
          break;
        case 2:
          header="LR";
          break;
        case 3: 
          header="RR";
          break;
        default:break;
    }
    cJSON_AddItemToObject(root, header,
			  cJSON_CreateIntArray((int*)normalized_histogram[corner],CONFIG_NUM_HISTOGRAM_BUCKETS));    
  }

  // write x axis data
  for (int column = 0; column < CONFIG_NUM_HISTOGRAM_BUCKETS; column++) {
    x_axis[column] = HISTOGRAM_BUCKET_SIZE*(column - (CONFIG_NUM_HISTOGRAM_BUCKETS)/2); 
  } 
  cJSON_AddItemToObject(root, "x_axis",
			cJSON_CreateIntArray(x_axis,CONFIG_NUM_HISTOGRAM_BUCKETS));    

  cJSON_AddItemToObject(root, "current_positions_mm",
			cJSON_CreateIntArray(shock_positions_mm, CORNER_COUNT));    
  
  char *rv = cJSON_Print(root);
  cJSON_Delete(root);
  return rv;
} 


static void handle_input(esp_spp_cb_param_t *param) {
  char *rv = create_histogram_json();
  if (rv != NULL) {
    if (ESP_OK != 
	esp_spp_write(param->srv_open.handle, strlen(rv), (uint8_t *)rv)) {
      ESP_LOGE(TAG, "Result Generation Failed");
    }
    free(rv);
  } else {
    ESP_LOGE(TAG, "Histogram JSON creation failed");
  }
}

static void esp_spp_cb(esp_spp_cb_event_t event, esp_spp_cb_param_t *param)
{
  switch (event) {
    case ESP_SPP_INIT_EVT:
      ESP_LOGI(TAG, "ESP_SPP_INIT_EVT");
      esp_bt_dev_set_device_name(CONFIG_ESP_BLUETOOTH_DEVICE_NAME);
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


void esp_bt_gap_cb(esp_bt_gap_cb_event_t event, esp_bt_gap_cb_param_t *param)
{
  switch (event) {
#if (BT_SPP_INCLUDED)
    case ESP_BT_GAP_AUTH_CMPL_EVT:{
        if (param->auth_cmpl.stat == ESP_BT_STATUS_SUCCESS) {
            ESP_LOGI(TAG, "authentication success: %s", param->auth_cmpl.device_name);
            esp_log_buffer_hex(TAG, param->auth_cmpl.bda, ESP_BD_ADDR_LEN);
        } else {
            ESP_LOGE(TAG, "authentication failed, status:%d", param->auth_cmpl.stat);
        }
        break;
    }
    case ESP_BT_GAP_CFM_REQ_EVT:
        ESP_LOGI(TAG, "ESP_BT_GAP_CFM_REQ_EVT Please compare the numeric value: %d", param->cfm_req.num_val);
        esp_bt_gap_ssp_confirm_reply(param->cfm_req.bda, true);
        break;
    case ESP_BT_GAP_KEY_NOTIF_EVT:
        ESP_LOGI(TAG, "ESP_BT_GAP_KEY_NOTIF_EVT passkey:%d", param->key_notif.passkey);
        break;
    case ESP_BT_GAP_KEY_REQ_EVT:
        ESP_LOGI(TAG, "ESP_BT_GAP_KEY_REQ_EVT Please enter passkey!");
        break;
#endif ///BT_SPP_INCLUDED
    default: 
        ESP_LOGI(TAG, "event: %d", event);
        break;    
  }
  return;
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
  if ((rc = esp_bt_gap_register_callback(esp_bt_gap_cb)) != ESP_OK) {
    ESP_LOGE(TAG, "%s gap register failed: %s\n", __func__, esp_err_to_name(rc));
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
