#!/usr/bin/python

from __future__ import print_function
try:
    import serial
except ImportError:
    print('''This software requires "pyserial" to be installed on your computer
Please visit http://pyserial.sourceforge.net/pyserial.html#installation''')

import struct

import platform


def default_serial_port():
    MAC_SERIAL_PORT = '/dev/tty.SLAB_USBtoUART'
    LINUX_SERIAL_PORT = '/dev/ttyUSB0'
    WINDOWS_SERIAL_PORT = 'COM3'

    system = platform.system()
    return {
        'Windows': WINDOWS_SERIAL_PORT,
        'Darwin': MAC_SERIAL_PORT,
        'Linux': LINUX_SERIAL_PORT
    }[system]


class FlyDreamDeviceException(Exception): pass

class FlyDreamDeviceSerialPortError(FlyDreamDeviceException): pass
class FlyDreamDeviceWriteError(FlyDreamDeviceException): pass
class FlyDreamDeviceReadError(FlyDreamDeviceException): pass
class FlyDreamDeviceProtocolError(FlyDreamDeviceException): pass


class FlyDreamDevice:
    ''' Implement FlyDream Altimeter low level serial protocol.'''

    # Supported sampling frequencies.
    FREQ_1_HERTZ = '\x00'
    FREQ_2_HERTZ = '\x01'
    FREQ_4_HERTZ = '\x02'
    FREQ_8_HERTZ = '\x03'

    # Serial commands.
    COMMAND_CLEAR = '\x0F\xDA\x10\x00\xCC\03\x00'
    COMMAND_UPLOAD = '\x0F\xDA\x10\x00\xCA\03\x00'
    COMMAND_SETUP_PREFIX = '\x0F\xDA\x10\x00\xCA\03'

    # Serial commands expected responses.
    RESPONSE_CLEAR = '\x07\x0F\xDA\x10\x00\xCC\03\x00'
    RESPONSE_UPLOAD = '\x07\x0F\xDA\x10\x00\xCA\03\x00'
    RESPONSE_SETUP_PREFIX = '\x07\x0F\xDA\x10\x00\xCA\03'

    # Device capacity information.
    EMPTY_ALTIMETER = 0x020000
    FULL_ALTIMETER = 0x100000

    # Data chunks size when reading.
    DATA_CHUNK_SIZE = 1000

    # Read timeout.
    READ_TIMEOUT = 20.0  # Seconds

    def __init__(self, port=None):
        self._port = port if port else default_serial_port()
        self._baudrate = 19200
        self._timeout = 30  # Read timeout, in seconds.
        self._alt = None

    def open(self):
        '''Open serial port.

        This method must be called before any other interaction.

        This method is separated to ease tests.'''
        try:
            self._alt = serial.Serial(
                    self._port,
                    baudrate=self._baudrate,
                    timeout=self.READ_TIMEOUT)
        except OSError:
            raise FlyDreamDeviceSerialPortError(
                    'Could not open serial port %s' % self._port)

    @property
    def port(self):
        return self._port

    def close(self):
        '''Close serial port.

        Do not forget to call this method after use.'''
        self._alt.close()
        self._alt = None

    def clear(self):
        '''Reset the device flight data.

        Return True if data is correctly reset.

        This command may take a while to execute (10 seconds or so).'''

        # Send reset flight data command.
        self._write(self.COMMAND_CLEAR)

        # Read response.
        # Expected response is command lenght + command echo:
        response = self._read(len(self.RESPONSE_CLEAR))
        if response != self.RESPONSE_CLEAR:
            raise FlyDreamDeviceProtocolError('Unexpected response: %s'
                    % response)

        return True

    def parse_header(self, header):
        '''Extract information from upload header.

        Arguments:
        header -- Full raw binary upload header.

        Returns a (data size, max data size) tuple. '''

        # Sanity checks.
        expected_size = 12
        if len(header) != expected_size:
            raise FlyDreamDeviceProtocolError(
                    'Incorrect upload header size (%d given, expected %d)' %
                    (len(header), expected_size))

        # First 8 bytes are a fixed byte sequence (write echo it seems).
        # Expected content is lenght + command echo:
        if header[:8] != self.RESPONSE_UPLOAD:
            raise FlyDreamDeviceProtocolError(
                    'Unexpected response header: %s, expected %s'
                    % (repr(header[:8]), repr(self.RESPONSE_UPLOAD)))

        # Last 4 bytes of header tell about device capacity usage.
        occupied, = struct.unpack('>I', header[8:])
        data_size = occupied - self.EMPTY_ALTIMETER

        # Ensure data size is valid.
        if data_size < 0:
            raise FlyDreamDeviceProtocolError(
                    'Negative data size: %d' % data_size)

        max_size = self.FULL_ALTIMETER - self.EMPTY_ALTIMETER
        if data_size > max_size:
            raise FlyDreamDeviceProtocolError(
                    'Data size (%x) exceeds device capacity: %x'
                    % (data_size, max_size))

        return data_size, max_size

    def upload(self, callback=None):
        '''Retrieve raw flight data.

        The altimeter flight data is split between header and content.
        This method parse the header to know how much data it must read
        from the device.

        The result is given a (header, data) tuple.count.

        Keyword arguments:
        callback -- A callable that take (int, int) argument (default: None).

        The first argument of the callback is the read byte count.
        The second argument is the total data size.

        callback example:
            def on_progress(read_size, total_size):
                ...

        NOTE: Take care not to perform blocking actions
              in your callback implementation.'''

        # Send flight data retrieval command.
        self._write(self.COMMAND_UPLOAD)

        # 1. Header is 12 bytes.
        header = self._read(12)
        data_size, _ = self.parse_header(header)

        # 2. Next read the flight data.
        data = ''
        remaining = data_size
        while remaining > 0:
            # Read some data.
            n = self.DATA_CHUNK_SIZE if remaining > self.DATA_CHUNK_SIZE \
                    else remaining
            data += self._alt.read(n)

            # Tell about progression.
            if callback:
                callback(len(data), data_size)

            # Check for more data.
            remaining = data_size - len(data)

        # Provide raw data. Parsing is caller's responsibility.
        return (header, data)

    def setup(self, rate):
        '''Change sampling frequency setting.

        Return True if sampling frequency is correctly set.

        Argument:
        rate -- Wanted sampling rate

        Example:
            device.setup(FlyDreamDevice.FREQ_2_HERTZ)
        '''

        # Check argument validity.
        if rate not in [self.FREQ_1_HERTZ, self.FREQ_2_HERTZ,
                self.FREQ_4_HERTZ, self.FREQ_8_HERTZ]:
            raise ValueError('Invalid argument')

        # Send new sampling frequency command.
        command = self.COMMAND_SETUP_PREFIX + rate
        self._write(command)

        # Read response.
        # Expected response is command lenght + command echo:
        response = self._read(len(self.RESPONSE_SETUP_PREFIX) + 1)
        if response != self.RESPONSE_SETUP_PREFIX + rate:
            raise FlyDreamDeviceProtocolError('Unexpected response: %s'
                    % response)

        return True

    def _write(self, command):
        # Write and check written byte count.
        written = self._alt.write(command)
        if written != len(command):
            raise FlyDreamDeviceWriteError('Error while writing %s'
                    '(sent: %d, reported: %d)'
                    % (command, len(command), written))

    def _read(self, size):
        # Write and check read byte count.
        # read() should be blocking when data is not available...
        data = self._alt.read(size)
        if len(data) != size:
            raise FlyDreamDeviceReadError('Error while reading')
        return data
