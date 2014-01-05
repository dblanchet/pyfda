#!/usr/bin/python

import Tkinter as tk
from tkFileDialog import askopenfilename

from flydream.uploadeddata import UploadedData
from flydream.dataparser import DataParser

import gettext
_ = gettext.translation('pyfdagui', fallback=True).ugettext


def flight_description(flight):
    duration = flight.records[-1].time + 1.0 / flight.sampling_freq
    return '%3.3d - %10.3f secs @ %dHz' % \
                (flight.index, duration, flight.sampling_freq)


class FdaFlightList(tk.Listbox):

    def __init__(self, parent, on_flight_selected, *args, **kwargs):
        tk.Listbox.__init__(self, parent, *args, **kwargs)
        self.on_flight_selected = on_flight_selected
        self.bind('<<ListboxSelect>>', self.on_select)

    def load_fda_file(self, path):
        # Load data.
        raw_upload = UploadedData.from_file(path)
        self._flights = DataParser().extract_flights(raw_upload.data)

        # Populate list.
        self.update_content()

        # Select last flight.
        if self._flights:
            self.selection_clear(0)
            self.selection_set(tk.END)
            self.see(tk.END)
            self.on_select(None)

    def update_content(self):
        # Clear list.
        self.delete(0, tk.END)

        # Add loaded flights.
        for flight in self._flights:
            self.insert(tk.END, flight_description(flight))

    def on_select(self, event):
        # Find out index in list.
        selection = self.curselection()
        if not selection:
            return
        index_str, = selection

        if not self._flights:
            return
        flight = self._flights[int(index_str)]

        # Tell the world about current selected flight.
        self.on_flight_selected(flight)


class FdaFlightView(tk.Canvas):

    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, bg='lightgrey', *args, **kwargs)
        self._flight = None
        self.bind('<Configure>', self.on_resize)

    def display_flight(self, flight):
        self._flight = flight
        self.update_content()

    def on_resize(self, event):
        self.update_content()

    def update_content(self):
        self.delete(tk.ALL)

        if not self._flight:
            return

        # Title.
        title = flight_description(self._flight)
        self.create_text(5, 5, anchor='nw', text=title)

        # Altitude plot.
        width = self.winfo_width()
        height = self.winfo_height()
        records = self._flight.records

        x_stride = 1.0 * width / len(self._flight.records)

        alt_max = max(rec.altitude for rec in records)
        alt_min = min(rec.altitude for rec in records)

        def y_coord(altitude):
            rel_alt = 1.0 * (altitude - alt_min) / (alt_max - alt_min)
            return (1.0 - rel_alt) * height

        x_prev = 0
        y_prev = y_coord(records[0].altitude)

        for rec in records[1:]:
            x_next = x_prev + x_stride
            y_next = y_coord(rec.altitude)

            self.create_line(x_prev, y_prev, x_next, y_next, fill='red')

            x_prev = x_next
            y_prev = y_next


class FdaFileViewer(tk.Tk):

    def __init__(self, filename):
        tk.Tk.__init__(self, None)

        self.initialize()

        self.load_file(filename)

    def initialize(self):
        self.title(_('FlyDream Altimeter - Data Flight Viewer'))

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
        self.load_button = tk.Button(self, text=_('Load file...'),
                command=self.ask_for_file)
        self.load_button.grid(column=0, row=1, sticky='EW')

        # Flight representation.
        self.flight_info = FdaFlightView(self)
        self.flight_info.grid(column=1, row=0, sticky='NSEW')

        # TODO: Flight display information (units...)
        label = tk.Label(self, anchor="w", text='TODO: Change display units')
        label.grid(column=1, row=1, columnspan=2, sticky='EW')

    def ask_for_file(self):
        filename = askopenfilename(filetypes=(
            (_('Flydream Altimeter Data'), '*.fda'),
            (_('All files'), '*.*')))
        self.load_file(filename)

    def load_file(self, filename):
        if filename:
            self.flight_list.load_fda_file(filename)

    def on_flight_selected(self, flight):
        self.flight_info.display_flight(flight)

# vim:nosi:
