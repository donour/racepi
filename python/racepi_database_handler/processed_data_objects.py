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

from .objects import Base, CANData
from racepi_can_decoder import CanFrame


class ProcessedCANSample(CANData):

    def value(self, can_frame_value_extractor):
        # convert fields to can frame and extract value
        # arbitration id is not used in conversion
        f = CanFrame("000", self.msg)
        return can_frame_value_extractor.convert_frame(f)
