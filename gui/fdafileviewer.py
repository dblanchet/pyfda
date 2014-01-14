#!/usr/bin/python
# -+- encoding: utf-8 -+-

import Tkinter as tk
from tkFileDialog import askopenfilename

from flydream.uploadeddata import UploadedData
from flydream.dataparser import DataParser

import gettext
_ = gettext.translation('pyfdagui', fallback=True).ugettext


# http://geekyjournal.blogspot.fr/2011/10/
#              gaussian-filter-python-implementation.html
from math import exp


def get_window_weights(N):
    support_points = [(float(3 * i) / float(N)) ** 2.0
            for i in range(-N, N + 1)]
    gii_factors = [exp(-(i / 2.0)) for i in support_points]
    ki = float(sum(gii_factors))
    return [giin / ki for giin in gii_factors]


def apply_filter(index, array, window):
    N = (len(window) - 1) / 2
    # Fix out of range exception.
    array_l = [array[0] for i in range(N)] \
                + array \
                + [array[-1] for i in range(N)]
    return sum(float(array_l[N + index + i]) * window[N + i]
            for i in range(-N, N + 1))


def gaussian_filter(data, window_weights, filter_func=apply_filter):
    ret = []
    for i in range(len(data)):
        ret.append(filter_func(i, data, window_weights))
    return ret


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
        self.bind('<Motion>', self.on_mouse_motion)

    def display_flight(self, flight):
        self._flight = flight
        self.compute_flight_data_extrema(flight)

        self._x_scale = 1.0
        self._y_scale = 1.0


        # Triggers a redraw if size is known.
        self.on_resize(None)

    def on_mouse_motion(self, event):
        mouse_pos = '(%d, %d)  ' % (event.x, event.y)
        self.create_rectangle(200, 5, 300, 20, fill='lightgrey')
        self.create_text(300, 5, anchor='ne', text=mouse_pos)

    def compute_flight_data_extrema(self, flight):
        records = self._flight.records

        # http://stackoverflow.com/a/4002806
        _, temp_max, alt_max = map(max, zip(*records))
        _, temp_min, alt_min = map(min, zip(*records))

        # Add small margin to constant values.
        if temp_max == temp_min:
            temp_max += 1
            temp_min -= 1
        if alt_max == alt_min:
            alt_max += 0.1
            alt_min -= 0.1

        self._alt_min, self._alt_max = alt_min, alt_max
        self._temp_min, self._temp_max = temp_min, temp_max
        self.total_duration = self._flight.duration

    def on_resize(self, event):

        # Get new canvas size.
        width = self.winfo_width()
        if width == 1:
            return
        self._width = width

        height = self.winfo_height()
        if height == 1:
            return
        self._height = height

        # If size is properly defined,
        # refresh content.
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
        width = self._width
        height = self._height

        # Area sizes and margins.
        left_margin = 40  # More digits for altitude axis.
        right_margin = 30  # Less digits for temperature axis.
        adjusted_width = width - left_margin - right_margin

        top_margin = 30  # Plot information.
        bottom_margin = 30  # Time axis
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
        tick_len = 5
        text_value_offset = 15

        def adapt_axis_scale(full_val_range, px_width, min_val, min_px):

            def scale_factor_gen():
                while True:
                    yield 2
                    yield 2.5
                    yield 2
            scale_factor = scale_factor_gen()

            val_min, val_max = full_val_range
            val_width = val_max - val_min

            val_result = min_val
            px_result = px_width / (val_width / val_result)

            while px_result <= min_px:
                val_result *= scale_factor.next()
                px_result = px_width / (val_width / val_result)

            return val_result, px_result

        # Find out suitable unit interval.
        duration = self._flight.duration / self._x_scale
        k, interv = adapt_axis_scale(
                (0.0, duration),
                adjusted_width,
                min_val=0.01, min_px=50)

        # Draw ticks.
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
        alt_min, alt_max = self._alt_min, self._alt_max
        temp_min, temp_max = self._temp_min, self._temp_max

        # Draw length units.
        k, interv = adapt_axis_scale(
                (alt_min, alt_max),
                adjusted_height,
                min_val=0.25, min_px=30)

        # Draw ticks.
        y = top_margin
        height = alt_max
        while height >= alt_min:
            self.create_line(left_margin, y,
                    left_margin - tick_len, y)
            self.create_text(left_margin,
                    y,
                    anchor='ne',
                    text='%1.1f' % height)
            y += interv
            height -= k

        # Draw temperature units.
        k, interv = adapt_axis_scale(
                (temp_min, temp_max),
                adjusted_height,
                min_val=1.0, min_px=30)

        # Draw ticks.
        y = top_margin
        temp = temp_max
        while temp >= temp_min:
            self.create_line(width - right_margin, y,
                    width - left_margin + tick_len, y)
            self.create_text(width - right_margin + tick_len,
                    y,
                    anchor='nw',
                    text='%1.0f' % temp)
            y += interv
            temp -= k

        # Y-axis conversion routines.
        def y_alt_coord(altitude):
            rel_alt = 1.0 * (altitude - alt_min) / (alt_max - alt_min)
            return top_margin + (1.0 - rel_alt) * adjusted_height

        def y_temp_coord(temperature):
            rel_temp = 1.0 * (temperature - temp_min) / (temp_max - temp_min)
            return top_margin + (1.0 - rel_temp) * adjusted_height

        records = self._flight.records

        # Softened altitude curve values.
        window_width = 9
        softened_altitude = gaussian_filter( \
                [rec.altitude for rec in records], \
                get_window_weights(window_width))

        # Initial values.
        x_prev = left_margin
        y_alt_prev = y_alt_coord(records[0].altitude)
        y_temp_prev = y_temp_coord(records[0].temperature)
        y_soft_prev = y_alt_coord(softened_altitude[0])

        # Following ones.
        scaled_len = len(records) / self._x_scale
        x_stride = 1.0 * adjusted_width / scaled_len
        for index, rec in enumerate(records[1:int(scaled_len) + 1]):
            x_next = x_prev + x_stride
            y_alt_next = y_alt_coord(rec.altitude)
            y_temp_next = y_temp_coord(rec.temperature)
            y_soft_next = y_alt_coord(softened_altitude[1 + index])

            self.create_line(
                    x_prev, y_alt_prev,
                    x_next, y_alt_next,
                    fill='red')
            self.create_line(
                    x_prev, y_soft_prev,
                    x_next, y_soft_next,
                    fill='darkred', width=3.0)
            self.create_line(
                    x_prev, y_temp_prev,
                    x_next, y_temp_next,
                    fill='blue', width=2.0)

            x_prev = x_next
            y_alt_prev = y_alt_next
            y_temp_prev = y_temp_next
            y_soft_prev = y_soft_next


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
        self.scale = tk.Scale(self, orient=tk.HORIZONTAL,
                from_=1.0, to=100.0, resolution=0.1)
        self.scale.grid(column=1, row=1, columnspan=2, sticky='EW')
        self.scale.bind('<ButtonPress>', self.scale_pressed)
        self.scale.bind('<ButtonRelease>', self.scale_released)

    def scale_pressed(self, event):
        event.widget.bind('<Motion>', self.scale_changed)

    def scale_released(self, event):
        event.widget.unbind('<Motion>')

    def scale_changed(self, event):
        self.flight_info._x_scale = event.widget.get()
        self.flight_info.update_content()

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
        self.scale.set(1.0)

# vim:nosi:
