#!/usr/bin/python

# TODO
#
# All
#  - Add licence to this code.
#  - Unit tests!
#  - Test on Linux (py2 and py3)
#  - Test on Mac (py3)
#  - Test on Windows (py2 and py3)
#
# Library
#  - Merge device and altimeter, split altimeter and parser.
#  - Error reporting (given/expected in exceptions).
#  - Do not open port when no interaction is required.
#  - Do not expose port primitives.
#
# CLI
#  - Seperate altimeter interaction and data writing.
#
# GUI (Tkinter)
#  - Start writing it.

import struct
import StringIO

from flydreamdevice import FlyDreamDevice

from collections import namedtuple
Flight = namedtuple('Flight', 'sampling_rate, data')


class FlyDreamAltimeter:
    ''' TODO '''

    LENGTH_UNIT_METER = 0
    LENGTH_UNIT_FEET = 1

    TEMPERATURE_UNIT_CELSIUS = 0
    TEMPERATURE_UNIT_FAHRENHEIT = 1

    PRESSURE_REFERENCE = 101325  # Reference pressure (zero elevation).

    def __init__(self, port=None,
                 length_unit=LENGTH_UNIT_METER,
                 temperature_unit=TEMPERATURE_UNIT_CELSIUS):
        self._communication = FlyDreamDevice(port)
        self._communication.open()

        # Public properties.
        self.length_unit = length_unit
        self.temperature_unit = temperature_unit

    @property
    def port(self):
        return self._communication.port

    def close(self):
        self._communication.close()

    def set_sampling_frequency(self, hertz):
        supported_rates = {
                1: FlyDreamDevice.FREQ_1_HERTZ,
                2: FlyDreamDevice.FREQ_2_HERTZ,
                4: FlyDreamDevice.FREQ_4_HERTZ,
                8: FlyDreamDevice.FREQ_8_HERTZ
        }

        if isinstance(hertz, float):
            int_hertz = int(hertz)
            if int_hertz != hertz:
                keys = sorted(supported_rates.keys())
                raise ValueError('Supported values are', keys)
            hertz = int_hertz

        try:
            # Ensure given argument is valid.
            freq = supported_rates[hertz]

            # Send sampling rate to device.
            return self._communication.setup(freq)
        except KeyError:
            keys = sorted(supported_rates.keys())
            raise ValueError('Supported values are', keys)

    def erase_flight_data(self):
        return self._communication.clear()

    def read_flight_data(self, callback=None):
        # Ensure argument is valid.
        if callback and not callable(callback):
            raise ValueError('callback argument must be callable')

        # Extract raw data from device.
        return self._communication.upload(callback)

    def convert_flight_data(self, raw_data):
        # Parse raw data according to given units.
        return self._parse_raw_data(raw_data,
                self.length_unit, self.temperature_unit)

    def parse_header(self, raw_header):
        # Header contains information about
        # current storage occupation.
        #
        # Return (actual data size, max data size) tuple.
        return self._communication.parse_header(raw_header)

    def _parse_raw_data(self, data, length_unit, temp_unit):
        # Raw data contains several flights in binary format.
        # First split them apart, then decode them.
        flights = self._split_flight(data)
        return [self._convert_to_readable(rate, values, length_unit, temp_unit)
                for rate, values in flights]

    def _make_flight(self, flight_data):
        return Flight(flight_data[0], flight_data[1:])

    def _split_flight(self, data):
        # Flights are separated by sequences of 32 bytes.
        # First 31 are known predefined bytes. Last one
        # tells us about sampling rate.
        record_prefix = '\xFF' * 30 + '\x00'  # Last byte should be \x03 (doc).
        chunks = data.split(record_prefix)
        # Provide result as (sampling_rate, values) couples.
        return [self._make_flight(chunk) for chunk in chunks if len(chunk) > 0]

    def _convert_to_readable(self, flight, length_unit, temp_unit):
        # Get time interval according to sampling rate.
        timeslice = {
                FlyDreamDevice.FREQ_1_HERTZ: 1.0,
                FlyDreamDevice.FREQ_2_HERTZ: 1.0 / 2,
                FlyDreamDevice.FREQ_4_HERTZ: 1.0 / 4,
                FlyDreamDevice.FREQ_8_HERTZ: 1.0 / 8,
        }[flight.sampling_rate]

        # Flight data are 4 bytes records.
        assert len(flight.data) & 3 == 0

        # Convert each 4 bytes records.
        rel_time = 0.0
        data_stream = StringIO.StringIO(flight.data)
        result = []
        while True:

            # Parse data.
            try:
                record = data_stream.read(4)

                # The first byte is the temperature in celsius degrees.
                temp_info, = struct.unpack('b', record[0])

                # The 3 last bytes are the pressure in Pascal.
                raw_pressure, = struct.unpack('>I', record)
                pressure = raw_pressure & 0x00FFFFFF  # Keep only last 3 bytes.

                # Convert values to suitable units.
                temp = temp_info
                if temp_unit == self.TEMPERATURE_UNIT_FAHRENHEIT:
                    temp = self._to_fahrenheit(temp_info)

                elevation = self._to_elevation(pressure,
                        self.PRESSURE_REFERENCE, length_unit)

                # Add to result.
                result.append((rel_time, temp, elevation))
            except IndexError:
                # No more data.
                break

            # Update timestamp.
            rel_time += timeslice

        assert len(result) == len(flight.data) / 4.0

        return result

    def _to_fahrenheit(self, celsius):
        return celsius * 9.0 / 5.0 + 32

    def _to_elevation(self, pressure, reference, unit):
        meters = 44330 * (1 - (1.0 * pressure / reference) ** (1 / 5.255))
        if unit == self.LENGTH_UNIT_FEET:
            result = round(meters * 3.2808)
        else:
            result = round(meters, 1)
        return result

# vim:nosi:
