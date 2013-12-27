#!/usr/bin/python

import unittest

from flydream.uploadeddata import UploadedData
from flydream.exception import FlyDreamAltimeterProtocolError
from flydream import serialprotocol as sp

from flydream.dataparser import DataParser, RawFlight

# TODO Test other distance and temperature units.


class TestFlyDreamDataParser(unittest.TestCase):

    max_size = sp.FULL_ALTIMETER - sp.EMPTY_ALTIMETER

    def setUp(self):
        self._parser = DataParser()

    def tearDown(self):
        self._parser = None

    def test_parse_header_too_short(self):
        valid_header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x02\x07\x00'
        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._parser.parse_header(valid_header[:-1])

    def test_parse_header_too_long(self):
        valid_header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x02\x07\x00'
        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._parser.parse_header(valid_header + 'a')

    def test_parse_header_invalid(self):
        invalid_magic_seq = '\x07\x0E\xDA\x10\x00\xCA\x03\x00\x00\x02\x07\x00'
        #    Should be \x0f here ^
        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._parser.parse_header(invalid_magic_seq)

    def test_parse_header_negative_data_size(self):
        negative_data_size = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x01\x07\x00'
        #                                     Should be \x02 here ^
        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._parser.parse_header(negative_data_size)

    def test_parse_header_too_much_data_a_lot(self):
        max_data_size = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\xFF\xFF\xFF\xFF'
        #                                         Max is \x00\x10\x00\x00
        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._parser.parse_header(max_data_size)

    def test_parse_header_too_much_data_little_bit(self):
        max_data_size = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x10\x00\x01'
        #                                         Max is \x00\x10\x00\x00
        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._parser.parse_header(max_data_size)

    def test_parse_header_empty_device(self):
        header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x02\x00\x00'
        size, total = self._parser.parse_header(header)
        self.assertEqual(size, 0, 'Incorrect data size')
        self.assertEqual(total, self.max_size, 'Incorrect max data size')

    def test_parse_header_arbitrary(self):
        header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x02\x07\x00'
        size, total = self._parser.parse_header(header)
        self.assertEqual(size, 0x700, 'Incorrect data size')
        self.assertEqual(total, self.max_size, 'Incorrect max data size')

    def test_parse_header_full(self):
        header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x10\x00\x00'
        size, total = self._parser.parse_header(header)
        self.assertEqual(size, self.max_size, 'Incorrect data size')
        self.assertEqual(total, self.max_size, 'Incorrect max data size')

    def test_raw_split_raw_flight_empty(self):
        result = self._parser._split_raw_flight('')
        self.assertEqual(0, len(result), 'Incorrect flight count')

    def test_raw_split_raw_flight_single(self):
        sample = UploadedData.from_file(
                'test/test_flydreamaltimeter_sample_1_flight.fda').data
        result = self._parser._split_raw_flight(sample)
        self.assertEqual(1, len(result), 'Incorrect flight count')

        flight, = result
        self.assertEqual('\x03', flight.sampling_rate)  # 8 hertz sampling.
        self.assertTrue(len(flight.data) > 0, 'Empty data')

    def test_raw_split_raw_flight_several(self):
        sample = UploadedData.from_file(
                'test/test_flydreamaltimeter_sample_2_flights.fda').data
        result = self._parser._split_raw_flight(sample)

        self.assertEqual(2, len(result), 'Incorrect flight count')
        first, second = result

        self.assertEqual('\x03', first.sampling_rate)  # 8 hertz sampling.
        self.assertTrue(len(first.data) > 0, 'Empty data')
        self.assertEqual(440 * 4, len(first.data), 'Incorrect data length')

        self.assertEqual('\x03', second.sampling_rate)  # 8 hertz sampling.
        self.assertTrue(len(second.data) > 0, 'Empty data')
        self.assertEqual(32, len(second.data), 'Incorrect data length')

    def test_convert_raw_flight_empty(self):
        flight = RawFlight('\x00', '')
        result = self._parser._convert_raw_flight(flight,
                DataParser.LENGTH_UNIT_METER,
                DataParser.TEMPERATURE_UNIT_CELSIUS)
        self.assertEqual(0, len(result.records), 'Incorrect flight count')
        self.assertEqual(1.0, result.sampling_freq, 'Incorrect sampling freq')

    def test_convert_raw_flight_wrong_length(self):
        sample = UploadedData.from_file(
                'test/test_flydreamaltimeter_sample_1_flight.fda').data
        flights = self._parser._split_raw_flight(sample)
        self.assertEqual(1, len(flights), 'Incorrect flight count')
        flight, = flights

        incorrect = RawFlight(flight.sampling_rate, flight.data[:-1])

        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._parser._convert_raw_flight(incorrect,
                    DataParser.LENGTH_UNIT_METER,
                    DataParser.TEMPERATURE_UNIT_CELSIUS)

    def test_convert_raw_flight_regular(self):
        # A "regular" flight with 440 records at 8 Hz.
        sample = UploadedData.from_file(
                'test/test_flydreamaltimeter_sample_1_flight.fda').data
        flights = self._parser._split_raw_flight(sample)
        self.assertEqual(1, len(flights), 'Incorrect flight count')
        flight, = flights

        result = self._parser._convert_raw_flight(flight,
                DataParser.LENGTH_UNIT_METER,
                DataParser.TEMPERATURE_UNIT_CELSIUS)
        self.assertTrue(len(result.records) > 0,
                'Incorrect flight record count')
        self.assertEqual(8.0, result.sampling_freq, 'Incorrect sampling freq')
        self.assertEqual(DataParser.LENGTH_UNIT_METER,
                result.length_unit, 'Incorrect length unit')
        self.assertEqual(DataParser.TEMPERATURE_UNIT_CELSIUS,
                result.temperature_unit, 'Incorrect temperature unit')

        # Test first record.
        seconds, celcius, meters = result.records[0]
        self.assertEqual(0.0, seconds, 'Invalid record timestamp')
        self.assertEqual(25, celcius, 'Invalid record temperature')
        self.assertAlmostEqual(63.6, meters, places=1,
                msg='Invalid record height')

        # Test arbitrary record.
        seconds, celcius, meters = result.records[9]
        self.assertEqual(1.125, seconds, 'Invalid record timestamp')
        self.assertEqual(25, celcius, 'Invalid record temperature')
        self.assertAlmostEqual(63.6, meters, places=1,
                msg='Invalid record height')

    def test_extract_flight(self):
        # A "regular" flight with 440 records at 8 Hz.
        sample = UploadedData.from_file(
                'test/test_flydreamaltimeter_sample_2_flights.fda')
        result = self._parser.extract_flights(sample.data)

        self.assertEqual(2, len(result), 'Incorrect flight count')
        first, second = result

        self.assertEqual(8, first.sampling_freq)  # 8 hertz sampling.
        self.assertTrue(len(first.records) > 0, 'Empty data')
        self.assertEqual(440, len(first.records), 'Incorrect data length')
        self.assertEqual(DataParser.LENGTH_UNIT_METER,
                first.length_unit, 'Incorrect length unit')
        self.assertEqual(DataParser.TEMPERATURE_UNIT_CELSIUS,
                first.temperature_unit, 'Incorrect temperature unit')

        self.assertEqual(8, second.sampling_freq)  # 8 hertz sampling.
        self.assertTrue(len(second.records) > 0, 'Empty data')
        self.assertEqual(8, len(second.records), 'Incorrect data length')
        self.assertEqual(DataParser.LENGTH_UNIT_METER,
                second.length_unit, 'Incorrect length unit')
        self.assertEqual(DataParser.TEMPERATURE_UNIT_CELSIUS,
                second.temperature_unit, 'Incorrect temperature unit')

    def test_convert_raw_flight_regular_farhenheit_feet(self):
        # A "regular" flight with 440 records at 8 Hz.
        sample = UploadedData.from_file(
                'test/test_flydreamaltimeter_sample_1_flight.fda').data
        flights = self._parser._split_raw_flight(sample)
        self.assertEqual(1, len(flights), 'Incorrect flight count')
        flight, = flights

        result = self._parser._convert_raw_flight(flight,
                DataParser.LENGTH_UNIT_FEET,
                DataParser.TEMPERATURE_UNIT_FAHRENHEIT)
        self.assertTrue(len(result.records) > 0,
                'Incorrect flight record count')
        self.assertEqual(8.0, result.sampling_freq, 'Incorrect sampling freq')
        self.assertEqual(DataParser.LENGTH_UNIT_FEET,
                result.length_unit, 'Incorrect length unit')
        self.assertEqual(DataParser.TEMPERATURE_UNIT_FAHRENHEIT,
                result.temperature_unit, 'Incorrect temperature unit')

        # Test first record.
        seconds, farhenheit, feet = result.records[0]
        self.assertEqual(0.0, seconds, 'Invalid record timestamp')
        self.assertEqual(77, farhenheit, 'Invalid record temperature')
        self.assertAlmostEqual(208, feet, places=1,
                msg='Invalid record height')

        # Test arbitrary record.
        seconds, farhenheit, feet = result.records[9]
        self.assertEqual(1.125, seconds, 'Invalid record timestamp')
        self.assertEqual(77, farhenheit, 'Invalid record temperature')
        self.assertAlmostEqual(209, feet, places=1,
                msg='Invalid record height')

    def test_convert_raw_flight_regular_farhenheit_meter(self):
        # A "regular" flight with 440 records at 8 Hz.
        sample = UploadedData.from_file(
                'test/test_flydreamaltimeter_sample_1_flight.fda').data
        flights = self._parser._split_raw_flight(sample)
        self.assertEqual(1, len(flights), 'Incorrect flight count')
        flight, = flights

        result = self._parser._convert_raw_flight(flight,
                DataParser.LENGTH_UNIT_METER,
                DataParser.TEMPERATURE_UNIT_FAHRENHEIT)
        self.assertTrue(len(result.records) > 0,
                'Incorrect flight record count')
        self.assertEqual(8.0, result.sampling_freq, 'Incorrect sampling freq')
        self.assertEqual(DataParser.LENGTH_UNIT_METER,
                result.length_unit, 'Incorrect length unit')
        self.assertEqual(DataParser.TEMPERATURE_UNIT_FAHRENHEIT,
                result.temperature_unit, 'Incorrect temperature unit')

        # Test first record.
        seconds, farhenheit, meters = result.records[0]
        self.assertEqual(0.0, seconds, 'Invalid record timestamp')
        self.assertEqual(77, farhenheit, 'Invalid record temperature')
        self.assertAlmostEqual(63.6, meters, places=1,
                msg='Invalid record height')

        # Test arbitrary record.
        seconds, farhenheit, meters = result.records[9]
        self.assertEqual(1.125, seconds, 'Invalid record timestamp')
        self.assertEqual(77, farhenheit, 'Invalid record temperature')
        self.assertAlmostEqual(63.6, meters, places=1,
                msg='Invalid record height')

    def test_convert_raw_flight_regular_celsius_meters(self):
        # A "regular" flight with 440 records at 8 Hz.
        sample = UploadedData.from_file(
                'test/test_flydreamaltimeter_sample_1_flight.fda').data
        flights = self._parser._split_raw_flight(sample)
        self.assertEqual(1, len(flights), 'Incorrect flight count')
        flight, = flights

        result = self._parser._convert_raw_flight(flight,
                DataParser.LENGTH_UNIT_METER,
                DataParser.TEMPERATURE_UNIT_FAHRENHEIT)
        self.assertTrue(len(result.records) > 0,
                'Incorrect flight record count')
        self.assertEqual(8.0, result.sampling_freq, 'Incorrect sampling freq')
        self.assertEqual(DataParser.LENGTH_UNIT_METER,
                result.length_unit, 'Incorrect length unit')
        self.assertEqual(DataParser.TEMPERATURE_UNIT_FAHRENHEIT,
                result.temperature_unit, 'Incorrect temperature unit')

        # Test first record.
        seconds, farhenheit, meters = result.records[0]
        self.assertEqual(0.0, seconds, 'Invalid record timestamp')
        self.assertEqual(77, farhenheit, 'Invalid record temperature')
        self.assertAlmostEqual(63.6, meters, places=1,
                msg='Invalid record height')

        # Test arbitrary record.
        seconds, farhenheit, meters = result.records[9]
        self.assertEqual(1.125, seconds, 'Invalid record timestamp')
        self.assertEqual(77, farhenheit, 'Invalid record temperature')
        self.assertAlmostEqual(63.6, meters, places=1,
                msg='Invalid record height')

    def test_various_sampling_frequencies(self):
        # 4 flights:
        #    0:      216 records @ 2Hz -   108.000 seconds
        #    1:      136 records @ 1Hz -   136.000 seconds
        #    2:      496 records @ 8Hz -    62.000 seconds
        #    3:      176 records @ 4Hz -    44.000 seconds
        sample = UploadedData.from_file(
                'test/test_freq_2_then_1_then_8_then_4.fda')
        result = self._parser.extract_flights(sample.data)

        self.assertEqual(4, len(result), 'Incorrect flight count')
        first, second, third, fourth = result

        self.assertEqual(2, first.sampling_freq)
        self.assertEqual(216, len(first.records), 'Incorrect data length')

        self.assertEqual(1, second.sampling_freq)
        self.assertEqual(136, len(second.records), 'Incorrect data length')

        self.assertEqual(8, third.sampling_freq)
        self.assertEqual(496, len(third.records), 'Incorrect data length')

        self.assertEqual(4, fourth.sampling_freq)
        self.assertEqual(176, len(fourth.records), 'Incorrect data length')


if __name__ == '__main__':
    unittest.main()
