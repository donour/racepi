# Copyright 2017 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

from racepi.can.can_data import CanFrameValueExtractor
from math import pi
import ctypes

# Focus RS Mk3 CAN converters
focus_rs_steering_angle_converter       = CanFrameValueExtractor(49, 15, a=(pi/0x1000))
focus_rs_steering_direction_converter   = CanFrameValueExtractor(32, 1)
focus_rs_tps_converter                  = CanFrameValueExtractor(6, 10, a=0.1)
focus_rs_rpm_converter                  = CanFrameValueExtractor(36, 12, a=2.0)
focus_rs_brake_pressure_converter       = CanFrameValueExtractor(24, 16, a=1e-3)
focus_rs_wheelspeed1_converter          = CanFrameValueExtractor(1, 15, a=1/307.0)
focus_rs_wheelspeed2_converter          = CanFrameValueExtractor(17, 15, a=1/307.0)
focus_rs_wheelspeed3_converter          = CanFrameValueExtractor(33, 15, a=1/307.0)
focus_rs_wheelspeed4_converter          = CanFrameValueExtractor(49, 15, a=1/307.0)

lotus_evora_s1_rpm_converter            = CanFrameValueExtractor(1, 15)
lotus_evora_s1_tps_converter            = CanFrameValueExtractor(24, 8, a=100.0/0xFB)
lotus_evora_s1_steering_angle_converter = CanFrameValueExtractor(0, 16,
                                                                 custom_transform=lambda v: ctypes.c_short(v).value)

