#!/usr/bin/python

import unittest

import tempfile

from flydream.uploadeddata import UploadedData
import flydream.serialprotocol as sp


class FlyDreamUploadedData(unittest.TestCase):

    def test_read(self):
        result = UploadedData.from_file('test/test_flydreamdevice_sample.fda')

        header = result.header
        self.assertEqual(len(header), sp.RAW_DATA_HEADER_LENGTH,
                'Invalid header length')
        expected_value = sp.RESPONSE_UPLOAD + '\x00\x02\x07\x00'
        self.assertEqual(header, expected_value, 'Incorrect header')

        data = result.data
        self.assertEqual(len(data), 0x700, 'Invalid header length')

    def test_write(self):
        origin = UploadedData.from_file('test/test_flydreamdevice_sample.fda')

        _, name = tempfile.mkstemp(prefix='flydream_tests')
        fname = name + '0'  # mkstemp creates the file. We do not want this.
        origin.to_file(fname)

        result = UploadedData.from_file(fname)
        self.assertEqual(result.header, origin.header, 'Incorrect header')
        self.assertEqual(result.data, origin.data, 'Incorrect data')

    def test_write_existing(self):
        origin = UploadedData.from_file('test/test_flydreamdevice_sample.fda')

        _, name = tempfile.mkstemp(prefix='flydream_tests')
        fname = name + '0'  # mkstemp creates the file. We do not want this.
        origin.to_file(fname)

        with self.assertRaises(IOError):
            origin.to_file(fname)
