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
#ifndef __ESP32_CAN_PROCESSOR_
#define __ESP32_CAN_PROCESSOR_

// TODO: configure RX filters

// Configure ESP32 CAN driver with specified TX/RX pins.
// returns:
//        -1 on install failure
//        -2 on setup failure
int16_t setup_can_driver(uint8_t tx_gpio, uint8_t rx_gpio);

#endif//__ESP32_CAN_PROCESSOR_
