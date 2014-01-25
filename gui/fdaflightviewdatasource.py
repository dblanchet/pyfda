
from util import flight_description
from smoothcurve import gaussian_filter, get_window_weights


class FdaFlightViewDataSource:

    GAUSSIAN_WINDOW_WIDTH = 9
    HEIGHT_MARGIN = 0.1
    TEMP_MARGIN = 1.0

    def __init__(self, flight):
        # Flight description.
        self.description = flight_description(flight)

        # Full data time range.
        self.time_min = 0.0
        self.time_max = flight.duration

        # Full data values.
        full_time_values = [rec.time for rec in flight.records]
        full_alt = [rec.altitude for rec in flight.records]
        full_temp = [rec.temperature for rec in flight.records]
        full_soft_alt = gaussian_filter(
                full_alt,
                get_window_weights(self.GAUSSIAN_WINDOW_WIDTH))

        self.full_data = zip(full_time_values, full_temp,
                full_alt, full_soft_alt)

        self.compute_extrema()

        # Displayed time information.
        self.time_scale = 1.0
        self.time_lo = 0.0
        self.time_hi = flight.duration

    def compute_extrema(self):

        # http://stackoverflow.com/a/4002806
        _, temp_max, alt_max, _ = map(max, zip(*self.full_data))
        _, temp_min, alt_min, _ = map(min, zip(*self.full_data))

        # Add small margin to constant values.
        #
        # A simple way to display them and
        # prevent division by zero exceptions.
        if temp_max == temp_min:
            temp_max += self.TEMP_MARGIN
            temp_min -= self.TEMP_MARGIN
        if alt_max == alt_min:
            alt_max += self.HEIGHT_MARGIN
            alt_min -= self.HEIGHT_MARGIN

        self.alt_min, self.alt_max = alt_min, alt_max
        self.temp_min, self.temp_max = temp_min, temp_max

    def set_time_scale(self, factor):

        assert factor >= 1.0

        self.time_scale = factor

        # Ensure time offset allow data display.
        time_range = (self.time_max - self.time_min) / self.time_scale
        if self.time_lo + time_range > self.time_max:
            self.time_hi = self.time_max
            self.time_lo = self.time_hi - time_range
        else:
            self.time_hi = self.time_lo + time_range

    def set_time_offset(self, offset):

        self.time_lo = offset

        # Ensure acceptable scrolling bounds.
        if self.time_lo < self.time_min:
            self.time_lo = self.time_min

        time_range = (self.time_max - self.time_min) / self.time_scale
        if self.time_lo + time_range > self.time_max:
            self.time_hi = self.time_max
            self.time_lo = self.time_hi - time_range
        else:
            self.time_hi = self.time_lo + time_range

    def get_displayed_sample_count(self):
        # Depending on scale factor, this count
        # may not be an integer value.
        return len(self.full_data) / self.time_scale

    def get_displayed_data(self):
        # Only return values, not timestamps.
        return [rec for rec in self.full_data
                if self.time_lo <= rec[0] <= self.time_hi]

    def find_nearest_values(self, time):
        # Return values except soften alt curve.
        return min(self.full_data, key=lambda x: abs(x[0] - time))[0:3]
