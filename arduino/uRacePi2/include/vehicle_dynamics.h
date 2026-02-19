/**************************************************************************
    Copyright 2020-2026 Donour Sizemore

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

#ifndef __VEHICLE_DYNAMICS_H_
#define __VEHICLE_DYNAMICS_H_

#define EVORA_WHEELBASE_M (2.575f)
#define EVORA_STEERING_RATIO (16.0f)

// steering_wheel_deg: steering wheel angle in degrees
// speed_ms:           vehicle speed in m/s
// yaw_rate_dps:       actual yaw rate in deg/s from IMU
// lat_accel_g:        lateral acceleration in g's from IMU
// mu:                 estimated friction coefficient (peak-hold with decay from lateral accel)
typedef struct {
  float steering_wheel_deg;
  float speed_ms;
  float yaw_rate_dps;
  float lat_accel_g;
  float mu;
} dynamics_state_t;

extern dynamics_state_t dynamics_state;

void update_mu_estimate(dynamics_state_t *state);
float compute_steering_gradient(dynamics_state_t *state);

#endif // __VEHICLE_DYNAMICS_H_
