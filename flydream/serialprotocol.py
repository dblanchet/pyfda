
# Supported sampling frequencies.
FREQ_1_HERTZ = '\x00'
FREQ_2_HERTZ = '\x01'
FREQ_4_HERTZ = '\x02'
FREQ_8_HERTZ = '\x03'

# Device capacity information.
EMPTY_ALTIMETER = 0x020000
FULL_ALTIMETER = 0x100000

# Serial commands.
COMMAND_CLEAR = '\x0F\xDA\x10\x00\xCC\03\x00'
COMMAND_UPLOAD = '\x0F\xDA\x10\x00\xCA\03\x00'
COMMAND_SETUP_PREFIX = '\x0F\xDA\x10\x00\xCA\03'

# Serial commands expected responses.
RESPONSE_CLEAR = '\x07\x0F\xDA\x10\x00\xCC\03\x00'
RESPONSE_UPLOAD = '\x07\x0F\xDA\x10\x00\xCA\03\x00'
RESPONSE_SETUP_PREFIX = '\x07\x0F\xDA\x10\x00\xCA\03'

# Uploaded data header size.
RAW_DATA_HEADER_LENGTH = 12

# Flights are separated by sequences of 32 bytes.
#
# Doc says last byte should be \x03,
# device says otherwise.
RAW_FLIGHTS_SEPARATOR = '\xFF' * 30 + '\x00'
