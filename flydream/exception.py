

class FlyDreamAltimeterException(Exception):
    pass


class FlyDreamAltimeterSerialPortError(FlyDreamAltimeterException):
    pass


class FlyDreamAltimeterWriteError(FlyDreamAltimeterException):
    pass


class FlyDreamAltimeterReadError(FlyDreamAltimeterException):
    pass


class FlyDreamAltimeterProtocolError(FlyDreamAltimeterException):
    pass
