#!/usr/bin/env python3
# Copyright 2017 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.
from collections import defaultdict


class DataBuffer:
    """
    Simple collection of buffers for sensor data
    """
    def __init__(self):
        self.data = defaultdict(list)

    def add_sample(self, source_name, values):
        self.data[source_name].extend(values)

    def expire_old_samples(self, expire_time):
        """
        Expire (remove) all samples older than specified time
        :param expire_time: expiration age timestamp
        """
        for k in self.data:
            while self.data[k] and self.data[k][0][0] < expire_time:
                self.data[k].pop(0)

    def get_available_sources(self):
        return self.data.keys()

    def get_sensor_data(self, sensor_source):
        """
        Get data for specified source and clear buffer
        :param sensor_source: name of sensor source
        :return: data for specified sensor source
        """
        # fail early if an invalid source is requested
        if sensor_source not in self.data:
            raise ValueError("Invalid source specified")

        return self.data[sensor_source]

    def clear(self):
        self.data.clear()

