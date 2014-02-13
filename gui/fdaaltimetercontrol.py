# -+- encoding: utf-8 -+-

import Tkinter as tk

import tkMessageBox

import gettext
_ = gettext.translation('messages', 'gui', fallback=True).ugettext


class FdaAltimeterControl(tk.Toplevel):

    def __init__(self):
        tk.Toplevel.__init__(self)

        self.initialize()

    def initialize(self):
        self.title(_(u'FlyDream Altimeter - Device Controller'))

        # Set minimal size
        self.minsize(640, 480)
        self.resizable(False, False)

        # Available actions on the left.
        upload = tk.Button(self, text=_(u'Upload data'),
                command=self.upload)
        upload.grid(column=0, row=0, sticky='EW')

        erase = tk.Button(self, text=_(u'Erase data'),
                command=self.erase)
        erase.grid(column=0, row=1, sticky='EW')

        setup = tk.Button(self, text=_(u'Set sampling frequency'),
                command=self.set_frequency)
        setup.grid(column=0, row=2)

    def upload(self):
        tkMessageBox.showwarning('Upload flight data', 'Not implemented yet')

    def erase(self):
        reply = tkMessageBox.askokcancel(_(u'Erase flight data'),
                _(u'Really erase all flight data in your altimeter?'))
        if reply:
            self.do_erase()

    def do_erase(self):
        tkMessageBox.showwarning('Erase flight data', 'Not implemented yet')

    def set_frequency(self):
        tkMessageBox.showwarning('Upload flight data', 'Not implemented yet')
