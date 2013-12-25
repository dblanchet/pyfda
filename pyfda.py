#!/usr/bin/python
# -+- encoding: utf-8 -+-

from __future__ import print_function

import sys
import argparse
import time
import json

from flydream.uploadeddata import UploadedData
from flydream.dataparser import DataParser
from flydream.altimeter import Altimeter
from flydream.exception import FlyDreamAltimeterSerialPortError

RAW_FILE_EXTENSION = '.fda'
CSV_FILE_EXTENSION = '.csv'
JSON_FILE_EXTENSION = '.json'


def parse_command_line():
    # Setup parser.
    parser = argparse.ArgumentParser(
            description='Interact with FlyDream Altimeter (FDA) device.')

    # Command: What to do.
    group = parser.add_argument_group('Available commands')
    group.add_argument('command',
            choices=['upload', 'setup', 'clear', 'convert', 'info'],
            help='With connected altimeter: "upload", "setup" or "clear"\n'
            'With raw data file: "convert" or "info"')  # \n\n'
            #'upload  - Get all flight data from the Altimeter\n'
            #'setup   - Change altimeter sampling frequency\n'
            #'clear   - Erase all flight data on the Device\n\n'
            #'info    - Print a summary of flight data\n'
            #'convert - Convert raw altimeter data to various formats')

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
    #print(args)

    # Check argument coherency.
    command = args.command

    if command == 'setup' and not args.frequency:
        print('error: Missing --frequency argument with command: %s'
                % command)
        return None

    if command in ['info', 'convert']:
        if not args.fda_file:
            print('error: Missing fda_file argument with command: %s'
                    % command)
            return None

    # Make convert format default to CSV format.
    if command == 'convert':
        if not args.csv and not args.json:
            args.csv = True

    return args


def read_fda_file(fda_file):
    print('Reading file %s...' % fda_file)
    raw_flights = UploadedData.from_file(fda_file)

    flights = DataParser().extract_flights(raw_flights.data)
    print('Found %d flights:' % len(flights))

    return flights


def print_file_info(fda_file):
    flights = read_fda_file(fda_file)
    for idx, flight in enumerate(flights):
        duration = flight.records[-1].time + 1.0 / flight.sampling_freq
        print('   %d: %8d records @ %dHz -%10.3f seconds' %
                (idx, len(flight.records),
                    flight.sampling_freq, duration))


def default_out_filename():
    return time.strftime('%Y-%m-%d %H-%M-%S', time.localtime()) + '_flight'


def convert_to_csv(flights, out_prefix=None):
    for idx, flight in enumerate(flights):
        fname = out_prefix + '_%3.3d' % idx + CSV_FILE_EXTENSION
        print('   Writing %s file' % fname)
        with open(fname, 'w') as f:
            temp_unit = '°C'  # TODO Fahrenheit
            length_unit = 'm'  # TODO Feet
            f.write('time(sec),temperature(%s),altitude(%s)\n'
                    % (temp_unit, length_unit))
            for rec in flight.records:
                f.write('%.3f,%d,%.1f\n' % rec)


def convert_to_json(flights, out_prefix=None):
    for idx, flight in enumerate(flights):
        fname = out_prefix + '_flight_%3.3d' % idx + JSON_FILE_EXTENSION

        # Prepare header.
        temp_unit = 'celsius'  # TODO Fahrenheit
        length_unit = 'meters'  # TODO Feet
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
        flights = read_fda_file(args.fda_file)
        fname_prefix = args.prefix if args.prefix else default_out_filename()

        if args.csv:
            convert_to_csv(flights, fname_prefix)

        if args.json:
            convert_to_json(flights, fname_prefix)

        return 0

    # Remaining command requires a connected altimeter.
    altimeter = Altimeter(args.port)

    # Erase all data.
    try:
        if command == 'clear':
            print('Erasing all data. Do not disconnect the altimeter...')
            altimeter.clear()
            print('All data erased')

        if command == 'setup':
            print('Setting sampling frequency. '
                    'Do not disconnect the altimeter...')
            altimeter.setup(args.frequency)
            print('All data erased')

        if command == 'upload':

            def progression(read, total):
                if read < total:
                    print('Read %d out of %d\r' % (read, total), end='')
                    sys.stdout.flush()
                else:
                    print('Read %d bytes from altimeter' % total)

            print('Reading all data. Do not disconnect the altimeter...')
            raw_data = altimeter.upload(progression)
            print('All data read')

            fname_prefix = args.prefix if args.prefix \
                    else default_out_filename()
            fname = fname_prefix + RAW_FILE_EXTENSION
            raw_data.to_file(fname)

    except FlyDreamAltimeterSerialPortError as e:
        print('''\nerror: %s

Please ensure that:
 - your altimeter is plugged to the USB adapter.
 - the USB adapter is plugged to your computer.
 - the given port is correct.
 - the USB adapter driver is properly installed on your computer, see
   http://www.silabs.com/products/mcu/pages/usbtouartbridgevcpdrivers.aspx'''
   % e.message)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

# vim:nosi:
