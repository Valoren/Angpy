## This module handles certain common colors.

import json
import os

COLOR_MAP = json.load(open(os.path.join('data', 'colors.txt'), 'r'))


## Given a color name, return the associated RGB tuple.
def getColor(name):
    # Ensure that name is a hashable type (and not, for example, a Numpy 
    # array). 
    if ((isinstance(name, str) or isinstance(name, unicode)) and 
            name in COLOR_MAP):
        return COLOR_MAP[name]
    # Assume that the name is already an RGB tuple and just return it.
    return name


## Convert an HSV input (hue, saturation, value) to RGB (red, green, blue).
# Returned values are in the range [0, 1].
# Cribbed from http://www.cs.rit.edu/~ncs/color/t_convert.html
def hsvToRgb(hue, saturation, value):
    if saturation == 0:
        # Greyscale.
        return (value, value, value)

    hue = hue % 360
    hue /= 60.0
    sector = int(hue)
    hueDecimal = hue - sector # Portion of hue after decimal point
    p = value * (1 - saturation)
    q = value * (1 - saturation * hueDecimal)
    t = (1 - saturation * (1 - hueDecimal))

    if sector == 0:
        return (value, t, p)
    if sector == 1:
        return (q, value, p)
    if sector == 2:
        return (p, value, t)
    if sector == 3:
        return (p, q, value)
    if sector == 4:
        return (t, p, value)
    return (value, p, q)

