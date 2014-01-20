import gettext
_ = gettext.translation('messages', 'gui', fallback=True).ugettext


def flight_description(flight):
    return _('%3.3d - %10.3f secs @ %d Hz') % \
                (flight.index, flight.duration, flight.sampling_freq)
