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
#ifndef __SHOCK_SAMPLER_H__
#define __SHOCK_SAMPLER_H__

#include "freertos/FreeRTOS.h"

#define CORNER_COUNT  (4) // LF, RF, LR, RR
#define ADC_MAX_VALUE ((1<<12)-1)
#define ADC_MAX_RATE  (200 * ADC_MAX_VALUE)

// Because the buckets contain both positive and negative values, we need
// the buckets to be _twice_ the max rate / number of buckets. Zero is the
// center bucket.
#define HISTOGRAM_BUCKET_SIZE ((ADC_MAX_RATE*2) / CONFIG_NUM_HISTOGRAM_BUCKETS)

#define TICKS_PER_SHOCK_SAMPLE (1 / portTICK_PERIOD_MS) // 1 khz

void shock_histogram_init();
void sample_shock_channels();
void zero_histogram();
void populate_normalized_histogram();

extern unsigned long             histogram[CORNER_COUNT][CONFIG_NUM_HISTOGRAM_BUCKETS];
extern unsigned short normalized_histogram[CORNER_COUNT][CONFIG_NUM_HISTOGRAM_BUCKETS];
#endif // __SHOCK_SAMPLER_H__
