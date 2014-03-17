#!/usr/bin/python

import unittest

try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

from flydream.serialdevice import SerialDevice
from flydream.exception import FlyDreamAltimeterReadError, \
        FlyDreamAltimeterWriteError, \
        FlyDreamAltimeterSerialPortError, \
        FlyDreamAltimeterProtocolError

from flydream import serialprotocol as sp

UNEXISTING_PORT = 'unexisting'


class SerialMock:

    def __init__(self, content, write_len=None):
        self._readBuf = StringIO(content)
        self._writeBuf = b''

        self.write_len = write_len

        self.open_count = 0
        self.close_count = 0

    def open(self):
        self.open_count += 1

    def close(self):
        self.close_count += 1

    def write(self, data):
        self._writeBuf += data
        return len(data) if not self.write_len else self.write_len

    def read(self, size):
        return self._readBuf.read(size)

    def received(self):
        return self._writeBuf


class SerialDeviceMock(SerialDevice):

    def _open(self):
        self._serial_port = SerialMock(b'')
        self._serial_port.open()


class TestFlyDreamDevice(unittest.TestCase):

    def setUp(self):
        self._device = SerialDevice(UNEXISTING_PORT)

    def tearDown(self):
        self._device = None

    def test_clear(self):
        expectedWrite = sp.COMMAND_CLEAR
        expectedRead = sp.RESPONSE_CLEAR
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        self._device.clear()

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_clear_write_error(self):
        expectedRead = sp.RESPONSE_CLEAR
        serialMock = SerialMock(expectedRead, 4)  # 8 bytes should be written.
        self._device._serial_port = serialMock

        with self.assertRaises(FlyDreamAltimeterWriteError):
            self._device.clear()

    def test_clear_incomplete_response(self):
        expectedRead = sp.RESPONSE_CLEAR[:4]  # 8 bytes are expected.
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        with self.assertRaises(FlyDreamAltimeterReadError):
            self._device.clear()

    def test_clear_incorrect_response(self):
        expectedRead = sp.RESPONSE_UPLOAD
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._device.clear()

    def test_setup_1_hertz(self):
        arg = sp.FREQ_1_HERTZ
        expectedWrite = sp.COMMAND_SETUP_PREFIX + arg
        expectedRead = sp.RESPONSE_SETUP_PREFIX + arg
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        self._device.setup(sp.FREQ_1_HERTZ)

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_setup_2_hertz(self):
        arg = sp.FREQ_2_HERTZ
        expectedWrite = sp.COMMAND_SETUP_PREFIX + arg
        expectedRead = sp.RESPONSE_SETUP_PREFIX + arg
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        self._device.setup(sp.FREQ_2_HERTZ)

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_setup_4_hertz(self):
        arg = sp.FREQ_4_HERTZ
        expectedWrite = sp.COMMAND_SETUP_PREFIX + arg
        expectedRead = sp.RESPONSE_SETUP_PREFIX + arg
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        self._device.setup(sp.FREQ_4_HERTZ)

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_setup_8_hertz(self):
        arg = sp.FREQ_8_HERTZ
        expectedWrite = sp.COMMAND_SETUP_PREFIX + arg
        expectedRead = sp.RESPONSE_SETUP_PREFIX + arg
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        self._device.setup(sp.FREQ_8_HERTZ)

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_setup_invalid_argument(self):
        serialMock = SerialMock(b'')
        self._device._serial_port = serialMock

        with self.assertRaises(ValueError):
            self._device.setup(1)

        with self.assertRaises(ValueError):
            self._device.setup('1')

        with self.assertRaises(ValueError):
            self._device.setup(['1'])

        with self.assertRaises(ValueError):
            self._device.setup((1,))

    def test_setup_incomplete_response(self):
        arg = sp.FREQ_4_HERTZ
        # 8 bytes are expected.
        expectedRead = (sp.RESPONSE_SETUP_PREFIX + arg)[:4]
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        with self.assertRaises(FlyDreamAltimeterReadError):
            self._device.setup(arg)

    def test_setup_incorrect_response(self):
        arg = sp.FREQ_4_HERTZ
        expectedRead = sp.RESPONSE_UPLOAD
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        with self.assertRaises(FlyDreamAltimeterProtocolError):
            self._device.setup(arg)

    def test_upload(self):
        with open('tests/test_flydreamdevice_sample.fda', 'rb') as f:
            sample = f.read()

        expectedWrite = sp.COMMAND_UPLOAD
        serialMock = SerialMock(sample)
        self._device._serial_port = serialMock

        uploaded = self._device.upload()

        self.assertEqual(serialMock.received(), expectedWrite)
        self.assertEqual(uploaded.header, sample[:12])
        self.assertEqual(len(uploaded.data), len(sample[12:]))

    def test_upload_incomplete_header(self):
        with open('tests/test_flydreamdevice_sample.fda', 'rb') as f:
            sample = f.read()
        # 8 bytes are expected.
        expectedRead = sample[:6]
        serialMock = SerialMock(expectedRead)
        self._device._serial_port = serialMock

        with self.assertRaises(FlyDreamAltimeterReadError):
            self._device.upload()

    def test_upload_with_callback(self):
        with open('tests/test_flydreamdevice_sample.fda', 'rb') as f:
            sample = f.read()
        serialMock = SerialMock(sample)
        self._device._serial_port = serialMock
        total_len = len(sample) - sp.RAW_DATA_HEADER_LENGTH

        def callback(read, total):
            if read == 1000:
                self.assertEqual(total, total_len, 'Incorrect total lenght')
                return

            if read == total_len:
                self.assertEqual(total, total_len, 'Incorrect total lenght')
                return

            raise Exception('Incorrect callback arguments')

        self._device.upload(callback)

    def test_open_unexisting(self):
        with self.assertRaises(FlyDreamAltimeterSerialPortError):
            self._device._open()

    def test_serial_port_open_close(self):
        device = SerialDeviceMock(UNEXISTING_PORT)

        with device.opened():
            serial_port = device._serial_port
        open_count = serial_port.open_count
        close_count = serial_port.close_count

        self.assertEqual(device._serial_port, None, 'Incorrect serial port')
        self.assertEqual(open_count, 1, 'Incorrect open count')
        self.assertEqual(close_count, 1, 'Incorrect close count')

    def test_serial_port_open_close_with_exception(self):
        device = SerialDeviceMock(UNEXISTING_PORT)

        with self.assertRaises(IndexError):
            with device.opened():
                serial_port = device._serial_port
                raise IndexError
        open_count = serial_port.open_count
        close_count = serial_port.close_count

        self.assertEqual(open_count, 1, 'Incorrect open count')
        self.assertEqual(close_count, 1, 'Incorrect close count')


if __name__ == '__main__':
    unittest.main()
