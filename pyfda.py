#!/usr/bin/python

from __future__ import print_function

import sys
import argparse
import time
import json

import flydreamaltimeter
import flydreamdevice

RAW_FILE_EXTENSION = '.fda'
CSV_FILE_EXTENSION = '.csv'
JSON_FILE_EXTENSION = '.json'


def main(argv):

    # Parse command line arguments.
    parser = argparse.ArgumentParser(
            description='Interact with FlyDream Altimeter (FDA).')
    parser.add_argument('command',
            help='With connected altimeter: "upload", "setup" or "clear"\n'
            'With raw data file: "convert" or "info"')

    group = parser.add_argument_group('Altimeter configuration')
    group.add_argument('--port',
           help='Altimeter serial port name. Default is platform dependent. '
           'With "upload", "setup" or "clear" command only.')
    group.add_argument('--frequency', type=int, choices=[1, 2, 4, 8],
            help='Sampling frequency (with "setup" command only)')

    group = parser.add_argument_group('Expected output format (default: raw)')
    group.add_argument('--raw',
            action='store_true',
            help='Output raw binary data (with "upload" command only)')
    group.add_argument('--csv',
            action='store_true',
            help='Output CSV data (with "upload" or "convert" command)')
    group.add_argument('--json',
            action='store_true',
            help='Output JSON data (with "upload" or "convert" command)')
    group.add_argument('--output',
            help='Destination of flight data (with "upload" or "convert" '
            ' commands). Use current date/time as default.')

    group = parser.add_argument_group('Expected input filename')
    group.add_argument('--input',
            help='Altimeter raw data file (with "convert" command only).')

    # Check command line arguments.
    args = parser.parse_args()
    #print(args)
    if args.command not in ['upload', 'setup', 'clear', 'info', 'convert']:
        print('Invalid command: %s\n' % args.command)
        parser.print_help()
        return 1

    command = args.command
    frequency = args.frequency
    output = args.output
    raw = args.raw
    json_file = args.json
    csv = args.csv

    if command == 'setup' and not frequency:
        print('Missing --frequency argument with command: %s\n' % command)
        parser.print_help()
        return 1

    if command == 'info':
        # TODO
        print('Not implemnted yet')
        return 0

    if command == 'convert':
        # TODO
        print('Not implemnted yet')
        return 0

    # Perform requested task.
    try:
        altimeter = flydreamaltimeter.FlyDreamAltimeter()
    except flydreamaltimeter.FlyDreamDeviceSerialPortError as e:
        print('''Error: %s

Please ensure that:
 - your altimeter is plugged to the USB adapter.
 - the USB adapter is plugged to your computer.
 - the given port is correct.
 - the USB adapter driver is properly installed on your computer, see
   http://www.silabs.com/products/mcu/pages/usbtouartbridgevcpdrivers.aspx'''
   % e.message)
        return 2

    print('Opening altimeter on %s' % altimeter.port)
    try:
        # Erase all flight data.
        if command == 'clear':
            print('Erasing flight data. Do not disconnect the altimeter')
            if altimeter.reset_flight_data():
                print('Success')
            else:
                print('Failure')

        # Retrieve flight data.
        if command == 'upload':
            print('Reading flight data. Do not disconnect the altimeter')

            fname = output if output else time.strftime(
                    '%Y-%m-%d %H-%M-%S', time.localtime())

            def progression(read, total):
                if read < total:
                    print('Read %d out of %d\r' % (read, total), end='')
                    sys.stdout.flush()
                else:
                    print('Read %d bytes from altimeter' % total)

            data = altimeter.read_flight_data(progression)
            if raw:
                with open(fname + RAW_FILE_EXTENSION, 'wb') as f:
                    f.write(data[0])
                    f.write(data[1])
                print('Raw data written to %s' % fname)

            if csv or json_file:
                flights = altimeter.convert_flight_data(data)

                count = 0
                for flight in flights:
                    if csv:
                        out_fname = fname + '_%d' % count + CSV_FILE_EXTENSION
                        with open(out_fname, 'w') as f:
                            for sample in flight:
                                f.write('%f,%d,%f' % sample)

                    if json_file:
                        out_fname = fname + '_%d' % count + JSON_FILE_EXTENSION
                        with open(out_fname, 'w') as f:
                            f.write(json.dumps(flight))

        # Change sampling frequency.
        if command == 'setup':
            print('Reading flight data. Do not disconnect the altimeter')
            if altimeter.set_sampling_frequency(frequency):
                print('Success')
            else:
                print('Failure')

    except flydreamdevice.FlyDreamDeviceException as e:
        print('Error while communicating with the altimeter: %s' %
                e.message)
        return 2
    finally:
        print('Closing altimeter on %s' % altimeter.port)
        altimeter.close()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

# vim:nosi:
