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
