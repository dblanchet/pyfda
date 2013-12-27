#!/usr/bin/python

import unittest

from flydream.altimeter import Altimeter

from flydream.exception import FlyDreamAltimeterSerialPortError

from contextlib import contextmanager

UNEXISTING_PORT = 'unexisting'


class SerialDevice_TestHelper:

    @contextmanager
    def opened(self):
        yield self

    def clear(self):
        return True

    def setup(self, sampling_freq):
        pass

    def upload(self, callback=None):
        pass


class Altimeter_TestHelper(Altimeter):

    def __init__(self):
        Altimeter.__init__(self, port=UNEXISTING_PORT)
        self._device = SerialDevice_TestHelper()


class TestFlyDreamDevice(unittest.TestCase):

    def setUp(self):
        self._altimeter = Altimeter_TestHelper()

    def tearDown(self):
        self._altimeter = None

    def test_open(self):
        assert self._altimeter

    def test_port_getter(self):
        self.assertEqual(self._altimeter.port, UNEXISTING_PORT,
                'Incorrect port')

    def test_setup(self):
        with self.assertRaises(ValueError):
            self._altimeter.setup('a')  # Not a number.
        with self.assertRaises(ValueError):
            self._altimeter.setup(None)  # Not a number.
        with self.assertRaises(ValueError):
            self._altimeter.setup(4.5)  # Not an int number.
        with self.assertRaises(ValueError):
            self._altimeter.setup(-1)  # Negative number.
        with self.assertRaises(ValueError):
            self._altimeter.setup(3)  # Unsupported number.
        with self.assertRaises(ValueError):
            self._altimeter.setup(10)  # Too high number.

        # These ones should not raise exceptions:
        self._altimeter.setup(1)
        self._altimeter.setup(1.0)
        self._altimeter.setup(2)
        self._altimeter.setup(2.0)
        self._altimeter.setup(4)
        self._altimeter.setup(4.0)
        self._altimeter.setup(8)
        self._altimeter.setup(8.0)

    def test_read_flight_data_callback_not_callable(self):
        with self.assertRaises(ValueError):
            self._altimeter.upload('a')  # Not callable argument.

        # These ones should not raise exceptions:
        self._altimeter.upload()
        self._altimeter.upload(None)
        self._altimeter.upload(lambda x: x)

    def test_clear(self):
        # Just running after coverage rate...
        self.assertTrue(self._altimeter.clear(), 'Incorrect return value')


if __name__ == '__main__':
    unittest.main()
