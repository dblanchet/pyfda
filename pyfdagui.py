#!/usr/bin/python

import sys

from gui.fdafileviewer import FdaFileViewer


def main(argv):
    filename = argv[1] if argv[1:] else None
    app = FdaFileViewer(filename)
    app.mainloop()


if __name__ == "__main__":
    sys.exit(main(sys.argv))

# vim:nosi:
