# -+- encoding: utf-8 -+-

import Tkinter as tk

import gettext
_ = gettext.translation('messages', 'gui', fallback=True).ugettext

import itertools

from util import flight_description
from smoothcurve import gaussian_filter, get_window_weights


class FdaFlightView(tk.Canvas):

    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, bg='lightgrey', *args, **kwargs)
        self._flight = None
        self._parent = parent
        self._scrolling = False

        self.bind('<Configure>', self.on_resize)
        self.bind('<Motion>', self.on_mouse_motion)
        self.bind('<ButtonPress-1>', self.on_button1_press)
        self.bind('<ButtonRelease-1>', self.on_button1_release)

    def set_x_scale(self, x_scale):
        self._x_scale = x_scale

        # Ensure time offset allow data display.
        adjusted_duration = self._flight.duration / x_scale
        if self._x_time_offset + adjusted_duration > self._flight.duration:
            self._x_time_offset = self._flight.duration - adjusted_duration

        # Save this value for many other usage later.
        self._adjusted_duration = adjusted_duration

    def on_button1_press(self, event):
        # Left mouse button triggers scrolling.
        #
        # But only if scaling allows it.
        if self._x_scale > 1.0:
            self._parent.config(cursor='sizing')

            self._scrolling = True
            self._scroll_orig = self._mouse_coords
            self._offset_orig = self._x_time_offset

    def on_button1_release(self, event):
        # No more scrolling when left
        # mouse button is released.
        self._parent.config(cursor='arrow')
        self._scrolling = False

    def on_mouse_motion(self, event):
        self._mouse_coords = event.x, event.y

        # DEBUG
        #mouse_pos = '(%d, %d)  ' % (x, y)
        #self.create_rectangle(200, 5, 300, 20, fill='lightgrey')
        #self.create_text(300, 5, anchor='ne', text=mouse_pos)

        if self._scrolling:
            # When scrolling, convert mouse move
            # to suitable user units.
            #
            # Time axis unit is seconds.
            x_orig, _ = self._scroll_orig
            x_offset = x_orig - event.x
            time_offset = self.px_to_seconds(x_offset)

            self._x_time_offset = self._offset_orig + time_offset

            # Ensure acceptable scrolling bounds.
            if self._x_time_offset < 0.0:
                self._x_time_offset = 0.0

            time_offset_limit = self._flight.duration - self._adjusted_duration
            if self._x_time_offset > time_offset_limit:
                self._x_time_offset = time_offset_limit

            # Refresh content.
            self.update_content()

    def display_flight(self, flight):
        self._flight = flight

        # Extract a few information.
        self.compute_flight_data_extrema(flight)

        # Reset zoom.
        self._x_scale = 1.0

        # Reset scrolling.
        self._x_time_offset = 0.0
        self._adjusted_duration = self._flight.duration

        # Triggers a redraw if size is known.
        self.on_resize(None)

    def px_to_seconds(self, px):
        # Scrolling conversion routine.
        sec_per_pixel = (self._adjusted_duration) / self._width
        return px * sec_per_pixel

    def compute_flight_data_extrema(self, flight):
        records = self._flight.records

        # http://stackoverflow.com/a/4002806
        _, temp_max, alt_max = map(max, zip(*records))
        _, temp_min, alt_min = map(min, zip(*records))

        # Add small margin to constant values.
        #
        # A simple way to display them and
        # prevent division by zero exceptions.
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
        self.draw_axis()
        self.draw_curves()

    def draw_title(self):
        title = flight_description(self._flight)
        self.create_text(5, 5, anchor='nw', text=title)

    def draw_axis(self):
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

        # Add unit labels.
        text_offset = 5

        self.create_text(left_margin + text_offset, top_margin + text_offset,
                anchor='nw', text=_(u'altitude (m)'), fill='red')
        self.create_text(right - text_offset, top_margin + text_offset,
                anchor='ne', text=_(u'temperature (°C)'), fill='blue')
        self.create_text(left_margin + text_offset, bottom - text_offset,
                anchor='sw', text=_(u'time (s)'))

        # Find out suitable unit interval.
        def adapt_axis_scale(full_val_range, px_width, min_val, min_px):

            val_min, val_max = full_val_range
            val_width = val_max - val_min

            val_result = min_val
            px_result = px_width / (val_width / val_result)

            scale_factor = itertools.cycle([2.0, 2.5, 2.0])
            while px_result <= min_px:
                val_result *= scale_factor.next()
                px_result = px_width / (val_width / val_result)

            return val_result, px_result

        # Add axis and unit ticks.
        tick_len = 5
        text_value_offset = 15

        # Draw horizontal (time) ticks.
        val_interv, px_interv = adapt_axis_scale(
                (0.0, self._adjusted_duration),
                adjusted_width,
                min_val=0.01, min_px=50)

        x = left_margin
        time_val = self._x_time_offset
        while time_val <= self._x_time_offset + self._adjusted_duration:
            self.create_line(x, bottom,
                    x, bottom + tick_len)
            self.create_text(x - text_value_offset,
                    bottom + text_offset,
                    anchor='nw',
                    text='%1.2f' % time_val)
            x += px_interv
            time_val += val_interv

        # Draw vertical axis.
        alt_min, alt_max = self._alt_min, self._alt_max
        temp_min, temp_max = self._temp_min, self._temp_max

        # Draw left vertical (length) ticks.
        val_interv, px_interv = adapt_axis_scale(
                (alt_min, alt_max),
                adjusted_height,
                min_val=0.25, min_px=30)

        y = top_margin
        height = alt_max
        while height >= alt_min:
            self.create_line(left_margin, y,
                    left_margin - tick_len, y)
            self.create_text(left_margin,
                    y,
                    anchor='ne',
                    text='%1.1f' % height)
            y += px_interv
            height -= val_interv

        # Draw right vertical (temperature) ticks.
        val_interv, px_interv = adapt_axis_scale(
                (temp_min, temp_max),
                adjusted_height,
                min_val=1.0, min_px=30)

        y = top_margin
        temp = temp_max
        while temp >= temp_min:
            self.create_line(width - right_margin, y,
                    width - left_margin + tick_len, y)
            self.create_text(width - right_margin + tick_len,
                    y,
                    anchor='nw',
                    text='%1.0f' % temp)
            y += px_interv
            temp -= val_interv

    def draw_curves(self):
        # TODO Remove duplicated code.
        width = self._width
        height = self._height

        # Area sizes and margins.
        left_margin = 40  # More digits for altitude axis.
        right_margin = 30  # Less digits for temperature axis.
        adjusted_width = width - left_margin - right_margin

        top_margin = 30  # Plot information.
        bottom_margin = 30  # Time axis
        adjusted_height = height - top_margin - bottom_margin

        # Y-axis value conversion routines.
        alt_min, alt_max = self._alt_min, self._alt_max
        temp_min, temp_max = self._temp_min, self._temp_max

        def y_alt_coord(altitude):
            rel_alt = 1.0 * (altitude - alt_min) / (alt_max - alt_min)
            return top_margin + (1.0 - rel_alt) * adjusted_height

        def y_temp_coord(temperature):
            rel_temp = 1.0 * (temperature - temp_min) / (temp_max - temp_min)
            return top_margin + (1.0 - rel_temp) * adjusted_height

        # Displayed part of data.
        records = [record for record in self._flight.records
                if self._x_time_offset <= record.time
                if record.time <= self._x_time_offset + self._adjusted_duration]

        # Softened altitude curve values.
        window_width = 9
        softened_altitude = gaussian_filter( \
                [rec.altitude for rec in records], \
                get_window_weights(window_width))

        # Initial values...
        x_prev = left_margin
        y_alt_prev = y_alt_coord(records[0].altitude)
        y_temp_prev = y_temp_coord(records[0].temperature)
        y_soft_prev = y_alt_coord(softened_altitude[0])

        # ... then following ones.
        x_stride = 1.0 * adjusted_width / (len(records) - 1)
        for index, rec in enumerate(records[1:]):
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
