# This file is (c) 2013 Richard Barrell <rchrd@brrll.co.uk>, see LICENSE.txt
# (it's the ISC license, which is 2-clause BSD with simplified wording)

# To compile the cmap code with gcc, use this invocation:
# gcc _cmap.c -o _cmap.so -fPIC -shared -O2 -std=c99 -Wall -Werror

import ctypes
import numpy
import numpy.ctypeslib
import os

heatMapArray = numpy.ctypeslib.ndpointer(
    dtype=numpy.int32,
    ndim=2,
    flags=('C_CONTIGUOUS', 'ALIGNED', 'WRITEABLE'),
)

# Assume that the compiled cmap code is in the same directory as this module.
mapLib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "_cmap.so"))
mapLib.burnHeatMap.argtypes = (
    ctypes.c_int32, ctypes.c_int32, heatMapArray,
    ctypes.c_size_t, ctypes.POINTER(ctypes.c_int32), 
    ctypes.POINTER(ctypes.c_int32))
mapLib.burnHeatMap.restype = ctypes.c_int


## Generate a heat map. We marshall our inputs into a format that the C code
# can understand, and then hand the actual work off to it.
def getHeatMap(gridMap, goals):
    # Explicitly copy gridMap into heatMap.
    heatMap = numpy.ndarray(gridMap.shape, dtype=numpy.int32, order='C')
    heatMap[:,:] = gridMap[:,:]

    # Copy the goals list into a format that's convenient for ctypes passing.
    goalsType = ctypes.c_int32 * len(goals)
    goalXs = goalsType()
    goalYs = goalsType()
    for i, (y, x) in enumerate(goals):
        goalXs[i] = x
        goalYs[i] = y

    xMax = heatMap.shape[1]
    yMax = heatMap.shape[0]

    errorLine = mapLib.burnHeatMap(xMax, yMax, heatMap, len(goals), 
            goalXs, goalYs)
    if errorLine != 0:
        raise MemoryError("allocation error in _cmap on line %d." % errorLine)
    return heatMap


