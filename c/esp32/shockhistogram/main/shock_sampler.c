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
#include "esp_task_wdt.h"
#include "driver/adc.h"
#include "shock_sampler.h"


// This code calculates histogram for shock (suspension damper) velocities by
// reading four (4) ADC channels. It samples around ~1 khz, so a large number of
// samples are collected per lap/run/session. We care about the distribution of 
// the samples, generally, and not their exact values. We expect off-by-one 
// errors in the count to be well below the noise of the system. Therefore, we 
// don't both to implement the sample counters as atomics. Given infinite time 
// We would replace all the counter increments with hardware atomic compare and 
// swap, but it just isn't needed. 

// TODO: we may want to also keep track of the sample counts when displaying results
unsigned long             histogram[CORNER_COUNT][CONFIG_NUM_HISTOGRAM_BUCKETS];
unsigned short normalized_histogram[CORNER_COUNT][CONFIG_NUM_HISTOGRAM_BUCKETS];
volatile bool recording_active = true;

static const adc_atten_t atten = ADC_ATTEN_DB_11; // full 3.9v range
static const adc_unit_t   unit = ADC_UNIT_1;
static int last_shock_position[CORNER_COUNT];
static long last_shock_time[CORNER_COUNT];
static unsigned int sample_delay_ticks = TICKS_PER_SHOCK_SAMPLE;

static const adc_channel_t adc_channels[] = {
  ADC1_CHANNEL_6,
  ADC1_CHANNEL_3,
  ADC1_CHANNEL_0,
  ADC1_CHANNEL_5,
};  

void zero_histogram() {
  memset(histogram, 0, (sizeof(unsigned long))*CORNER_COUNT*CONFIG_NUM_HISTOGRAM_BUCKETS);
}

// Populate normalized histogram array where buckets represent percentage of the 
// total sample count
void populate_normalized_histogram() {
  // TODO: this should take the destination object as an argument
  for (int corner = 0; corner < CORNER_COUNT; corner++) {
    // add extra sampel to avoid divide by zero
    unsigned long total_samples_count = 1;
    
    for (int bucket = 0; bucket < CONFIG_NUM_HISTOGRAM_BUCKETS; bucket++) {
      total_samples_count += histogram[corner][bucket];
    }
    for (int bucket = 0; bucket < CONFIG_NUM_HISTOGRAM_BUCKETS; bucket++) {
      normalized_histogram[corner][bucket] = (unsigned short)(histogram[corner][bucket]*1000 / total_samples_count);
    }  
  }
}

void shock_histogram_init() {
  //Configure ADC
  adc1_config_width(ADC_WIDTH_BIT);  
  for (int i = 0; i < CORNER_COUNT; i++) { 
    adc1_config_channel_atten(adc_channels[i], atten);
  }
  zero_histogram();    

  if (sample_delay_ticks <= 0 ) {
    // TODO: select appropriate sleep time.
    printf("Warning: shock sampling interval is more frequent than clock tick. Please rebuild with a higher tick frequency.");
    sample_delay_ticks = 1;
  }
}

// rate must be in mm/s
static int get_bucket_from_rate(int rate) {
  int bucket = (int)( rate + MAX_SPEED_MM_S) / HISTOGRAM_BUCKET_SIZE;
  if (bucket < 0) return  0;
  if (bucket >=  CONFIG_NUM_HISTOGRAM_BUCKETS) return CONFIG_NUM_HISTOGRAM_BUCKETS - 1;
  return bucket;
}

void sample_corner(unsigned int corner) {
  int shock_velocity;
  struct timeval tv;
  int adc_val = 0;
  
  // Read and timestamp the channel		    
  for (int sample_count = 0; sample_count < ADC_MULTISAMPLE_COUNT; sample_count++) {
    adc_val += adc1_get_raw((adc1_channel_t)adc_channels[corner]);
    esp_task_wdt_reset();
  }
  adc_val /= ADC_MULTISAMPLE_COUNT;
  
  gettimeofday(&tv, 0); // TODO: check return code
  long timestamp = (long) tv.tv_usec + ((long) tv.tv_sec) * 1e6;
  
  // calculate the channel rate
  int count_per_second = ((adc_val - last_shock_position[corner])*1e6) / (timestamp - last_shock_time[corner]);
  shock_velocity = ADC_TO_MM(count_per_second);
  histogram[corner][get_bucket_from_rate(shock_velocity)]++;
  // save current readings
  last_shock_position[corner] = adc_val;
  last_shock_time[corner] = timestamp;
}

void sample_shock_channels() {
  // subscribe to watchdog and verify
  ESP_ERROR_CHECK(esp_task_wdt_add(NULL));
  ESP_ERROR_CHECK(esp_task_wdt_status(NULL));
  while (true) {
    vTaskDelay(sample_delay_ticks);
    if (recording_active) {
      for(int i = 0; i < CORNER_COUNT; i++) {
	sample_corner(i);
	ESP_ERROR_CHECK(esp_task_wdt_reset());
      }
    }
  }
}

