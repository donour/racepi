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
import itertools
from math import tan


def uptime_helper():
    """Simple helper function to get the current system uptime in seconds on Linux"""
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds
    return -1.0


def merge_and_generate_ordered_log(data):
    """
    This utility function takes a data object of the type
    { source: [ (timestamp, (values,...)), ... ], ... } and returns
    a new list of (source, timestamp, (values,...)) for outputting
    as a multi-source stream.

    :param data:
    :return:
    """
    vals_with_keys = [[(key,) + val for val in data[key]] for key in data.keys()]
    flat_data = list(itertools.chain.from_iterable(vals_with_keys))
    flat_data.sort(key=lambda x: x[1])  # sort by time
    return flat_data


def safe_speed_to_float(v):
    """
    convert speed value to float in typesafe way
    :param v:
    :return: float value of v, 0.0 if conversion fails
    """
    if not v:
        return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0


def oversteer_coefficient(steering_angle, wheelbase, velocity, yaw_rate):
    """
    Calculate the difference of requested yaw to actual. Values > 0 are
    oversteer, values 0 1 are understeer.
    
    :param steering_angle: in radians
    :param wheelbase: in meters
    :param velocity: in meters/second
    :param yaw_rate: in radians/sec
    :return: ratio
    """

    # TODO, this has not been thoroughly tested

    if steering_angle > 1e-5:
        requested_turn_radius = wheelbase / tan(steering_angle)
        requested_yaw_rate = velocity / requested_turn_radius
    else:
        requested_yaw_rate = 0.0

    return requested_yaw_rate - yaw_rate


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
            v = sample[1]
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
            try:
                # this try catch is REALLY stupid, but python iterators can't
                # detect the end
                while next_dist[0] < sample:
                    last_dist = next_dist
                    next_dist = next(dist_iter)
            except:
                pass
            # linear interpolation of last distance sample
            # before and after the target sample
            if next_dist[2] > 1e-4:
                interpolated_distance = \
                    (sample-last_dist[0])/next_dist[2] * next_dist[3] + last_dist[1]
            else:
                interpolated_distance = 0.0

            result.append(interpolated_distance)

        if len(time_trace) != len(result):
            print("Warning: distance samples dropped")

        return result



