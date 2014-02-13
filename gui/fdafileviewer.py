# -+- encoding: utf-8 -+-

import Tkinter as tk
from tkFileDialog import askopenfilename

from fdaflightlist import FdaFlightList
from fdaflightview import FdaFlightView
from fdaflightviewdatasource import FdaFlightViewDataSource

from fdaaltimetercontrol import FdaAltimeterControl

import gettext
_ = gettext.translation('messages', 'gui', fallback=True).ugettext


class FdaFileViewer(tk.Tk):

    def __init__(self, filename):
        tk.Tk.__init__(self, None)

        self.initialize()

        self.load_file(filename)

    def initialize(self):
        self.title(_(u'FlyDream Altimeter - Data Flight Viewer'))

        # Set minimal size
        self.minsize(480, 240)
        self.resizable(True, False)

        # Prevent first column and last row to resize.
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Flight list.
        self.flight_list = FdaFlightList(self, self.on_flight_selected, \
                width=25)
        self.flight_list.grid(column=0, sticky='NS')

        # Choose file button.
        self.load_button = tk.Button(self, text=_(u'Load file...'),
                command=self.ask_for_file)
        self.load_button.grid(column=0, row=1, sticky='EW')

        # Flight representation.
        self.flight_info = FdaFlightView(self)
        self.flight_info.grid(column=1, row=0, sticky='NSEW')

        # Flight display settings and other controls.
        frame = tk.Frame(self)
        frame.grid(column=1, row=1, columnspan=2, sticky='EW')

        # X zoom level.
        self.scale = tk.Scale(self, orient=tk.HORIZONTAL,
                from_=1.0, to=100.0, resolution=0.1)
        self.scale.pack(in_=frame, side='left')
        self.scale.bind('<ButtonPress>', self.scale_pressed)
        self.scale.bind('<ButtonRelease>', self.scale_released)

        # Device interaction button.
        device = tk.Button(self, text=_(u'Altimeter'),
                command=self.open_device_window)
        device.pack(in_=frame, side='right')

    def scale_pressed(self, event):
        event.widget.bind('<Motion>', self.scale_changed)

    def scale_released(self, event):
        event.widget.unbind('<Motion>')

    def scale_changed(self, event):
        self.flight_info.set_x_scale(event.widget.get())

    def open_device_window(self):
        FdaAltimeterControl()

    def ask_for_file(self):
        filename = askopenfilename(filetypes=(
            (_(u'Flydream Altimeter Data'), '*.fda'),
            (_(u'All files'), '*.*')))
        self.load_file(filename)

    def load_file(self, filename):
        if filename:
            self.flight_list.load_fda_file(filename)

    def on_flight_selected(self, flight):
        # Tell canvas view to display this flight.
        data_source = FdaFlightViewDataSource(flight)
        self.flight_info.display_flight_data(data_source)

        # Reset our scale factor widget, because
        # loading a new file resets canvas scale.
        self.scale.set(1.0)
