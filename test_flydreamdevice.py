#!/usr/bin/python

import unittest

import flydreamdevice
import StringIO


class SerialMock:

    def __init__(self, content):
        self._readBuf = StringIO.StringIO(content)
        self._writeBuf = ''

    def write(self, data):
        self._writeBuf += data
        return len(data)

    def read(self, size):
        return self._readBuf.read(size)

    def received(self):
        return self._writeBuf


class TestFlyDreamDevice(unittest.TestCase):

    def setUp(self):
        self._device = flydreamdevice.FlyDreamDevice()

    def tearDown(self):
        self._device = None

    def test_clear(self):
        expectedWrite = self._device.COMMAND_CLEAR
        expectedRead = self._device.RESPONSE_CLEAR
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        self._device.clear()

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_clear_incomplete_response(self):
        expectedRead = self._device.RESPONSE_CLEAR[:4]  # 8 bytes are expected.
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        with self.assertRaises(flydreamdevice.FlyDreamDeviceReadError):
            self._device.clear()

    def test_clear_incorrect_response(self):
        expectedRead = self._device.RESPONSE_UPLOAD
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        with self.assertRaises(flydreamdevice.FlyDreamDeviceProtocolError):
            self._device.clear()

    def test_setup_1_hertz(self):
        arg = self._device.FREQ_1_HERTZ
        expectedWrite = self._device.COMMAND_SETUP_PREFIX + arg
        expectedRead = self._device.RESPONSE_SETUP_PREFIX + arg
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        self._device.setup(flydreamdevice.FlyDreamDevice.FREQ_1_HERTZ)

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_setup_2_hertz(self):
        arg = self._device.FREQ_2_HERTZ
        expectedWrite = self._device.COMMAND_SETUP_PREFIX + arg
        expectedRead = self._device.RESPONSE_SETUP_PREFIX + arg
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        self._device.setup(flydreamdevice.FlyDreamDevice.FREQ_2_HERTZ)

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_setup_4_hertz(self):
        arg = self._device.FREQ_4_HERTZ
        expectedWrite = self._device.COMMAND_SETUP_PREFIX + arg
        expectedRead = self._device.RESPONSE_SETUP_PREFIX + arg
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        self._device.setup(flydreamdevice.FlyDreamDevice.FREQ_4_HERTZ)

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_setup_8_hertz(self):
        arg = self._device.FREQ_8_HERTZ
        expectedWrite = self._device.COMMAND_SETUP_PREFIX + arg
        expectedRead = self._device.RESPONSE_SETUP_PREFIX + arg
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        self._device.setup(flydreamdevice.FlyDreamDevice.FREQ_8_HERTZ)

        self.assertEqual(serialMock.received(), expectedWrite)

    def test_setup_invalid_argument(self):
        serialMock = SerialMock('')
        self._device._alt = serialMock

        with self.assertRaises(ValueError):
            self._device.setup(1)

        with self.assertRaises(ValueError):
            self._device.setup('1')

        with self.assertRaises(ValueError):
            self._device.setup(['1'])

        with self.assertRaises(ValueError):
            self._device.setup((1,))

    def test_setup_incomplete_response(self):
        arg = self._device.FREQ_4_HERTZ
        # 8 bytes are expected.
        expectedRead = (self._device.RESPONSE_SETUP_PREFIX + arg)[:4]
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        with self.assertRaises(flydreamdevice.FlyDreamDeviceReadError):
            self._device.setup(arg)

    def test_setup_incorrect_response(self):
        arg = self._device.FREQ_4_HERTZ
        expectedRead = self._device.RESPONSE_UPLOAD
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        with self.assertRaises(flydreamdevice.FlyDreamDeviceProtocolError):
            self._device.setup(arg)

    def test_parse_header(self):
        valid_header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x02\x07\x00'
        with self.assertRaises(flydreamdevice.FlyDreamDeviceProtocolError):
            self._device.parse_header(valid_header[:-1])  # Header too short.
        with self.assertRaises(flydreamdevice.FlyDreamDeviceProtocolError):
            self._device.parse_header(valid_header + 'a')  # Header too long.

        invalid_magic_seq = '\x07\x0E\xDA\x10\x00\xCA\x03\x00\x00\x02\x07\x00'
        #    Should be \x0f here ^
        with self.assertRaises(flydreamdevice.FlyDreamDeviceProtocolError):
            self._device.parse_header(invalid_magic_seq)  # Malformed header.

        negative_data_size = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x01\x07\x00'
        #                                     Should be \x02 here ^
        with self.assertRaises(flydreamdevice.FlyDreamDeviceProtocolError):
            self._device.parse_header(negative_data_size)  # Invalid data size.

        max_data_size = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\xFF\xFF\xFF\xFF'
        #                                         Max is \x00\x10\x00\x00
        with self.assertRaises(flydreamdevice.FlyDreamDeviceProtocolError):
            self._device.parse_header(max_data_size)  # Invalid data size.

        max_data_size = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x10\x00\x01'
        #                                         Max is \x00\x10\x00\x00
        with self.assertRaises(flydreamdevice.FlyDreamDeviceProtocolError):
            self._device.parse_header(max_data_size)  # Invalid data size.

        max_size = self._device.FULL_ALTIMETER - self._device.EMPTY_ALTIMETER

        # Empty device.
        header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x02\x00\x00'
        size, total = self._device.parse_header(header)
        self.assertEqual(size, 0, 'Incorrect data size')
        self.assertEqual(total, max_size, 'Incorrect max data size')

        # Arbitrary size.
        header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x02\x07\x00'
        size, total = self._device.parse_header(header)
        self.assertEqual(size, 0x700, 'Incorrect data size')
        self.assertEqual(total, max_size, 'Incorrect max data size')

        # Full device.
        header = '\x07\x0F\xDA\x10\x00\xCA\x03\x00\x00\x10\x00\x00'
        size, total = self._device.parse_header(header)
        self.assertEqual(size, max_size, 'Incorrect data size')
        self.assertEqual(total, max_size, 'Incorrect max data size')

    def test_upload(self):
        with open('test_flydreamdevice_sample.fda', 'rb') as f:
            sample = f.read()

        expectedWrite = self._device.COMMAND_UPLOAD
        serialMock = SerialMock(sample)
        self._device._alt = serialMock

        header, data = self._device.upload()

        self.assertEqual(serialMock.received(), expectedWrite)
        self.assertEqual(header, sample[:12])
        self.assertEqual(len(data), len(sample[12:]))

    def test_upload_incomplete_header(self):
        with open('test_flydreamdevice_sample.fda', 'rb') as f:
            sample = f.read()
        # 8 bytes are expected.
        expectedRead = sample[:6]
        serialMock = SerialMock(expectedRead)
        self._device._alt = serialMock

        with self.assertRaises(flydreamdevice.FlyDreamDeviceReadError):
            self._device.upload()


if __name__ == '__main__':
    unittest.main()
