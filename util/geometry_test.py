import geometry
import numpy

def test_getAdjacent():
    grid = numpy.zeros((6, 4))
    items = [i for i in geometry.getAdjacent(0, 0)]
    assert items == [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), 
            (1, 0), (1, 1)]
    items = [i for i in geometry.getAdjacent(0, 0, grid = grid)]
    assert items == [(0, 1), (1, 0), (1, 1)]
    items = [i for i in geometry.getAdjacent(5, 3, grid = grid)]
    assert items == [(4, 2), (4, 3), (5, 2)]


def test_generateCone():
    for start, direction, sequence in [
            ((0, 0), (1, 0), [(1, 0), (1, 1), (1, -1), (2, 0), (2, 1), (2, -1), (2, 2), (2, -2)]),
            ((5, 5), (-1, 0), [(4, 5), (4, 4), (4, 6), (3, 5), (3, 4), (3, 6), (3, 3), (3, 7)])]:
        iterator = geometry.generateCone(start, direction)
        for i, loc in enumerate(iterator):
            if i == len(sequence):
                break
            if loc != sequence[i]:
                print "Cone failure; expected %s got %s" % (sequence[i], loc)
            assert loc == sequence[i]


def test_aStarSearch():
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
00000000"""]
    starts = [(0, 0), (1, 1), (5, 2)]
    ends = [(2, 2), (3, 1), (2, 4)]
    expectedPaths = (
            ((0, 0), (1, 1), (2, 2)), 
            ((1, 1), (1, 2), (2, 3), (3, 2), (3, 1)), 
            ((5, 2), (4, 2), (3, 2), (2, 2), (1, 2), (0, 3), (0, 4), 
                (0, 5), (1, 6), (2, 6), (3, 6), (4, 5), (3, 4), (2, 4))
    )

    for i in xrange(len(mapStrs)):        
        # Conversion to array could be simpler but I want to use X/Y ordering
        # instead of Y/X.
        lines = mapStrs[i].split('\n')
        mapGrid = numpy.zeros((len(lines[0]), len(lines)))
        for j, line in enumerate(lines):
            mapGrid[:, j] = map(int, line)
        path = geometry.aStarSearch(mapGrid, starts[i], ends[i])
        assert tuple(path) == expectedPaths[i]


if __name__ == '__main__':
    test_getAdjacent()
    test_generateCone()
    test_aStarSearch()
