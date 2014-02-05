import platform

import serialprotocol as sp
from serialdevice import SerialDevice


class Altimeter:
    ''' Provide FlyDream Altimeter basic operations.

    It implements the altimeter low level serial protocol.'''

    MAC_SERIAL_PORT = '/dev/tty.SLAB_USBtoUART'
    LINUX_SERIAL_PORT = '/dev/ttyUSB0'
    WINDOWS_SERIAL_PORT = 'COM3'

    # Supported setup values.
    _freq_to_rate = {
            1: sp.FREQ_1_HERTZ,
            2: sp.FREQ_2_HERTZ,
            4: sp.FREQ_4_HERTZ,
            8: sp.FREQ_8_HERTZ
    }
    _freq_list = sorted(_freq_to_rate.keys())

    def _default_serial_port(self):
        ''' Default port depends on the platform.'''
        return {
            'Windows': self.WINDOWS_SERIAL_PORT,
            'Darwin': self.MAC_SERIAL_PORT,
            'Linux': self.LINUX_SERIAL_PORT
        }.get(platform.system(), None)

    def __init__(self, port=None):
        self._port = port if port else self._default_serial_port()
        self._device = SerialDevice(self._port)

    @property
    def port(self):
        '''Serial port name to the physical altimeter device.'''
        return self._port

    def clear(self):
        '''Reset the device flight data.

        Return True if data is correctly reset.

        This command may take a while to execute (10 seconds or so).'''
        with self._device.opened() as device:
            result = device.clear()

        return result

    def setup(self, hertz):
        '''Change sampling frequency setting.

        Return True if sampling frequency is correctly set.

        Argument:
        hertz -- Wanted sampling frequency

        Example:
            device.setup(2.0)'''

        # Float are OK if roundable to int.
        if isinstance(hertz, float):
            int_hertz = int(hertz)
            if int_hertz != hertz:
                raise ValueError('Supported values are', self._freq_list)
            hertz = int_hertz

        # Ensure given argument is supported.
        try:
            rate = self._freq_to_rate[hertz]
        except KeyError:
            raise ValueError('Supported values are', self._freq_list)

        # Send sampling rate to device.
        with self._device.opened() as device:
            result = device.setup(rate)

        return result

    def upload(self, callback=None):
        '''Retrieve raw flight data.

        The altimeter flight data is split between header and content.
        This method parse the header to know how much data it must read
        from the device.

        The result is UploadedData object.

        Keyword arguments:
        callback -- A callable that take (int, int) argument (default: None).

        The first argument of the callback is the read byte count.
        The second argument is the total data size.

        callback example:
            def on_progress(read_size, total_size):
                ...

        NOTE: Take care not to perform blocking actions
              in your callback implementation.'''

        # Ensure argument is valid.
        if callback and not callable(callback):
            raise ValueError('callback argument must be callable')

        # Extract raw data from device.
        #
        # Result is a UploadedData object.
        with self._device.opened() as device:
            result = device.upload(callback)

        return result
