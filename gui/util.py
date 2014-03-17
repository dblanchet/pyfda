import gettext
translations = gettext.translation('messages', 'gui', fallback=True)
try:
    _ = translations.ugettext
except AttributeError:
    _ = translations.gettext


def flight_description(flight):
    return _('%3.3d - %10.3f secs @ %d Hz') % \
                (flight.index, flight.duration, flight.sampling_freq)
