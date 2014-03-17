
import os

from flydream import serialprotocol as sp


class UploadedData:

    def __init__(self, header, data):
        self.header = header
        self.data = data

    def full_data(self):
        return self.header + self.data

    @staticmethod
    def from_file(filename):
        with open(filename, 'rb') as f:
            header = f.read(sp.RAW_DATA_HEADER_LENGTH)
            data = f.read()
            return UploadedData(header, data)

    def to_file(self, filename):
        if os.path.exists(filename):
            raise IOError('File already exists')

        with open(filename, 'wb') as f:
            f.write(self.full_data())
