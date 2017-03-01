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


class TimeToDistanceConverter:
    """
    This is a utility class for converting samples timestamps to distance deltas
    withing a recording
    """

    def __init__(self, speed_data):

        # calculate distance trace

        if not speed_data or len(speed_data) < 2:
            raise ValueError("Insufficient data provided")

        self.distance_samples = []

        t_last = speed_data[0][0]
        total_distance = 0.0

        for sample in speed_data[1:]:

            t = sample[0]
            v = sample[1]['speed']
            t_delta = t-t_last
            t_last = t

            # TODO: interpolate v from multiple samples
            d_delta = t_delta * v
            total_distance = total_distance + d_delta
            self.distance_samples.append((t, total_distance, t_delta, d_delta))

    def generate_distance_trace(self, time_trace):

        if not self.distance_samples:
            raise RuntimeError("No distance data available")

        result = []

        dist_iter = iter(self.distance_samples)
        last_dist = next(dist_iter)
        next_dist = next(dist_iter)

        for sample in time_trace:
            # find next distance sample if necessary
            while next_dist and next_dist[0] < sample[0]:
                last_dist = next_dist
                next_dist = next(dist_iter)

            # linear interpolation of last distance sample
            # before and after the target sample
            interpolated_distance = \
                (sample[0]-last_dist[0])/next_dist[2] * next_dist[3] + last_dist[1]

            result.append((interpolated_distance, sample[1]))

        return result



