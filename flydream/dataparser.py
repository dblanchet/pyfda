# vim:nosi:

import struct
import StringIO

from .exception import FlyDreamAltimeterProtocolError

from . import serialprotocol as sp

from collections import namedtuple
RawFlight = namedtuple('RawFlight', 'sampling_rate, data')
FlightRecord = namedtuple('FlightRecord', 'time, temperature, altitude')
Flight = namedtuple('Flight', 'index, sampling_freq, temperature_unit, '
                    'length_unit, records')


class DataParser:

    LENGTH_UNIT_METER = 0
    LENGTH_UNIT_FEET = 1

    TEMPERATURE_UNIT_CELSIUS = 0
    TEMPERATURE_UNIT_FAHRENHEIT = 1

    PRESSURE_REFERENCE = 101325  # Reference pressure (zero elevation).

    def __init__(self, length_unit=LENGTH_UNIT_METER,
                 temperature_unit=TEMPERATURE_UNIT_CELSIUS):
        self.length_unit = length_unit
        self.temperature_unit = temperature_unit

    def parse_header(self, header):
        '''Extract information from upload header.

        Header contains information about current
        storage occupation.

        Arguments:
        header -- Full raw binary upload header.

        Returns a (data size, max data size) tuple. '''

        # Sanity checks.
        expected_size = sp.RAW_DATA_HEADER_LENGTH
        if len(header) != expected_size:
            raise FlyDreamAltimeterProtocolError(
                    'Incorrect upload header size: found %d, expected %d'
                            % (len(header), expected_size))

        # First 8 bytes are a fixed byte sequence (write echo it seems).
        # Expected content is lenght + command echo:
        if header[:8] != sp.RESPONSE_UPLOAD:
            raise FlyDreamAltimeterProtocolError(
                    'Unexpected response header: found %s, expected %s'
                    % (repr(header[:8]), repr(sp.RESPONSE_UPLOAD)))

        # Last 4 bytes of header tell about device capacity usage.
        occupied, = struct.unpack('>I', header[8:])
        data_size = occupied - sp.EMPTY_ALTIMETER

        # Ensure data size is valid.
        if data_size < 0:
            raise FlyDreamAltimeterProtocolError(
                    'Negative data size: %d' % data_size)

        max_size = sp.FULL_ALTIMETER - sp.EMPTY_ALTIMETER
        if data_size > max_size:
            raise FlyDreamAltimeterProtocolError(
                    'Data size (%x) exceeds device capacity: %x'
                    % (data_size, max_size))

        return data_size, max_size

    def extract_flights(self, uploaded_data):
        ''' Parse raw data according to given units.'''
        return self._parse_raw_data(uploaded_data,
                self.length_unit, self.temperature_unit)

    def _make_flight(self, flight_data_chunck):
        # First byte of chunck tells us about sampling rate.
        # The remaining bytes are raw records.
        #
        # Expected pattern:
        #    <constant_byte> <sampling_rate> <data_records...>
        #
        # Ignore first byte, as it value does not
        # seem to be always compliant with specifications.
        return RawFlight(flight_data_chunck[1], flight_data_chunck[2:])

    def _split_raw_flight(self, data):
        chunks = data.split(sp.RAW_FLIGHTS_SEPARATOR)
        # Provide result as RawFlight objects.
        return [self._make_flight(chunk) for chunk in chunks if len(chunk) > 0]

    def _parse_raw_data(self, data, length_unit, temp_unit):
        # Raw data contains several flights in binary format.
        # First split them apart, then decode them.
        raw_flights = self._split_raw_flight(data)
        return [self._convert_raw_flight(raw_flight,
                                         index,
                                         length_unit,
                                         temp_unit)
                for index, raw_flight in enumerate(raw_flights)]

    def _convert_raw_flight(self, raw_flight, index, length_unit, temp_unit):
        # Get time interval according to sampling rate.
        hertz = {
                sp.FREQ_1_HERTZ: 1.0,
                sp.FREQ_2_HERTZ: 2.0,
                sp.FREQ_4_HERTZ: 4.0,
                sp.FREQ_8_HERTZ: 8.0,
        }[raw_flight.sampling_rate]
        timeslice = 1 / hertz

        # Flight data are 4 bytes records.
        if len(raw_flight.data) & 3 != 0:
            raise FlyDreamAltimeterProtocolError(
                    'Unexpected data size (not multiple of 4): %d' \
                            % len(raw_flight.data))

        # Convert each 4 bytes records.
        rel_time = 0.0
        data_stream = StringIO.StringIO(raw_flight.data)
        records = []
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
                records.append(FlightRecord(rel_time, temp, elevation))
            except IndexError:
                # No more data.
                break

            # Update timestamp.
            rel_time += timeslice

        return Flight(index, hertz, temp_unit, length_unit, records)

    def _to_fahrenheit(self, celsius):
        # Formula taken from Google search.
        return celsius * 9.0 / 5.0 + 32

    def _to_elevation(self, pressure, reference, unit):
        # Fly-Dream specifications provide this formula.
        meters = 44330 * (1 - (1.0 * pressure / reference) ** (1 / 5.255))

        # Convert to wanted units.
        if unit == self.LENGTH_UNIT_FEET:
            result = round(meters * 3.2808)
        else:
            result = round(meters, 1)

        return result
