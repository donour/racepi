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

from unittest import TestCase, main

from racepi.racetech.writers import *

DBC_FILENAME = "dbc/evora.dbc"


class RaceCaptureWriterTests(TestCase):

    def setUp(self):
        self.writer = RaceTechnologyDL1FeedWriter(DBC_FILENAME)
        self.assertFalse(self.writer.pending_messages)

    def test_send_steering_angle_zero(self):
        self.writer.send_steering_angle(0.0)
        self.assertEqual(1, len(self.writer.pending_messages))

    def test_send_steering_angle_positive(self):
        self.writer.send_steering_angle(1.0)
        self.assertEqual(1, len(self.writer.pending_messages))

    def test_send_steering_angle_negative(self):
        self.writer.send_steering_angle(-1.0)
        self.assertEqual(1, len(self.writer.pending_messages))

    def test_send_steering_angle_clip(self):
        self.writer.send_steering_angle(CLIP_STEERING_ANGLE+1)
        self.assertFalse(self.writer.pending_messages)
        self.writer.send_steering_angle((-CLIP_STEERING_ANGLE) - 1)

    def test_send_steering_angle_range_limit(self):
        self.writer.send_steering_angle(CLIP_STEERING_ANGLE-1e-4)
        self.assertEqual(1, len(self.writer.pending_messages))
        self.writer.send_steering_angle(-CLIP_STEERING_ANGLE+1e-4)
        self.assertEqual(2, len(self.writer.pending_messages))


if __name__ == "__main__":
    main()
