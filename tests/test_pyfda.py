#!/bin/python

import os

from unittest import TestCase
from scripttest import TestFileEnvironment


class TestPyfdaCommandLineTool(TestCase):

    def setUp(self):
        self.env = TestFileEnvironment(
                base_path=os.path.abspath('tests/test-output'),
                cwd=os.getcwd(),
                #environ={
                    #'PATH': '/usr/local/bin:/usr/bin:/bin',
                    #'HOME': os.path.abspath('tests/test-output'),
                    #},
                #template_path=os.path.abspath('tests/data'),
                ignore_hidden=False)

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
        self.assertEquals(result.stderr, expected, 'Incorrect error message')

    def test_info_missing_fda_file(self):
        'Test: pyfda info'

        cmd = './pyfda.py info'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: Missing fda_file argument with command: info\n'
        self.assertEquals(result.stderr, expected, 'Incorrect error message')

    def test_convert_missing_fda_file(self):
        'Test: pyfda convert'

        cmd = './pyfda.py convert'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: Missing fda_file argument with command: convert\n'
        self.assertEquals(result.stderr, expected, 'Incorrect error message')

    def test_convert_too_much_temperature_arguments(self):
        'Test: pyfda convert file.fda --celsius --fahrenheit'

        cmd = './pyfda.py convert file.fda --celsius --fahrenheit'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: --celsius and --fahrenheit can not ' \
                'be both specified.\n'
        self.assertEquals(result.stderr, expected, 'Incorrect error message')

    def test_convert_too_much_length_arguments(self):
        'Test: pyfda convert file.fda --feet --meters'

        cmd = './pyfda.py convert file.fda --feet --meters'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: --meters and --feet can not be both specified.\n'
        self.assertEquals(result.stderr, expected, 'Incorrect error message')

    def test_convert_incorrect_last_negative_value(self):
        'Test: pyfda convert file.fda --last -1'

        cmd = './pyfda.py convert file.fda --last -1'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 1,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: --last argument must be positive.\n'
        self.assertEquals(result.stderr, expected, 'Incorrect error message')

    def test_convert_incorrect_last_non_integer_value(self):
        'Test: pyfda convert file.fda --last toto'

        cmd = './pyfda.py convert file.fda --last toto'
        result = self.env.run(cmd, expect_error=True)

        self.assertEqual(result.returncode, 2,\
                'Expect returncode=1, got %r' % result.returncode)
        expected = 'error: argument --last: invalid int value:'
        self.assertTrue(expected in result.stderr, 'Incorrect error message')

# vim:nosi:
