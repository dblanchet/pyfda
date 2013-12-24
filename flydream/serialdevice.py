try:
    import serial
except ImportError:
    print('''This software requires "pyserial" to be installed on your computer
Please visit http://pyserial.sourceforge.net/pyserial.html#installation''')

from contextlib import contextmanager

from .exception import FlyDreamAltimeterReadError, \
        FlyDreamAltimeterWriteError, \
        FlyDreamAltimeterSerialPortError, \
        FlyDreamAltimeterProtocolError

import serialprotocol as sp

from dataparser import DataParser
from uploadeddata import UploadedData


class SerialDevice:

    # Data chunks size when reading.
    DATA_CHUNK_SIZE = 1000

    # Read timeout.
    READ_TIMEOUT = 20.0  # Seconds

    def __init__(self, port):
        self._port = port
        self._baudrate = 19200
        self._timeout = 30  # Read timeout, in seconds.

    def _open(self):
        '''Open serial port.

        This method must be called before any serial interaction.

        This method is separated to ease tests.'''
        try:
            self._serial_port = serial.Serial(
                    self._port,
                    baudrate=self._baudrate,
                    timeout=self.READ_TIMEOUT)
        except OSError:
            raise FlyDreamAltimeterSerialPortError(
                    'Could not open serial port %s' % self._port)

    def _close(self):
        '''Close serial port.

        Do not forget to call this method after use.'''
        self._serial_port.close()
        self._serial_port = None

    @contextmanager
    def opened(self):
        self._open()
        try:
            yield self
        finally:
            self._close()

    def clear(self):
        # Send reset flight data command.
        self._write(sp.COMMAND_CLEAR)

        # Read response.
        # Expected response is command length + command echo:
        response = self._read(len(sp.RESPONSE_CLEAR))
        if response != sp.RESPONSE_CLEAR:
            raise FlyDreamAltimeterProtocolError('Unexpected response: %s'
                    % response)

        return True

    def setup(self, rate):
        # Check argument validity.
        if rate not in [sp.FREQ_1_HERTZ, sp.FREQ_2_HERTZ,
                sp.FREQ_4_HERTZ, sp.FREQ_8_HERTZ]:
            raise ValueError('Invalid rate argument')

        # Send new sampling frequency command.
        command = sp.COMMAND_SETUP_PREFIX + rate
        self._write(command)

        # Read response.
        # Expected response is command length + command echo:
        response = self._read(len(sp.RESPONSE_SETUP_PREFIX) + 1)
        if response != sp.RESPONSE_SETUP_PREFIX + rate:
            raise FlyDreamAltimeterProtocolError('Unexpected response: %s'
                    % response)

        return True

    def upload(self, callback=None):
        # Send flight data retrieval command.
        self._write(sp.COMMAND_UPLOAD)

        # 1. Header is fixed-length.
        header = self._read(sp.RAW_DATA_HEADER_LENGTH)
        data_size, _ = DataParser().parse_header(header)

        # 2. Next read the flight data.
        data = ''
        remaining = data_size
        while remaining > 0:
            # Read some data.
            n = self.DATA_CHUNK_SIZE if remaining > self.DATA_CHUNK_SIZE \
                    else remaining
            data += self._serial_port.read(n)

            # Tell about progression.
            if callback:
                callback(len(data), data_size)

            # Check for more data.
            remaining = data_size - len(data)

        # Provide raw data. Flight parsing is caller's responsibility.
        return UploadedData(header, data)

    def _write(self, command):
        # Write and check written byte count.
        written = self._serial_port.write(command)
        if written != len(command):
            raise FlyDreamAltimeterWriteError('Error while writing %s'
                    '(sent: %d, reported: %d)'
                    % (command, len(command), written))

    def _read(self, size):
        # Write and check read byte count.
        # read() should be blocking when data is not available...
        data = self._serial_port.read(size)
        if len(data) != size:
            raise FlyDreamAltimeterReadError('Error while reading')
        return data
