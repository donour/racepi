#!/usr/bin/env python2
# Copyright 2016 Donour Sizemore
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
"""
Decoding and transform tools for CAN frames.
"""


class CanFrameValueExtractor:
    """
    This class extracts transformed frames from CanFrames. A
    transform must be specified at object construction and
    can be repeated applied to data.
    """

    def __init__(self, start_bit, bit_len, a=1, c=0, b=0, custom_transform=None):
        """
        Create extractor for a field within a CanDataFrame
        object. Specify the start bit and length to extract
        the desired field.

        The result can be transformed in a linear way by specifying
        coefficients:

        value = a( FIELD + b) + c

        Alternatively, a custom transform function can be specified

        :param start_bit: first bit of field, zero indexed
        :param bit_len: number of bits in field
        :param a:
        :param c:
        :param b:
        :param custom_transform: user-provided transform function
        """

        self.start = start_bit
        self.len = bit_len
        self.a = a
        self.b = b
        self.c = c
        self.transform = custom_transform

    def __get_field(self, payload):
        # extract field value from bytes
        field = 0
        for i in range(8):
            field <<= 8
            if i < len(payload):
                field += payload[i]

        bas = 64 - self.start  # bits after start
        mask = (field >> bas) << bas
        return (mask ^ field) >> (bas-self.len)

    def convert_frame(self, frame):
        """
        Convert the specified data frame to a
        scalar value.

        :param frame: CanFrame
        :return: translated value of specified field
        """
        if not frame or not frame.payload:
            raise ValueError("Missing frame payload")
        field = self.__get_field(frame.payload)
        if self.transform:
            return self.transform(field)
        return self.a*(field+self.b) + self.c


class CanFrame:
    """
    CAN frame object. Constructs internal bytearrays of data
    from various representations.
    """

    def __init__(self, arbitrationId, payload):
        """
        :param arbitrationId: hex string of arbId
        :param payload: hex string of data payload
        """
        self.arbId, self.payload = self.__from_message_strings(arbitrationId, payload)

    def __from_message_strings(self, arbitrationID, payload):
        # append leading zero to 11-bit ids
        if len(arbitrationID) == 3:
            arbitrationID = '0' + arbitrationID

        cid = bytearray.fromhex(arbitrationID)
        data = bytearray.fromhex(str(payload))
        return cid, data
