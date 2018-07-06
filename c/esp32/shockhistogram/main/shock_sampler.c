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

#include <string.h>
#include <sys/time.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/adc.h"
#include "shock_sampler.h"

unsigned long histogram[CORNER_COUNT][CONFIG_NUM_HISTOGRAM_BUCKETS];

static const adc_atten_t atten = ADC_ATTEN_DB_0;
static const adc_unit_t unit = ADC_UNIT_1;
static unsigned short last_shock_position[CORNER_COUNT];
static unsigned long  last_shock_time[CORNER_COUNT];

static const adc_channel_t adc_channels[] = {
  ADC_CHANNEL_1,
  ADC_CHANNEL_2,
  ADC_CHANNEL_3,
  ADC_CHANNEL_4
};  

void zero_histogram() {
  memset(histogram, 0, (sizeof(unsigned long))*CORNER_COUNT*CONFIG_NUM_HISTOGRAM_BUCKETS);
}

void shock_histogram_init() {
  zero_histogram();
    
  //Configure ADC
  adc1_config_width(ADC_WIDTH_BIT_12);
  for (int i = 0; i < CORNER_COUNT; i++) { 
    adc1_config_channel_atten(adc_channels[i], atten);
  }
}

/*
static void normalize_histogram_buckets(unsigned long *data[]) {
  for(int i = 0; i < CORNER_COUNT; i++) {
    unsigned long total_count = 0;
    for (int j = 0; j < NUM_HISTOGRAM_BUCKETS; j++) {
      total_count += data[i][j];
    }

    for (int j = 0; j < NUM_HISTOGRAM_BUCKETS; j++) {
      data[i][j] = data[i][j]*100 / total_count;
    }    
  }
}
*/

static int get_bucket_from_rate(int rate) {
  int bucket = (int)( rate + ADC_MAX_RATE) / HISTOGRAM_BUCKET_SIZE;
  if (bucket < 0) return  0;
  if (bucket >=  CONFIG_NUM_HISTOGRAM_BUCKETS) return CONFIG_NUM_HISTOGRAM_BUCKETS - 1;
  return bucket;
}

void sample_shock_channels() {
  while (true) {
    int shock_velocity[CORNER_COUNT];
    struct timeval tv;
  
    for(int i = 0; i < CORNER_COUNT; i++) {

      // Read and timestamp the channel
      unsigned short adc_val = adc1_get_raw((adc1_channel_t)adc_channels[i]);
      gettimeofday(&tv, 0); // TODO: check return code
      unsigned long timestamp = (unsigned long) tv.tv_usec + ((unsigned long) tv.tv_sec) * 1e6;

      // calculate the channel rate
      long count_per_second = ((adc_val - last_shock_position[i])*1e6) / (timestamp - last_shock_time[i]);

      shock_velocity[i] = count_per_second;
    
      // TODO: scale to distance

      histogram[i][get_bucket_from_rate(shock_velocity[i])]++;

      // save current readings
      last_shock_position[i] = adc_val;
      last_shock_time[i] = timestamp;
    }
    vTaskDelay(1 / portTICK_PERIOD_MS);
  }
}

