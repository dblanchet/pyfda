# -+- encoding: utf-8 -+-

import itertools

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import gettext
translations = gettext.translation('messages', 'gui', fallback=True)
try:
    _ = translations.ugettext
except AttributeError:
    _ = translations.gettext


class FdaFlightView(tk.Canvas):

    LEFT_MARGIN = 40        # Digits of vertical altitude left axis.
    RIGHT_MARGIN = 30       # Digits of vertical temperature right axis.
    TOP_MARGIN = 30         # Plot title.
    BOTTOM_MARGIN = 30      # Digits of horizontal time bottom axis.

    AXIS_MARGIN = 5         # Minimal distance between axis and curves.

    LABEL_X_OFFSET = 10     # Distance between value on curve and label.

    BACKGROUND_COLOR = 'lightgrey'
    AXIS_COLOR = 'black'

    ALTITUDE_CURVE_COLOR = 'red'
    SOFTEN_ALTITUDE_CURVE_COLOR = 'darkred'
    TEMP_CURVE_COLOR = 'blue'

    MAX_ALTITUDE_COLOR = 'green'

    CURRENT_ALTITUDE_COLOR = 'yellow'
    CURRENT_SOFT_ALT_COLOR = 'orange'
    CURRENT_TEMP_COLOR = 'lightblue'

    LABEL_FILL_COLOR = 'khaki1'
    LABEL_OULINE_COLOR = AXIS_COLOR

    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, bg=self.BACKGROUND_COLOR,
                *args, **kwargs)
        self._data_source = None
        self._parent = parent
        self._scrolling = False

        self.bind('<Configure>', self.on_resize)
        self.bind('<Motion>', self.on_mouse_motion)
        self.bind('<ButtonPress-1>', self.on_button1_press)
        self.bind('<ButtonRelease-1>', self.on_button1_release)

        self.mouse_info_fmt = _(u'- Pointer at %.3f secs: %.1f °C and %.1f m')

        # Prevent unwanted refresh.
        self.prev_time = -1

    def set_x_scale(self, x_scale):

        # Do nothing if no data is displayed.
        if self._data_source is None:
            return

        self._x_scale = x_scale
        self._data_source.set_time_scale(x_scale)

        # Depending on previous scrolling and
        # scaling value, scrolling position may
        # have changed.
        self._x_time_offset = self._data_source.time_lo

        # Refresh content.
        self.update_content()

    # X axis conversion routines.

    def px_to_seconds(self, px):
        src = self._data_source
        adjusted_duration = src.time_hi - src.time_lo

        sec_per_pixel = adjusted_duration / self._adjusted_width
        return px * sec_per_pixel

    def seconds_to_px(self, seconds):
        src = self._data_source
        adjusted_duration = src.time_hi - src.time_lo

        px_per_seconds = self._adjusted_width / adjusted_duration
        return seconds * px_per_seconds

    # Y axis conversion routines.

    def px_to_alt(self, px):
        src = self._data_source
        alt_range = src.alt_max - src.alt_min

        rel_px = (1.0 * px - self.TOP_MARGIN) / self._adjusted_height
        return src.alt_min + (1.0 - rel_px) * alt_range

    def px_to_temp(self, px):
        src = self._data_source
        temp_range = src.temp_max - src.temp_min

        rel_px = (1.0 * px - self.TOP_MARGIN) / self._adjusted_height
        return src.temp_min + (1.0 - rel_px) * temp_range

    def alt_to_px(self, altitude):
        src = self._data_source
        alt_min, alt_max = src.alt_min, src.alt_max

        rel_alt = 1.0 * (altitude - alt_min) / (alt_max - alt_min)
        return self.TOP_MARGIN + (1.0 - rel_alt) * self._adjusted_height

    def temp_to_px(self, temperature):
        src = self._data_source
        temp_min, temp_max = src.temp_min, src.temp_max

        rel_temp = 1.0 * (temperature - temp_min) / (temp_max - temp_min)
        return self.TOP_MARGIN + (1.0 - rel_temp) * self._adjusted_height

    def on_button1_press(self, event):

        # Do nothing if no data is displayed.
        if self._data_source is None:
            return

        # Left mouse button triggers scrolling.
        #
        # But only if scaling allows it.
        if self._x_scale > 1.0:
            self._parent.config(cursor='sizing')

            self._scrolling = True
            self._scroll_orig = event.x, event.y
            self._offset_orig = self._x_time_offset

    def on_button1_release(self, event):
        # No more scrolling when left
        # mouse button is released.
        self._parent.config(cursor='arrow')
        self._scrolling = False

    def on_mouse_motion(self, event):

        # Do nothing if no data is displayed.
        if self._data_source is None:
            return

        x, y = event.x, event.y

        if self._scrolling:

            # When scrolling, convert mouse move
            # to suitable user units.
            #
            # Time axis unit is seconds.
            x_orig, _ = self._scroll_orig
            x_offset = x_orig - x
            time_offset = self._offset_orig + self.px_to_seconds(x_offset)

            # Tell data source.
            self._data_source.set_time_offset(time_offset)

            # Refresh content if a scroll occured.
            prev_time_offset = self._x_time_offset
            self._x_time_offset = self._data_source.time_lo
            if self._x_time_offset != prev_time_offset:
                self.update_content()

        else:

            # Check if mouse pointer is in curves' zone.
            if self.LEFT_MARGIN <= x <= self._width - self.RIGHT_MARGIN \
                and self.TOP_MARGIN <= y <= self._height - self.BOTTOM_MARGIN:

                # Give information about hovered value.
                self.update_pointer_info(x, y)

            else:
                # Remove previous information.
                self.remove_mouse_info()
                self.remove_value_info()

    def display_flight_data(self, data_source):
        self._data_source = data_source

        # Reset horizontal scaling.
        self._x_scale = 1.0

        # Reset horizontal scrolling.
        self._x_time_offset = 0.0

        # Triggers a redraw if size is known.
        self.on_resize(None)

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

        # Curve area size.
        self._adjusted_width = width - self.LEFT_MARGIN - self.RIGHT_MARGIN
        self._adjusted_height = height - self.TOP_MARGIN - self.BOTTOM_MARGIN

        # If size is properly defined,
        # refresh content.
        self.update_content()

    def update_content(self):
        # Reset Canvas content.
        self.delete(tk.ALL)

        # Stop if no data to be drawn.
        if not self._data_source:
            return

        # Draw all the parts.
        self.draw_title()
        self.draw_axis()
        self.draw_curves()
        self.draw_max_alt()

    def draw_title(self):
        # Flight description in upper left corner.
        title = self._data_source.description
        self.create_text(5, 5, anchor='nw', text=title)

    def draw_axis(self):
        # Draw axis lines.
        top = self.TOP_MARGIN - self.AXIS_MARGIN
        bottom = self._height - self.BOTTOM_MARGIN + self.AXIS_MARGIN
        right = self._width - self.RIGHT_MARGIN

        left_margin = self.LEFT_MARGIN
        self.create_line(left_margin, top,
                left_margin, bottom,
                fill=self.AXIS_COLOR)
        self.create_line(left_margin, bottom,
                right, bottom,
                fill=self.AXIS_COLOR)
        self.create_line(right, top,
                right, bottom,
                fill=self.AXIS_COLOR)

        # Add unit labels.
        text_offset = 5

        top_margin = self.TOP_MARGIN
        self.create_text(
                left_margin + text_offset,
                top_margin + text_offset,
                anchor='nw', text=_(u'altitude (m)'),
                fill=self.ALTITUDE_CURVE_COLOR)
        self.create_text(
                right - text_offset,
                top_margin + text_offset,
                anchor='ne', text=_(u'temperature (°C)'),
                fill=self.TEMP_CURVE_COLOR)
        self.create_text(
                left_margin + text_offset,
                bottom - text_offset,
                anchor='sw', text=_(u'time (s)'),
                fill=self.AXIS_COLOR)

        # Find out suitable unit interval.
        def adapt_axis_scale(full_val_range, px_width, min_val, min_px):

            val_min, val_max = full_val_range
            val_width = val_max - val_min

            val_result = min_val
            px_result = px_width / (val_width / val_result)

            scale_factor = itertools.cycle((2.0, 2.5, 2.0))
            for scale in scale_factor:
                if px_result > min_px:
                    break
                val_result *= scale
                px_result = px_width / (val_width / val_result)

            return val_result, px_result

        # Add axis and unit ticks.
        tick_len = 5
        text_value_offset = 15

        # Draw horizontal (time) ticks.
        src = self._data_source
        adjusted_duration = src.time_hi - src.time_lo
        val_interv, px_interv = adapt_axis_scale(
                (0.0, adjusted_duration),
                self._adjusted_width,
                min_val=0.01, min_px=50)

        x = left_margin
        time_val = self._x_time_offset
        while time_val <= self._x_time_offset + adjusted_duration:
            self.create_line(x, bottom,
                    x, bottom + tick_len)
            self.create_text(x - text_value_offset,
                    bottom + text_offset,
                    anchor='nw',
                    text='%1.2f' % time_val)
            x += px_interv
            time_val += val_interv

        # Draw vertical axis.
        alt_min, alt_max = src.alt_min, src.alt_max
        temp_min, temp_max = src.temp_min, src.temp_max

        # Draw left vertical (length) ticks.
        val_interv, px_interv = adapt_axis_scale(
                (alt_min, alt_max),
                self._adjusted_height,
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
                self._adjusted_height,
                min_val=1.0, min_px=30)

        y = top_margin
        temp = temp_max
        while temp >= temp_min:
            self.create_line(self._width - self.RIGHT_MARGIN, y,
                    self._width - left_margin + tick_len, y)
            self.create_text(self._width - self.RIGHT_MARGIN + tick_len,
                    y,
                    anchor='nw',
                    text='%1.0f' % temp)
            y += px_interv
            temp -= val_interv

    def draw_curves(self):
        # Displayed part of data.
        src = self._data_source
        curve_data = src.get_displayed_data()

        # Initial values...
        time, temp, alt, soft_alt = curve_data[0]

        rel_time = time - self._x_time_offset
        x_prev = self.LEFT_MARGIN + self.seconds_to_px(rel_time)

        y_temp_prev = self.temp_to_px(temp)
        y_alt_prev = self.alt_to_px(alt)
        y_soft_prev = self.alt_to_px(soft_alt)

        # ... then following ones.
        x_stride = self._adjusted_width / src.get_displayed_sample_count()
        for time, temp, alt, soft_alt in curve_data[1:]:
            x_next = x_prev + x_stride

            y_temp_next = self.temp_to_px(temp)
            y_alt_next = self.alt_to_px(alt)
            y_soft_next = self.alt_to_px(soft_alt)

            self.create_line(
                    x_prev, y_temp_prev,
                    x_next, y_temp_next,
                    fill=self.TEMP_CURVE_COLOR,
                    width=2.0)
            self.create_line(
                    x_prev, y_soft_prev,
                    x_next, y_soft_next,
                    fill=self.SOFTEN_ALTITUDE_CURVE_COLOR,
                    width=3.0)
            self.create_line(
                    x_prev, y_alt_prev,
                    x_next, y_alt_next,
                    fill=self.ALTITUDE_CURVE_COLOR)

            x_prev = x_next
            y_alt_prev = y_alt_next
            y_temp_prev = y_temp_next
            y_soft_prev = y_soft_next

    def draw_max_alt(self):
        src = self._data_source
        time_lo, time_hi = src.time_lo, src.time_hi

        max_alt = self._data_source.get_max_alt()
        for time, alt in max_alt:

            if not time_lo <= time <= time_hi:
                continue

            rel_time = time - self._x_time_offset
            px_time = self.LEFT_MARGIN + self.seconds_to_px(rel_time)

            px_alt = self.alt_to_px(alt)

            self.create_rectangle(px_time - 3, px_alt - 3,
                px_time + 3, px_alt + 3,
                outline=self.MAX_ALTITUDE_COLOR, width=3.0)

    def update_pointer_info(self, x, y):
        # Find time value for current x coordinate.
        rel_time = self.px_to_seconds(x - self.LEFT_MARGIN)
        abs_time = rel_time + self._x_time_offset

        # Tell user about mouse pointer information.
        self.update_mouse_info(abs_time, y)

        # Get nearest pointed value.
        src = self._data_source
        time, temp, alt, soft = src.find_nearest_values(abs_time)

        # Do not update canvas if value did not change.
        if self.prev_time == time:
            return
        self.prev_time = time

        # Tell user about nearest value.
        self.update_value_info(time, temp, alt, soft)

    def update_mouse_info(self, time, y):
        # Remove previous information.
        self.remove_mouse_info()

        # Show mouse position information to user.
        pointed_value = self.mouse_info_fmt % \
                (time, self.px_to_temp(y), self.px_to_alt(y))
        self.mpos = self.create_text(200, 5, anchor='nw',
                text=pointed_value)

    def update_value_info(self, time, temp, alt, soft):
        # Remove previous information.
        self.remove_value_info()

        # Draw vertical line over the curves.
        vline_px = self.LEFT_MARGIN + \
                self.seconds_to_px(time - self._x_time_offset)
        vline = self.create_line(
                vline_px,
                self.TOP_MARGIN - self.AXIS_MARGIN,
                vline_px,
                self._height - self.BOTTOM_MARGIN + self.AXIS_MARGIN)
        self.value_info_items.append(vline)

        # Show pointed value information to user.
        px_temp = self.temp_to_px(temp)
        temp_val_rect = self.create_rectangle(
                vline_px - 3, px_temp - 3,
                vline_px + 3, px_temp + 3,
                outline=self.CURRENT_TEMP_COLOR,
                width=3.0)
        self.value_info_items.append(temp_val_rect)

        px_soft = self.alt_to_px(soft)
        soft_val_rect = self.create_rectangle(
                vline_px - 3, px_soft - 3,
                vline_px + 3, px_soft + 3,
                outline=self.CURRENT_SOFT_ALT_COLOR,
                width=3.0)
        self.value_info_items.append(soft_val_rect)

        px_alt = self.alt_to_px(alt)
        alt_val_rect = self.create_rectangle(
                vline_px - 3, px_alt - 3,
                vline_px + 3, px_alt + 3,
                outline=self.CURRENT_ALTITUDE_COLOR,
                width=3.0)
        self.value_info_items.append(alt_val_rect)

        # Draw labels with numerical values.

        # Get label sizes.
        scratch = tk.Canvas()

        def text_item_size(text):
            text_id = scratch.create_text(0, 0, text=text, anchor='nw')
            bounds = scratch.bbox(text_id)
            scratch.delete(text_id)
            return bounds[2:]

        alt_text = _(u'%.1f m') % alt
        alt_val_witdh, alt_val_height = text_item_size(alt_text)

        soft_text = _(u'%.1f m') % soft
        soft_val_witdh, soft_val_height = text_item_size(soft_text)

        temp_text = _(u'%d °C') % temp
        temp_val_witdh, temp_val_height = text_item_size(temp_text)

        # Take care not to overlap vertical axis.
        largest = max(alt_val_witdh, soft_val_witdh, temp_val_witdh) \
                + self.LABEL_X_OFFSET
        align_right = vline_px + largest >= self._width - self.RIGHT_MARGIN

        # Properly flow the label without overlaps.
        highest = max(alt_val_height, soft_val_height, temp_val_height)
        px_l_alt, px_l_soft, px_l_temp = self.distribute_labels(
                px_alt, px_soft, px_temp,
                min_y=self.TOP_MARGIN,
                max_y=self._height - self.BOTTOM_MARGIN,
                label_height=highest)

        # Draw labels.
        items = self.draw_label(vline_px, px_l_alt,
                        alt_val_witdh, alt_val_height,
                        text=alt_text, align=align_right,
                        fill=self.ALTITUDE_CURVE_COLOR)
        self.value_info_items.extend(items)

        items = self.draw_label(vline_px, px_l_soft,
                soft_val_witdh, soft_val_height,
                text=soft_text, align=align_right,
                fill=self.SOFTEN_ALTITUDE_CURVE_COLOR)
        self.value_info_items.extend(items)

        items = self.draw_label(vline_px, px_l_temp,
                temp_val_witdh, temp_val_height,
                text=temp_text, align=align_right,
                fill=self.TEMP_CURVE_COLOR)
        self.value_info_items.extend(items)

    def draw_label(self, x, y, width, height, text, align, fill):
        items = []
        if align:
            xo = x - self.LABEL_X_OFFSET - width
        else:
            xo = x + self.LABEL_X_OFFSET
        items.append(self.create_rectangle(
                xo, y, xo + width, y - height,
                outline=self.LABEL_OULINE_COLOR,
                fill=self.LABEL_FILL_COLOR))
        items.append(self.create_text(
                xo, y,
                anchor='sw', text=text,
                fill=fill))
        return items

    def distribute_labels(self, alt, soft, temp, min_y, max_y, label_height):
        # Order values per vertical positions.
        #
        # list(zip(()) because Python3's zip returns a generator.
        y_offset = 1.0 * label_height / 2
        l = list(zip((alt + y_offset, soft + y_offset, temp + y_offset),
            range(3)))
        l.sort(key=lambda x: x[0])
        r = list(zip(*l))
        order = r[1]
        y0, y1, y2 = r[0]

        # Ensure no labels overlap.
        if y2 - y1 < label_height:
            y2 = y1 + label_height

        if y1 - y0 < label_height:
            y1 = y0 + label_height

            if y2 - y1 < label_height:
                y2 = y1 + label_height

        # Ensure top label is inside curve zone.
        if y0 - label_height < self.TOP_MARGIN:
            y0 = self.TOP_MARGIN + label_height

            if y1 - y0 < label_height:
                y1 = y0 + label_height

                if y2 - y1 < label_height:
                    y2 = y1 + label_height

        # Ensure bottom label is still inside curve zone.
        if y2 >= self._height - self.BOTTOM_MARGIN:
            y2 = self._height - self.BOTTOM_MARGIN

            if y2 - y1 < label_height:
                y1 = y2 - label_height

                if y1 - y0 < label_height:
                    y0 = y1 - label_height

        # Restore expected order.
        #
        # list(zip(()) because Python3's zip returns a generator.
        l = list(zip((y0, y1, y2), order))
        l.sort(key=lambda x: x[1])
        return list(zip(*l))[0]

    def remove_mouse_info(self):
        try:
            self.delete(self.mpos)
        except AttributeError:
            pass
        finally:
            self.mpos = None

    def remove_value_info(self):
        try:
            for item in self.value_info_items:
                self.delete(item)
        except AttributeError:
            pass
        finally:
            self.value_info_items = []
