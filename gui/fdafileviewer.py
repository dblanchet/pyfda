#!/usr/bin/python
# -+- encoding: utf-8 -+-

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

        self.draw_title()
        self.draw_plots()

    def draw_title(self):
        title = flight_description(self._flight)
        self.create_text(5, 5, anchor='nw', text=title)

    def draw_plots(self):
        # Plot sizes and margins
        width = self.winfo_width()
        if width == 1:
            return
        left_margin = 40
        right_margin = 40
        adjusted_width = width - left_margin - right_margin

        height = self.winfo_height()
        if height == 1:
            return
        top_margin = 30
        bottom_margin = 30
        adjusted_height = height - top_margin - bottom_margin

        # Draw axis.
        axis_margin = 5
        top = top_margin - axis_margin
        bottom = height - bottom_margin + axis_margin
        right = width - right_margin

        self.create_line(left_margin, top,
                left_margin, bottom,
                fill='black')
        self.create_line(left_margin, bottom,
                right, bottom,
                fill='black')
        self.create_line(right, top,
                right, bottom,
                fill='black')

        # Add labels with units.
        text_offset = 5

        self.create_text(left_margin + text_offset, top_margin + text_offset,
                anchor='nw', text=u'altitude (m)', fill='red')
        self.create_text(right - text_offset, top_margin + text_offset,
                anchor='ne', text=u'temperature (°C)', fill='blue')
        self.create_text(left_margin + text_offset, bottom - text_offset,
                anchor='sw', text=u'time (s)')

        # Add units along time axis.
        def scale_factor_gen():
            while True:
                yield 2
                yield 2.5
                yield 2
        scale_factor = scale_factor_gen()

        # Find out suitable unit interval.
        min_px_interval = 50  # Minimal tick width, in pixel.
        k = 0.01  # Seconds per tick.
        duration = self._flight.duration

        interv = adjusted_width / (duration / k)
        while interv < min_px_interval:
            k *= scale_factor.next()
            interv = adjusted_width / (duration / k)

        # Draw ticks.
        tick_len = 5
        text_value_offset = 15
        x = left_margin
        time_val = 0.0
        while time_val <= duration:
            self.create_line(x, bottom,
                    x, bottom + tick_len)
            self.create_text(x - text_value_offset,
                    bottom + text_offset,
                    anchor='nw',
                    text='%1.2f' % time_val)
            x += interv
            time_val += k

        # Draw curves.

        # Find out extrema.
        #
        # http://stackoverflow.com/a/4002806
        records = self._flight.records
        _, temp_max, alt_max = map(max, zip(*records))
        _, temp_min, alt_min = map(min, zip(*records))
        if temp_max == temp_min:
            temp_max += 1
            temp_min -= 1
        if alt_max == alt_min:
            alt_max += 0.1
            alt_min -= 0.1

        # Conversion routine.
        x_stride = 1.0 * adjusted_width / len(records)

        def y_alt_coord(altitude):
            rel_alt = 1.0 * (altitude - alt_min) / (alt_max - alt_min)
            return top_margin + (1.0 - rel_alt) * adjusted_height

        def y_temp_coord(temperature):
            rel_temp = 1.0 * (temperature - temp_min) / (temp_max - temp_min)
            return top_margin + (1.0 - rel_temp) * adjusted_height

        # Initial value.
        x_prev = left_margin
        y_alt_prev = y_alt_coord(records[0].altitude)
        y_temp_prev = y_temp_coord(records[0].temperature)

        # Following ones.
        for rec in records[1:]:
            x_next = x_prev + x_stride
            y_alt_next = y_alt_coord(rec.altitude)
            y_temp_next = y_temp_coord(rec.temperature)

            self.create_line(
                    x_prev, y_alt_prev,
                    x_next, y_alt_next,
                    fill='red')
            self.create_line(
                    x_prev, y_temp_prev,
                    x_next, y_temp_next,
                    fill='blue')

            x_prev = x_next
            y_alt_prev = y_alt_next
            y_temp_prev = y_temp_next


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

        # TODO: Flight display information (units...)
        label = tk.Label(self, anchor="w", text='TODO: Change display units')
        label.grid(column=1, row=1, columnspan=2, sticky='EW')

    def ask_for_file(self):
        filename = askopenfilename(filetypes=(
            (_(u'Flydream Altimeter Data'), '*.fda'),
            (_(u'All files'), '*.*')))
        self.load_file(filename)

    def load_file(self, filename):
        if filename:
            self.flight_list.load_fda_file(filename)

    def on_flight_selected(self, flight):
        self.flight_info.display_flight(flight)

# vim:nosi:
