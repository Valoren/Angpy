import numpy


## Generate a "heat map" that represents how far away each cell in the provided
# map is from any of the goal cells. The heat map can be used to allow entities
# to move towards those goal cells by simply examining their neighbors and 
# moving to the one with the shortest remaining distance.
# \param gridMap A Numpy array where 0 represents "open" and any 
#         other value represents "closed"
# \param goals A list (set, etc.) of (x, y) tuples representing the goal
#        tiles. 
# \param maxDepth How far out from the goals to search; any locations further
#        out will have a value of -1 in the result.
def getHeatMap(gridMap, goals, maxDepth = 10**10):
    # A Numpy array of integers where each value is 
    # the distance the corresponding cell in gridMap is from any goal tile.
    # Start with all non-goal tiles at -1 and all goal tiles at 0.
    heatMap = numpy.ones(gridMap.shape, dtype = numpy.int32) * -1
    for x, y in goals:
        heatMap[(x, y)] = 0

    xVals, yVals = numpy.where(gridMap != 0)
    # Maps cells we've seen to their costs. Add unreachable cells here so we
    # never try to reach them.
    cellToCost = dict([((xVals[i], yVals[i]), -1) for i in xrange(len(xVals))])
    # Queue of cells waiting to be scanned.
    cellQueue = []
    # Max values to feed into xrange when getting neighbors.
    maxX = gridMap.shape[0]
    maxY = gridMap.shape[1]
    for x, y in goals:
        cellToCost[(x, y)] = 0
        for xi in xrange(max(0, x - 1), min(maxX, x + 2)):
            for yi in xrange(max(0, y - 1), min(maxY, y + 2)):
                if (xi, yi) not in cellToCost and gridMap[xi, yi] == 0: 
                    cellToCost[(xi, yi)] = 1
                    heatMap[(xi, yi)] = 1
                    cellQueue.append((xi, yi))

    # Pop a cell, examine its neighbors, and add any not-yet-processed
    # neighbors to the queue. This is a simple breadth-first search.
    while cellQueue:
        x, y = cellQueue.pop(0)
        cost = cellToCost[(x, y)]
        # Find all neighbors for whom we have a new route.
        # We could use a nested loop here but it's about 10% slower.
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), 
                (1, 0), (1, 1)]:
            neighbor = (x + dx, y + dy)
            if (neighbor[0] >= 0 and neighbor[0] < maxX and 
                    neighbor[1] >= 0 and neighbor[1] < maxY):
                if neighbor not in cellToCost:
                    cellToCost[neighbor] = cost + 1
                    heatMap[neighbor] = cost + 1
                    if cost + 1 < maxDepth:
                        cellQueue.append(neighbor)
    return heatMap


