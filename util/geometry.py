## This module handles various geometry tasks, like finding lines or circles.

import copy
import math
import numpy
import random

## Useful constants
cardinalDirections = ((0, 1), (1, 0), (0, -1), (-1, 0))

## Given a tuple specifying a direction, change it to one 90 degrees away
#  The parameter clockwise specifies the chance of moving in a clockwise
#  direction, set it to 0 or 100 if you want it determined which direction
#  to turn
def changeCardinalDirection(direction, clockwise = 50):
    if len(direction) != 2:
        raise RuntimeError("Directions must have two elements")
    
    # If we move 90 degrees, x and y swap
    yDir = direction[0]
    xDir = direction[1]
    
    isClockwise = (random.randint(1, 100) <= clockwise)
    
    # Factor for multiplication
    mult = [-1, 1][isClockwise]
    
    if direction[0]: 
        return(xDir, yDir * mult)
    if direction[1]: 
        return(xDir * -1 * mult, yDir)
    
    # you entered a null direction direction coordinate
    return (0, 0)


## Given a directional offset to an adjacent tile (either orthogonally or 
# diagonally adjacent), return the two directions "next to" that direction (i.e.
# 45-degree rotations of that direction's vector). 
def getAdjacentDirections(direction):
    directions = [(1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1),
            (0, 1)]
    index = directions.index(direction)
    first = (index - 1) % len(directions)
    second = (index + 1) % len(directions)
    return (directions[first], directions[second])


