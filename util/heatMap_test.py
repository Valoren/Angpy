import pyximport; pyximport.install()
import cmap

import numpy

def test_getHeatMap():
    mapStrs = ["""000
000
000""", 
"""11111
10101
10101
10001
11111""",
"""00000000
01111110
00000010
01111110
01000000
01110110
00000000""",
"""00000
00000
00000"""]
    goals = [[(0, 0)], [(1, 1)], [(5, 2)], [(0, 1), (4, 1)]]
    expected = [
            [[0, 1, 2],
             [1, 1, 2],
             [2, 2, 2]],
            [[-1, -1, -1, -1, -1],
             [-1,  0,  1,  2, -1],
             [-1, -1, -1,  2, -1],
             [-1,  4,  3,  3, -1], 
             [-1, -1, -1, -1, -1]],
            [[6,   5,  5,  5,  6,  7,  8],
             [6,  -1,  4, -1, -1, -1,  8],
             [7,  -1,  3, -1, 13, -1,  9],
             [8,  -1,  2, -1, 12, -1, 10],
             [9,  -1,  1, -1, 12, 11, 11],
             [10, -1,  0, -1, 12, -1, 12],
             [11, -1, -1, -1, 13, -1, 13],
             [12, 12, 13, 14, 14, 14, 14]],
            [[1, 0, 1],
             [1, 1, 1],
             [2, 2, 2],
             [1, 1, 1],
             [1, 0, 1]],
    ]

    for i in xrange(len(mapStrs)):        
        # Conversion to array could be simpler but I want to use X/Y ordering
        # instead of Y/X.
        lines = mapStrs[i].split('\n')
        mapGrid = numpy.zeros((len(lines[0]), len(lines)))
        for j, line in enumerate(lines):
            mapGrid[:, j] = map(int, line)
        result = cmap.getHeatMap(mapGrid, goals[i])
        if numpy.any(result != expected[i]):
            print "Test %d failed" % i
            print "Expected:\n", expected[i]
            print "Got:\n", result
        assert numpy.all(result == expected[i])

def speedTest_getHeatMap():
    for i in xrange(10):
        grid = numpy.zeros((360, 240))
        cmap.getHeatMap(grid, [(0, 0)])

if __name__ == '__main__':
    test_getHeatMap()
    import cProfile
    cProfile.runctx('speedTest_getHeatMap()', locals(), globals(), 'profiling.txt')
