/**************************************************************************
    Copyright 2021 Donour Sizemore

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
#include <stdint.h>

#define MASS_IN_KG (1450)
#define EVORA_CD (0.337) // evora 410 specifies 0.35, lower value is probably S1 cars
#define EVORA_FRONT_AREA (1.91) // from lotus 410 launch material
  
float rho = 1.225; // approximate for sea level

float calculate_power_lost_to_drag(float v, float cd, float area) { 
  float drag_N = v*v * cd * area * rho * 0.5;
  return drag_N*v; // watt
}

float calculate_power_from_speed(
  int16_t speed_x1000, 
  int16_t last_speed_x1000,
  uint32_t gps_time_x1000,
  uint32_t last_gps_time_x1000,
  int16_t elevation) {

  uint32_t dtime = gps_time_x1000 - last_gps_time_x1000;
  int16_t dspeed = speed_x1000 - last_speed_x1000;
  float accel = (float)dspeed / (float)dtime;

  float power = (MASS_IN_KG) * accel * ((float)speed_x1000 / 1000.0);

  power += calculate_power_lost_to_drag(float(speed_x1000) / 1000.0, EVORA_CD, EVORA_FRONT_AREA);
 
  last_speed_x1000 = speed_x1000;
  return power;
}