## Return Euclidean square distance between two points
def distanceSquared(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    

## Return distance on a grid, i.e. where moving diagonally has the same cost
# as moving orthogonally.
def gridDistance(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

        
## Given a start point and an end point pick the proper cardinal direction that will
#  get us closest to our target (in physics parlance, minimal impact parameter)
#  The return is xDirection, yDirection, one of which is 0 and the other is either 
#  1 or -1.
def getCardinalDirection(start, end):
    x1, y1 = start
    x2, y2 = end
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    # Target lies to the east
    if (x2 >= x1) and (dx >= dy): 
        return (1, 0)
    # Target lies to the west
    if (x2 < x1) and (dx >= dy): 
        return (-1, 0)
    # Target lies to the south
    if (y2 >= y1) and (dy > dx): 
        return (0, 1)
    # Target lies to the north
    if (y2 < y1) and (dy > dx): 
        return (0, -1)
    
    # You moron, you passed in the same point for start and end
    return (0, 0)
    

## Given two sets find the set of points that are closest to each other
#   it makes a good-faith effort to find two points that are reasonably 
#   close to each other, while explicitly not trying to find the absolute 
#   closest pair to avoid an N^2 algorithm.
def getClosestPoints(setA, setB):
    # pick a random location in setA
    guessA = random.choice(list(setA))
    # find the closest point in set B to our guess
    guessB = getNearbyLocation(setB, guessA, closeness = 1)
    # now find the closest point in A to guessB
    guessA = getNearbyLocation(setA, guessB, closeness = 1)
    # We could iterate some more but there really isn't a reason to
    return guessA, guessB
    

## Returns a list of locations evenly spaced in the grid.  All four
#  corner points are included.  This is used for finding center locations
#  in caverns, and can also be used for speeding up checking for room
#  overlap conflicts for rectangular areas.    
def getMesh(xWest, yNorth, width, height, spacing):
    mesh = []
    for y in xrange(yNorth, yNorth + height, spacing):
        for x in xrange(xWest, xWest + width, spacing):
            mesh.append((x, y))
        # add the westernmost row always.
        mesh.append((xWest + width, y))
    # do the southern row
    for x in xrange(xWest, xWest + width, spacing):
        mesh.append((x, yNorth + height))
    # Finally, include the SW corner
    mesh.append((xWest + width, yNorth + height))
    return mesh

    
## Given a set of locations, return a random cell from that set that's close
# to the target
# /todo enable the closeness parameter specifying how many close cells to
# include. I.e. if closeness is 5 it will return a random location in the top
# 5 closest. If closeness is <= 1 it will return the closest cell. 
def getNearbyLocation(locationSet, target, closeness = 1):
    if not locationSet: 
        return
    locationList = list(locationSet)
    closest = locationList[0]
    closestDistance = distanceSquared(locationList[0], target)
    for loc in locationList:
        if distanceSquared(loc, target) < closestDistance:
            closest = loc
            closestDistance = distanceSquared(loc, target)
    return closest
    
    
## Given a location and a cardinal direction, find the squares that are
#  parallel to the given square with given offset.
def getParallelCells(location, direction, offset = 1):
    x, y = location
    cwDir = changeCardinalDirection(direction, clockwise = 100)
    ccwDir = changeCardinalDirection(direction, clockwise = 0)
    x1 = x + cwDir[0] * offset
    x2 = x + ccwDir[0] * offset
    y1 = y + cwDir[1] * offset
    y2 = y + ccwDir[1] * offset
    return (x1, y1), (x2, y2)
    
    
## Return a list of (x, y) tuples describing all of the tiles between the 
# start tile and the end tile, inclusive. Uses Bresenham's algorithm, as
# adapted from:
# http://www.gamedev.net/page/resources/_/technical/game-programming/line-drawing-algorithm-explained-r1275
def getLineBetween(start, end):
    result = []
    x1, y1 = start
    x2, y2 = end
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x = x1
    y = y1
    
    if x2 >= x1:
        xInc1 = 1
        xInc2 = 1
    else:
        xInc1 = -1
        xInc2 = -1
        
    if y2 >= y1:
        yInc1 = 1
        yInc2 = 1
    else:
        yInc1 = -1
        yInc2 = -1

    if dx >= dy:
        xInc1 = 0
        yInc2 = 0
        denominator = dx
        numerator = dx / 2
        numAdd = dy
        numPoints = dx
    else:
        xInc2 = 0
        yInc1 = 0
        denominator = dy
        numerator = dy / 2
        numAdd = dx
        numPoints = dy
    
    for i in xrange(numPoints):
        result.append((x, y))
        numerator += numAdd
        if numerator >= denominator:
            numerator -= denominator
            x += xInc1
            y += yInc1
        x += xInc2
        y += yInc2
    # Add on the final point, which is otherwise omitted.
    result.append((x, y))
    return result


## Check if directionTwo is 90 degrees clockwise rotation from
#  directionOne.  /todo make this more general.
def isClockwise(directionOne, directionTwo):
    testDirection = tuple(directionOne)
    testDirection = changeCardinalDirection(testDirection, clockwise = 100)
    return testDirection == directionTwo
    
    
## These values are arrays of preferred directions for the
#  marching squares algorithm (see below)
#  The zero algorithm should never occur and should probably
#  return something for failure.  For debug purposes we'll
#  use it
marchingSquaresDirectionCounterClockwise = [
        (1, 0),    (1, 0),  (0, 1), (1, 0),
        (0, -1),  (0, -1),  (0, -1),  (0, -1),
        (-1, 0), (-1, 0), (0, 1), (1, 0), 
        (-1, 0), (-1, 0), (0, 1), (-1, 0)]
 
marchingSquaresDirectionClockwise = [
        (-1, 0), (0, 1), (-1, 0), (-1, 0),
        (1, 0),   (0, 1), (0, 1), (-1, 0),
        (0, -1),   (1, 0),  (0, -1),  (0, -1), 
        (1, 0),   (0, 1), (1, 0), (1, 0)]
        
marchingSquaresExitDirections = [
        set(), set(), set(), {(0, 1)},
        set(), {(1, 0)}, set(), {(1, 0), (0, 1)},
        set(), set(), {(-1, 0)},{(-1, 0), (0, 1)},
        {(0, -1)}, {(1, 0), (0, -1)}, {(-1, 0), (0, -1)},
        {(0, 1), (1, 0), (-1, 0), (0, -1)}]    
    
    
## Get the marching square suggested direction used for following around
#  obstacles of arbitrary shape.  (see algorithm at
#  http://en.wikipedia.org/w/index.php?title=Marching_squares&oldid=312115449
# 
#  The input is a 2 x 2 matrix with boolean values.  Squares are FALSE if they
#  are blocked off and TRUE if they are available to place a feature.
#  Grid ordering is as follows
# 8 4
# 2 1
#  The function returns a suggestedDirection to move the block and a possibly empty tuple
#  of exitDirections which can be used to break out of the contour following
#  loop.
def marchingSquare(booleanMatrix, clockwise = False):
    # First convert the array into an integer value
    key = 0
    if booleanMatrix[0][0]:
        key += 8
    if booleanMatrix[1][0]:
        key += 4
    if booleanMatrix[0][1]:
        key += 2
    if booleanMatrix[1][1]:
        key += 1
     
    if clockwise:
        suggestedDirection = marchingSquaresDirectionClockwise[key]
    else:
        suggestedDirection = marchingSquaresDirectionCounterClockwise[key]

    exitDirections = marchingSquaresExitDirections[key]
    
    if key == 0:
        # This should never occur, but for debugging reasons we'll 
        # allow it for now.
        print "Fully impenetrable array in marchingSquares"
        #raise RuntimeError("Full obstacle matrix passed")
    
    return suggestedDirection, exitDirections

    
## Reverse direction, works for arbitrary x, y direction, not
#  just cardinal ones
def reverseDirection(direction):
    if len(direction) != 2:
        raise RuntimeError("Directions must have two elements")
    return (direction[0] * -1, direction[1] * -1)


## Yield a sequence of adjacent values to the provided (x, y) coordinates.
# \param grid Optional parameter, a 2D Numpy array representing the grid
#        we're operating on. If provided, then coordinates that are out of 
#        bounds will be excluded. 
def getAdjacent(x, y, grid = None):
    for i in xrange(x - 1, x + 2):
        for j in xrange(y - 1, y + 2):
            if (grid is not None and 
                    (i < 0 or i >= grid.shape[0] or 
                        j < 0 or j >= grid.shape[1])):
                continue
            if (i, j) != (x, y):
                yield (i, j)


## Yield a grid-spiral pattern centered on the given (x, y) coordinates.
def generateSpiral(x, y):
    directions = [(0, -1), (-1, 0), (0, 1), (1, 0)]
    curDirectionIndex = 0
    curSpiralSize = 1
    lastX = x
    lastY = y
    while True:
        dx, dy = directions[curDirectionIndex % 4]
        for j in xrange(1, curSpiralSize + 1):
            yield (lastX + dx * j, lastY + dy * j)
        lastX += dx * curSpiralSize
        lastY += dy * curSpiralSize
        if curDirectionIndex % 2:
            curSpiralSize += 1
        curDirectionIndex += 1


## Yield a conic pattern starting at the given (x, y) coordinates, moving in 
# the specified direction (must be cardinal or 45-degree diagonal), ordered 
# like this:
#   7
#  25
# X149...
#  36
#   8
def generateCone(start, direction):
    start = numpy.array(start, dtype = numpy.int)
    direction = numpy.array(direction, dtype = numpy.int)
    perpendicular = numpy.array([-1 * direction[1], direction[0]], 
            dtype = numpy.int)
    axialDistance = 1
    while True:
        base = start + direction * axialDistance
        yield tuple(base)
        for offsetDistance in xrange(1, axialDistance + 1):
            yield tuple(base + perpendicular * offsetDistance)
            yield tuple(base - perpendicular * offsetDistance)
        axialDistance += 1


## Given a 2D array of numbers where 0 is "open" and any other values are
# "closed", as well as starting and ending positions (represented as 
# (x, y) tuples), return a list of (x, y) tuples representing the path from
# the starting position to the ending position, as generated by the A*
# search algorithm.
# Code based on the pseudocode at
# http://en.wikipedia.org/wiki/A*_search_algorithm
# By default, we use gridDistance as our heuristic cost function; however, 
# any heuristic can be supplied.
def aStarSearch(mapGrid, start, end, heuristic = gridDistance):
    closedNodes = set() # Nodes we have evaluated
    # Set of nodes we are currently considering navigating through.
    openNodes = set([start])
    # Maps nodes to the node we used to reach them, allowing us to retrace
    # our steps when we finish. 
    nodeToPredecessor = dict()
    
    # Maps node to cost to get from start to that node.
    nodeToKnownCost = dict()
    nodeToKnownCost[start] = 0
    # Maps node to the result of calling the heuristic. 
    nodeToHeuristicCache = dict()
    nodeToHeuristicCache[start] = heuristic(start, end)
    # This helper function will check the cache for the value of calling
    # heuristic(node, end), saving us on function calls (though the performance
    # gains when using the default heuristic are extremely minor, they could
    # be more significant for more costly heuristics).
    def heuristicWrap(node):
        if node in nodeToHeuristicCache:
            return nodeToHeuristicCache[node]
        val = heuristic(node, end)
        nodeToHeuristicCache[node] = val
        return val
    # Maps node to estimated cost (i.e. known cost + heuristic cost) to get 
    # from start to end by way of that node.
    nodeToEstimatedCost = dict()
    nodeToEstimatedCost[start] = nodeToKnownCost[start] + heuristicWrap(start)

    while openNodes:
        # Find the next node with the lowest cost.
        temp = sorted(openNodes, key = lambda n: heuristicWrap(n))
        curNode = temp[0]
        openNodes.remove(curNode)
        closedNodes.add(curNode)
        if curNode == end:
            # All done! Generate the path back from curNode to start.
            result = [curNode]
            while curNode is not start:
                curNode = nodeToPredecessor[curNode]
                result.append(curNode)
            # Currently result is from end-to-start, so reverse it. 
            result.reverse()
            return result
        for neighbor in getAdjacent(*curNode, grid = mapGrid):
            # Ensure that neighbor is a valid (i.e. open) cell.
            if mapGrid[neighbor[0]][neighbor[1]] != 0:
                continue
            # Add 1 for the distance between curNode and neighbor.
            neighborCost = nodeToKnownCost[curNode] + 1
            if (neighbor in closedNodes and 
                    neighborCost >= nodeToKnownCost[neighbor]):
                # There's a shorter way to get to neighbar than by going
                # through curNode.
                continue
            if (neighbor not in openNodes or 
                    neighborCost < nodeToKnownCost[neighbor]):
                # Found a shorter route to neighbor than what we had before.
                nodeToPredecessor[neighbor] = curNode
                nodeToKnownCost[neighbor] = neighborCost
                nodeToEstimatedCost[neighbor] = neighborCost + heuristicWrap(neighbor)
                openNodes.add(neighbor)
    # Failed to find a path; return an empty path.
    return []


