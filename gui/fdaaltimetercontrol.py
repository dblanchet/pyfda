# -+- encoding: utf-8 -+-

import Tkinter as tk

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
