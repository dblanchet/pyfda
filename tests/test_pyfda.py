#!/bin/python

import os

from unittest import TestCase
from scripttest import TestFileEnvironment

TEST_SUBDIR = 'tests/test-output'
TEST_DIR = os.path.abspath(TEST_SUBDIR)
TEMPLATE_DIR = os.path.abspath('tests')

INPUT_FILE_NAME = 'sample.fda'
INPUT_FILE_PATH = os.path.join(TEST_SUBDIR, INPUT_FILE_NAME)
CONVERTED_PREFIX = os.path.join(TEST_SUBDIR, 'test_convert')


class TestPyfdaCommandLineTool(TestCase):

    def setUp(self):
        self.env = TestFileEnvironment(
                base_path=TEST_DIR,
                template_path=TEMPLATE_DIR,
                cwd=os.getcwd(),
                ignore_hidden=False)
        self.env.writefile(INPUT_FILE_NAME,
                frompath='test_freq_2_then_1_then_8_then_4.fda')

    def test_no_arguments(self):
        'Test: pyfda.py'

        cmd = './pyfda.py'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 2,\
                'Expect returncode=2, got %r' % result.returncode)
        self.assertEqual(result.stderr[:7], 'usage: ', \
                'Incorrect usage message')

        message = 'error: too few arguments\n'
        self.assertEqual(result.stderr[-len(message):], message, \
                'Incorrect error message')

    def test_setup_missing_frequency_argument(self):
        'Test: pyfda setup'

        cmd = './pyfda.py setup'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: Missing --frequency argument with command: setup\n'
        self.assertEqual(result.stderr, expected, 'Incorrect error message')

    def test_info_missing_fda_file(self):
        'Test: pyfda info'

        cmd = './pyfda.py info'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: Missing fda_file argument with command: info\n'
        self.assertEqual(result.stderr, expected, 'Incorrect error message')

    def test_convert_missing_fda_file(self):
        'Test: pyfda convert'

        cmd = './pyfda.py convert'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: Missing fda_file argument with command: convert\n'
        self.assertEqual(result.stderr, expected, 'Incorrect error message')

    def test_convert_too_much_temperature_arguments(self):
        'Test: pyfda convert file.fda --celsius --fahrenheit'

        cmd = './pyfda.py convert file.fda --celsius --fahrenheit'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: --celsius and --fahrenheit can not ' \
                'be both specified.\n'
        self.assertEqual(result.stderr, expected, 'Incorrect error message')

    def test_convert_too_much_length_arguments(self):
        'Test: pyfda convert file.fda --feet --meters'

        cmd = './pyfda.py convert file.fda --feet --meters'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: --meters and --feet can not be both specified.\n'
        self.assertEqual(result.stderr, expected, 'Incorrect error message')

    def test_convert_incorrect_last_negative_value(self):
        'Test: pyfda convert file.fda --last -1'

        cmd = './pyfda.py convert file.fda --last -1'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: --last argument must be positive.\n'
        self.assertEqual(result.stderr, expected, 'Incorrect error message')

    def test_convert_incorrect_last_non_integer_value(self):
        'Test: pyfda convert file.fda --last toto'

        cmd = './pyfda.py convert file.fda --last toto'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 2,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: argument --last: invalid int value:'
        self.assertTrue(expected in result.stderr, 'Incorrect error message')

    def test_print_fda_file_info(self):
        'Test: pyfda info sample.fda'

        cmd = './pyfda.py info ' + INPUT_FILE_PATH
        result = self.env.run(cmd, expect_error=False)

        self.assertEqual(result.returncode, 0,\
                'Expect returncode=0, got %r' % result.returncode)
        expected = \
"""Reading file %s...
Found 4 flights:
   0:      216 records @ 2Hz -   108.000 seconds
   1:      136 records @ 1Hz -   136.000 seconds
   2:      496 records @ 8Hz -    62.000 seconds
   3:      176 records @ 4Hz -    44.000 seconds
""" % INPUT_FILE_PATH
        self.assertEqual(expected, result.stdout, 'Incorrect output')

    def test_print_fda_file_convert_all_csv(self):
        'Test: pyfda --prefix=test_convert convert sample.fda'

        cmd = './pyfda.py --prefix=%s convert %s' % (
                CONVERTED_PREFIX, INPUT_FILE_PATH)
        result = self.env.run(cmd, expect_error=False)

        self.assertEqual(result.returncode, 0,\
                'Expect returncode=0, got %r' % result.returncode)
        expected = \
"""Reading file %s...
Found 4 flights:
Converting 4 flight(s) to CSV...
   Writing %s_000.csv file
   Writing %s_001.csv file
   Writing %s_002.csv file
   Writing %s_003.csv file
""" % (INPUT_FILE_PATH, CONVERTED_PREFIX, CONVERTED_PREFIX,
        CONVERTED_PREFIX, CONVERTED_PREFIX)
        self.assertEqual(expected, result.stdout, 'Incorrect output')
        # TODO: Check converted file contents.

    def test_print_fda_file_convert_last_csv(self):
        'Test: pyfda --last --prefix=test_convert convert sample.fda'

        cmd = './pyfda.py --last --prefix=%s convert %s' % (
                CONVERTED_PREFIX, INPUT_FILE_PATH)
        result = self.env.run(cmd, expect_error=False)

        self.assertEqual(result.returncode, 0,\
                'Expect returncode=0, got %r' % result.returncode)
        expected = \
"""Reading file %s...
Found 4 flights:
Converting 1 flight(s) to CSV...
   Writing %s_003.csv file
""" % (INPUT_FILE_PATH, CONVERTED_PREFIX)
        self.assertEqual(expected, result.stdout, 'Incorrect output')
        # TODO: Check converted file content.

    def test_print_fda_file_convert_last_two_csv(self):
        'Test: pyfda --last=2 --prefix=test_convert convert sample.fda'

        cmd = './pyfda.py --last=2 --prefix=%s convert %s' % (
                CONVERTED_PREFIX, INPUT_FILE_PATH)
        result = self.env.run(cmd, expect_error=False)

        self.assertEqual(result.returncode, 0,\
                'Expect returncode=0, got %r' % result.returncode)
        expected = \
"""Reading file %s...
Found 4 flights:
Converting 2 flight(s) to CSV...
   Writing %s_002.csv file
   Writing %s_003.csv file
""" % (INPUT_FILE_PATH, CONVERTED_PREFIX, CONVERTED_PREFIX)
        self.assertEqual(expected, result.stdout, 'Incorrect output')
        # TODO: Check converted file contents.
