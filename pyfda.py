#!/usr/bin/python
# -+- encoding: utf-8 -+-

from __future__ import print_function

import sys
import argparse
import textwrap
import time
import json

from flydream.uploadeddata import UploadedData
from flydream.dataparser import DataParser
from flydream.altimeter import Altimeter
from flydream.exception import FlyDreamAltimeterSerialPortError

RAW_FILE_EXTENSION = '.fda'
CSV_FILE_EXTENSION = '.csv'
JSON_FILE_EXTENSION = '.json'

CELSIUS_UNIT = '°C'
FAHRENHEIT_UNIT = '°F'

METER_UNIT = 'm'
FOOT_UNIT = 'ft'


def parse_command_line():
    # Setup parser.
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent('''\
                    Interact with FlyDream Altimeter (FDA) device and data.

                        Available device commands:
                            upload  - Get all flight data from the Altimeter
                            setup   - Change altimeter sampling frequency
                            clear   - Erase all flight data on the Device

                        Available data (FDA file) commands:
                            info    - Print a summary of flight data file
                            convert - Convert data to various formats
                    '''),
            epilog='Unrelevant arguments for given command are silently '
            'ignored.')

    # Command: What to do.
    group = parser.add_argument_group('Available commands')
    group.add_argument('command',
            choices=['upload', 'setup', 'clear', 'convert', 'info'],
            help='"upload", "setup" and "clear" commands require a '
            'connected altimeter. "convert" and "info" commands require '
            'a raw .fda file argument.')

    # Device related arguments.
    group = parser.add_argument_group('Altimeter configuration')
    group.add_argument('--port',
           help='Altimeter serial port name. Default is platform dependent. '
           'With "upload", "setup" or "clear" commands')
    group.add_argument('--frequency', type=int, choices=[1, 2, 4, 8],
            help='Sampling frequency (with "setup" command only)')

    # Generated file related arguments.
    group = parser.add_argument_group('Expected output format '
            '(default: raw FDA format with "upload", CSV with "convert")')
    group.add_argument('--csv',
            action='store_true',
            help='Output CSV data (with "upload" or "convert" command)')
    group.add_argument('--json',
            action='store_true',
            help='Output JSON data (with "upload" or "convert" command)')
    group.add_argument('--prefix',
            help='Prefix of generated files (with "upload" or "convert" '
            ' commands). Use current date/time as default.')
    group.add_argument('--last', type=int, default=0, nargs='?',
            help='Convert LAST lastest flights only (with "convert"). '
            'Default: 1.')

    # Generated file units.
    group = parser.add_argument_group('Conversion units '
            '(with "upload" or "convert" command)')
    group.add_argument('--celsius',
            action='store_true',
            help='Convert temperature to celsius degrees (default)')
    group.add_argument('--fahrenheit',
            action='store_true',
            help='Convert temperature to fahrenheit degrees')
    group.add_argument('--meters',
            action='store_true',
            help='Convert altitude to meters (default)')
    group.add_argument('--feet',
            action='store_true',
            help='Convert altitude to feet')

    # Input arguments.
    group = parser.add_argument_group('Expected input filename')
    group.add_argument('fda_file', nargs='?', default=None,
            help='Altimeter raw data FDA file '
            '(with "convert" and "info" commands)')

    # Extract arguments.
    args = parser.parse_args()
    #print(args)  # DEBUG

    # Check argument coherency.
    command = args.command

    if command == 'setup' and not args.frequency:
        print('error: Missing --frequency argument with command: %s'
                % command, file=sys.stderr)
        return None

    if command in ['info', 'convert']:
        if not args.fda_file:
            print('error: Missing fda_file argument with command: %s'
                    % command, file=sys.stderr)
            return None

    # Make convert format default to CSV format.
    if command == 'convert':
        if not args.csv and not args.json:
            args.csv = True

    # Set temperature units, defaults to celsius.
    if args.celsius and args.fahrenheit:
        print('error: --celsius and --fahrenheit can not '
                'be both specified.', file=sys.stderr)
        return None

    args.temp_unit = DataParser.TEMPERATURE_UNIT_CELSIUS
    if args.fahrenheit:
        args.temp_unit = DataParser.TEMPERATURE_UNIT_FAHRENHEIT

    # Set length unit, defaults to meters.
    if args.meters and args.feet:
        print('error: --meters and --feet can not be both specified.',
                file=sys.stderr)
        return None

    args.length_unit = DataParser.LENGTH_UNIT_METER
    if args.feet:
        args.length_unit = DataParser.LENGTH_UNIT_FEET

    # Conversion flight count.
    if args.last is None:
        # Specified without count: default to 1.
        args.last = 1

    if args.last < 0:
        print('error: --last argument must be positive.', file=sys.stderr)
        return None

    return args


def extract_flights(fda_file,
        length_unit=DataParser.LENGTH_UNIT_METER,
        temp_unit=DataParser.TEMPERATURE_UNIT_CELSIUS):

    print('Reading file %s...' % fda_file)
    raw_flights = UploadedData.from_file(fda_file)

    parser = DataParser(length_unit, temp_unit)
    flights = parser.extract_flights(raw_flights.data)
    print('Found %d flights:' % len(flights))

    return flights


