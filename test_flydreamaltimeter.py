#!/usr/bin/python

import unittest

from flydreamaltimeter import FlyDreamAltimeter, Flight
import flydreamdevice

UNEXISTING_PORT = 'unexisting'


class FlyDreamDevice_TestHelper:

    def open(self):
        pass

    def close(self):
        pass

    def clear(self):
        pass

    def setup(self, sampling_freq):
        pass

    def upload(self, callback=None):
        pass


class FlyDreamAltimeter_TestHelper(FlyDreamAltimeter):

    def __init__(self):
        try:
            FlyDreamAltimeter.__init__(self, port=UNEXISTING_PORT)
        except flydreamdevice.FlyDreamDeviceSerialPortError:
            pass
        self._communication = FlyDreamDevice_TestHelper()
        self.length_unit = FlyDreamAltimeter.LENGTH_UNIT_METER
        self.temperature_unit = FlyDreamAltimeter.TEMPERATURE_UNIT_CELSIUS


class TestFlyDreamDevice(unittest.TestCase):

    def setUp(self):
        self._altimeter = FlyDreamAltimeter_TestHelper()

    def tearDown(self):
        self._altimeter = None

    def test_open(self):
        assert self._altimeter

    def test_setup(self):
        with self.assertRaises(ValueError):
            self._altimeter.set_sampling_frequency('a')  # Not a number.
        with self.assertRaises(ValueError):
            self._altimeter.set_sampling_frequency(None)  # Not a number.
        with self.assertRaises(ValueError):
            self._altimeter.set_sampling_frequency(4.5)  # Not an int number.
        with self.assertRaises(ValueError):
            self._altimeter.set_sampling_frequency(-1)  # Negative number.
        with self.assertRaises(ValueError):
            self._altimeter.set_sampling_frequency(3)  # Unsupported number.
        with self.assertRaises(ValueError):
            self._altimeter.set_sampling_frequency(10)  # Too high number.

        # These ones should not raise exceptions:
        self._altimeter.set_sampling_frequency(1)
        self._altimeter.set_sampling_frequency(1.0)
        self._altimeter.set_sampling_frequency(2)
        self._altimeter.set_sampling_frequency(2.0)
        self._altimeter.set_sampling_frequency(4)
        self._altimeter.set_sampling_frequency(4.0)
        self._altimeter.set_sampling_frequency(8)
        self._altimeter.set_sampling_frequency(8.0)

    def test_read_flight_data_callback_not_callable(self):
        with self.assertRaises(ValueError):
            self._altimeter.read_flight_data('a')  # Not callable argument.

        # These ones should not raise exceptions:
        self._altimeter.read_flight_data()
        self._altimeter.read_flight_data(None)
        self._altimeter.read_flight_data(lambda x: x)

    def test_raw_upload_data_split_flight(self):
        # Empty data.
        result = self._altimeter._split_flight('')
        self.assertEqual(0, len(result), 'Incorrect flight count')

        # A single flight.
        with open('test_flydreamaltimeter_sample_1_flight.fda', 'rb') as f:
            sample = f.read()[12:]  # Remove header from sample.
        result = self._altimeter._split_flight(sample)
        self.assertEqual(1, len(result), 'Incorrect flight count')

        flight, = result
        self.assertEqual('\x03', flight.sampling_rate)  # 8 hertz sampling.
        self.assertTrue(len(flight.data) > 0, 'Empty data')

        # Several flights.
        with open('test_flydreamaltimeter_sample_2_flights.fda', 'rb') as f:
            sample = f.read()[12:]  # Remove header from sample.
        result = self._altimeter._split_flight(sample)

        self.assertEqual(2, len(result), 'Incorrect flight count')
        first, second = result

        self.assertEqual('\x03', first.sampling_rate)  # 8 hertz sampling.
        self.assertTrue(len(first.data) > 0, 'Empty data')
        self.assertEqual(440 * 4, len(first.data), 'Incorrect data length')

        self.assertEqual('\x03', second.sampling_rate)  # 8 hertz sampling.
        self.assertTrue(len(second.data) > 0, 'Empty data')
        self.assertEqual(32, len(second.data), 'Incorrect data length')

    def test_convert_to_readable(self):
        # Empty data.
        flight = Flight('\x00', '')
        result = self._altimeter._convert_to_readable(flight,
                FlyDreamAltimeter.LENGTH_UNIT_METER,
                FlyDreamAltimeter.TEMPERATURE_UNIT_CELSIUS)
        self.assertEqual(0, len(result), 'Incorrect flight count')

        # A "regular" flight, 440 records at 8 Hz.
        with open('test_flydreamaltimeter_sample_1_flight.fda', 'rb') as f:
            sample = f.read()[12:]  # Remove header from sample.
        flights = self._altimeter._split_flight(sample)
        self.assertEqual(1, len(flights), 'Incorrect flight count')
        flight, = flights

        result = self._altimeter._convert_to_readable(flight,
                FlyDreamAltimeter.LENGTH_UNIT_METER,
                FlyDreamAltimeter.TEMPERATURE_UNIT_CELSIUS)
        self.assertTrue(len(result) > 0, 'Incorrect flight record count')

        # Test first record.
        seconds, celcius, meters = result[0]
        self.assertEqual(0.0, seconds, 'Invalid record timestamp')
        self.assertEqual(25, celcius, 'Invalid record temperature')
        self.assertAlmostEqual(63.6, meters, places=1,
                msg='Invalid record height')

        # Test arbitrary record.
        seconds, celcius, meters = result[9]
        self.assertEqual(1.125, seconds, 'Invalid record timestamp')
        self.assertEqual(25, celcius, 'Invalid record temperature')
        self.assertAlmostEqual(63.6, meters, places=1,
                msg='Invalid record height')

    def test_convert_to_readable_invalid(self):
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()
