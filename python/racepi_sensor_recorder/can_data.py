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


class CanFrameValueExtractor:

    def __init__(self, start_bit, bit_len, a=1, c=0, b=0):
        """
        Create extractor for a field within a CanDataFrame
        object. Specify the start bit and lengh and the
        value will be calculated as:

        value = a( FIELD + b) + c

        This allows for simple scaling and unit conversion.

        :param start_bit: first bit of field, zero indexed
        :param bit_len: number of bits in field
        :param a:
        :param c:
        :param b:
        """
        self.start = start_bit
        self.len = bit_len
        self.a = a
        self.b = b
        self.c = c

    def __get_field(self, payload):
        # extract field value from bytes
        field = 0
        for i in range(8):
            field <<= 8
            if i < len(payload):
                field += payload[i]
        return field

    def convert_frame(self, frame):
        if not frame or not frame.payload:
            raise ValueError("Missing frame payload")
        field = self.__get_field(frame.payload)
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
        if isinstance(arbitrationId, str) and isinstance(payload, str):
            self.arbId, self.payload = self.__from_message_strings(arbitrationId, payload)

        else:
            raise ValueError("Illegal arguments : (%s,%s)" %
                             (type(arbitrationId), type(payload)))

    def __from_message_strings(self, arbitrationID, payload):
        # append leading zero to 11-bit ids
        if len(arbitrationID) == 3:
            arbitrationID = '0' + arbitrationID

        cid = bytearray.fromhex(arbitrationID)
        data = bytearray.fromhex(payload)
        return cid, data