def print_file_info(fda_file):
    flights = extract_flights(fda_file)
    for flight in flights:
        print('   %d: %8d records @ %dHz -%10.3f seconds' %
                (flight.index, len(flight.records),
                    flight.sampling_freq, flight.duration))


def default_out_filename():
    return time.strftime('%Y-%m-%d %H-%M-%S', time.localtime()) + '_flight'


def length_unit_to_string(length_unit):
    return {
            DataParser.LENGTH_UNIT_METER: METER_UNIT,
            DataParser.LENGTH_UNIT_FEET: FOOT_UNIT
    }[length_unit]


def temperature_unit_to_string(temp_unit):
    return {
            DataParser.TEMPERATURE_UNIT_CELSIUS: CELSIUS_UNIT,
            DataParser.TEMPERATURE_UNIT_FAHRENHEIT: FAHRENHEIT_UNIT
    }[temp_unit]


def convert_to_csv(flights, out_prefix, count=0):

    for flight in flights[-count:]:

        fname = out_prefix + '_%3.3d' % flight.index + CSV_FILE_EXTENSION
        print('   Writing %s file' % fname)

        length_unit = length_unit_to_string(flight.length_unit)
        temp_unit = temperature_unit_to_string(flight.temperature_unit)

        with open(fname, 'w') as f:
            f.write('time(sec),temperature(%s),altitude(%s)\n'
                    % (temp_unit, length_unit))
            for rec in flight.records:
                f.write('%.3f,%d,%.1f\n' % rec)


def convert_to_json(flights, out_prefix, count=0):

    for flight in flights[-count:]:
        fname = out_prefix + '_%3.3d' % flight.index + JSON_FILE_EXTENSION

        # Prepare header.
        length_unit = length_unit_to_string(flight.length_unit)
        temp_unit = temperature_unit_to_string(flight.temperature_unit)
        root = {
                'info': {
                    'temperature_unit': temp_unit,
                    'length_unit': length_unit,
                    'sampling_frequency': flight.sampling_freq
                    },
                'records': []
                }

        # Add records.
        for rec in flight.records:
            root['records'].append({
                'time': rec.time,
                'temperature': rec.temperature,
                'altitude': rec.altitude,
                })

        # Write to file.
        print('   Writing %s file' % fname)
        with open(fname, 'w') as f:
            f.write(json.dumps(root, indent=2, separators=(',', ': ')))


def convert_flights(flights, fname_prefix, args):

    # Make last argument relevant.
    if args.last == 0:
        flight_count = len(flights)
    else:
        flight_count = args.last

    # Convert to required formats.
    if args.csv:
        print('Converting %d flight(s) to CSV...' % flight_count)
        convert_to_csv(flights, fname_prefix, args.last)

    if args.json:
        print('Converting %d flight(s) to JSON...' % flight_count)
        convert_to_json(flights, fname_prefix, args.last)


def print_disconnection_warning(message):
    print('''%s...
WARNING: Do not disconnect the altimeter until the blue LED lights again.'''
    % message)


def main(argv):

    # Check command line argument.
    args = parse_command_line()
    if not args:
        return 1

    command = args.command

    # Give information about given file.
    if command == 'info':
        print_file_info(args.fda_file)
        return 0

    # Convert raw uploaded data.
    if command == 'convert':
        fname_prefix = args.prefix if args.prefix else default_out_filename()
        flights = extract_flights(args.fda_file,
                args.length_unit, args.temp_unit)
        convert_flights(flights, fname_prefix, args)
        return 0

    # Remaining command requires a connected altimeter.
    altimeter = Altimeter(args.port)

    try:
        # Erase all data.
        if command == 'clear':
            print_disconnection_warning('Erasing all data')
            altimeter.clear()

        # Change sampling frequency.
        if command == 'setup':
            print('Setting sampling frequency...')
            altimeter.setup(args.frequency)

        # Get all altimeter data.
        if command == 'upload':

            # Show data retrieval progression.
            def progression(read, total):
                if read < total:
                    print('   %d bytes read out of %d\r' % (read, total),
                            end='')
                    sys.stdout.flush()
                else:
                    print('Read %d bytes from altimeter' % total)

            # Get data from device.
            print_disconnection_warning('Reading data')
            raw_data = altimeter.upload(progression)
            if len(raw_data.data) == 0:
                print('   Altimeter does not contain any data')

            # Write raw data.
            fname_prefix = args.prefix if args.prefix \
                    else default_out_filename()
            fname = fname_prefix + RAW_FILE_EXTENSION
            print('Writing uploaded data to', fname)
            raw_data.to_file(fname)

            # Honor conversion requests.
            parser = DataParser(args.length_unit, args.temp_unit)
            flights = parser.extract_flights(raw_data.data)
            convert_flights(flights, fname_prefix, args)

    except FlyDreamAltimeterSerialPortError as e:
        print('''\nerror: %s

Please ensure that:
 - your altimeter is plugged to the USB adapter.
 - the USB adapter is plugged to your computer.
 - the given port is correct.
 - the USB adapter driver is properly installed on your computer, see
   http://www.silabs.com/products/mcu/pages/usbtouartbridgevcpdrivers.aspx'''
   % e.message, file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

# vim:nosi:
