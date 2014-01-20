def flight_description(flight):
    duration = flight.records[-1].time + 1.0 / flight.sampling_freq
    return '%3.3d - %10.3f secs @ %d Hz' % \
                (flight.index, duration, flight.sampling_freq)
