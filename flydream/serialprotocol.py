
# Supported sampling frequencies.
FREQ_1_HERTZ = b'\x00'
FREQ_2_HERTZ = b'\x01'
FREQ_4_HERTZ = b'\x02'
FREQ_8_HERTZ = b'\x03'

# Device capacity information.
EMPTY_ALTIMETER = 0x020000
FULL_ALTIMETER  = 0x100000

# Serial commands.
COMMAND_UPLOAD       = b'\x0F\xDA\x10\x00\xCA\03\x00'
COMMAND_SETUP_PREFIX = b'\x0F\xDA\x10\x00\xCB\03'
COMMAND_CLEAR        = b'\x0F\xDA\x10\x00\xCC\03\x00'

# Serial commands expected responses.
RESPONSE_UPLOAD       = b'\x07\x0F\xDA\x10\x00\xCA\03\x00'
RESPONSE_SETUP_PREFIX = b'\x07\x0F\xDA\x10\x00\xCB\03'
RESPONSE_CLEAR        = b'\x07\x0F\xDA\x10\x00\xCC\03\x00'

# Uploaded data header size.
RAW_DATA_HEADER_LENGTH = 12

# Flights are separated by sequences of 32 bytes.
#
# First 30 bytes are 0xFF bytes.
#
# Next one should always be 0x03,
# but it was found to be also 0x00.
# So it will be ignored by the parser.
#
# Last byte tells the sampling rate.
RAW_FLIGHTS_SEPARATOR = b'\xFF' * 30  # + b'\x03'
