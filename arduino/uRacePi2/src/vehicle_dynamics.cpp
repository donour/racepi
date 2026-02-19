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

#include <math.h>
#include <stddef.h>
#include <Arduino.h>
#include "vehicle_dynamics.h"

dynamics_state_t dynamics_state;

// Estimate available friction (mu) from lateral acceleration using
// peak-hold with exponential decay. The decay rate is tuned for ~50Hz
// IMU updates; mu decays toward zero with a time constant of ~10s.
void update_mu_estimate(dynamics_state_t *state) {
  if (NULL == state) {
    return;
  }
  const float decay = 0.998f;
  const float min_mu = 0.3f; // minimum friction to prevent divide-by-zero and excessive sensitivity
  float abs_lat = fabsf(state->lat_accel_g);
  float decayed_mu = fmax(min_mu,  state->mu * decay);
  state->mu = fmaxf(abs_lat, decayed_mu);
}


// Compute understeer coefficient (K) as yaw rate ratio:
//   actual_yaw / corrected_reference_yaw
//   < 1.0 = understeer, > 1.0 = oversteer, 1.0 = neutral
//
// Reference yaw rate from bicycle model with tire saturation correction:
//   yaw_ref = V * tan(delta_road) / L * (1 - grip_ratio^2)
//   grip_ratio = a_y / (mu * g)
//
float compute_steering_gradient(dynamics_state_t *state) {
  if (NULL == state) {
    return -1.0f;
  }

  float speed_ms = state->speed_ms;
  float steering_wheel_deg = state->steering_wheel_deg;
  float yaw_rate_dps = state->yaw_rate_dps;
  float lat_accel_g = state->lat_accel_g;
  float mu = state->mu;

  // Need meaningful speed and steering input to compute a ratio
  if (fabsf(speed_ms) < 3.0f || fabsf(steering_wheel_deg) < 5.0f) {
    return 1.0f;
  }

  float delta_road_rad = (steering_wheel_deg / EVORA_STEERING_RATIO) * DEG_TO_RAD;
  float yaw_ref = speed_ms * tanf(delta_road_rad) / EVORA_WHEELBASE_M;
  float yaw_ref_dps = yaw_ref / DEG_TO_RAD;

  if (fabsf(yaw_ref_dps) < 0.5f) {
    return 1.0f;
  }

  // Tire saturation correction: reduce expected yaw rate as lateral
  // acceleration approaches the friction limit (mu * g)
  float grip_ratio = fabsf(lat_accel_g) / mu;
  if (grip_ratio > 1.0f) grip_ratio = 1.0f;
  float saturation = 1.0f - grip_ratio * grip_ratio;
  yaw_ref_dps *= saturation;

  if (fabsf(yaw_ref_dps) < 0.5f) {
    return 1.0f;
  }

  return yaw_rate_dps / yaw_ref_dps;
}
