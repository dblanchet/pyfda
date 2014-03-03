#!/usr/bin/python

import sys

from gui.fdafileviewer import FdaFileViewer


def main(argv):
    filename = argv[1] if argv[1:] else None
    app = FdaFileViewer(filename)

    # Deal with Mac OS X data file double-click
    # handling: clicked files are not given on
    # command line, but through a system signal.
    if sys.platform.startswith('darwin'):

        def doOpenFile(*args):
            # Open first file only.
            for fname in args:
                app.load_file(fname)
                break

        # The command below is a hook in aquatk that is called whenever
        # the app receives a file open event. The callback can have
        # multiple arguments, one for every file that should be opened.
        #
        # http://stackoverflow.com/a/1004487
        app.createcommand("::tk::mac::OpenDocument", doOpenFile)

    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

# vim:nosi:
