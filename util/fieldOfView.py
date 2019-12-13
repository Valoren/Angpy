#
#    Author:         Aaron MacDonald
#    Date:           June 14, 2007
#
#    Description:    An implementation of the precise permissive field
#                    of view algorithm for use in tile-based games.
#                    Based on the algorithm presented at
# http://roguebasin.roguelikedevelopment.org/index.php?title=Precise_Permissive_Field_of_View.
#
#    You are free to use or modify this code as long as this notice is
#    included.
#    This code is released without warranty.
#
# As adapted by d_m, and then further modified for Pyrel. 

import copy



## Simple container class to represent a "bump" (i.e. obstruction) in a view.
class ViewBump:
    def __init__(self, x, y, parent):
        self.x = x
        self.y = y
        self.parent = parent



## Simple container class to represent a given field of view constrained by
# two lines.
class View:
    def __init__(self, shallowLine, steepLine, shallowBump = None, 
            steepBump = None):
        self.shallowLine = shallowLine
        self.steepLine = steepLine
        self.shallowBump = shallowBump
        self.steepBump = steepBump



## Determines which coordinates on a 2D grid are visible from a particular
# coordinate.
# 
# \param mapGrid Numpy array representing map visibility: 0 is clear, anything
#        else is obstructed.
# \param start (x, y) tuple representing the center of view.
# \param radius How far the field of view may extend along the X or Y axes.
# \param visibleFunc Function to call when a tile is visible. Accepts 
#        (x, y) as parameters (two distinct params, not a tuple).
def setFieldOfView(mapGrid, start, radius, visibleFunc):
    startX, startY = start
    # Tiles that have been visited already
    visited = set()

    # The center is always visible.
    visibleFunc(startX, startY)
    visited.add((startX, startY))

    # Get the dimensions of the actual field of view, making sure not to 
    # go off the map or beyond the radius.
    minExtentX = min(startX, radius)
    maxExtentX = min(mapGrid.shape[0] - startX - 1, radius)
    minExtentY = min(startY, radius)
    maxExtentY = min(mapGrid.shape[1] - startY - 1, radius)

    # Northeast quadrant
    checkQuadrant(visited, mapGrid, startX, startY, 1, 1, 
            maxExtentX, maxExtentY, visibleFunc)

    # Southeast quadrant
    checkQuadrant(visited, mapGrid, startX, startY, 1, -1, 
            maxExtentX, minExtentY, visibleFunc)

    # Southwest quadrant
    checkQuadrant(visited, mapGrid, startX, startY, -1, -1, 
            minExtentX, minExtentY, visibleFunc)

    # Northwest quadrant
    checkQuadrant(visited, mapGrid, startX, startY, -1, 1, 
            minExtentX, maxExtentY, visibleFunc)



class Line(object):
     def __init__(self, startX, startY, endX, endY):
         self.startX = startX
         self.startY = startY
         self.endX = endX
         self.endY = endY

     dx = property(fget = lambda self: self.endX - self.startX)
     dy = property(fget = lambda self: self.endY - self.startY)


     def isPointBelow(self, x, y):
         return self.getRelativeSlope(x, y) > 0


     def isPointBelowOrCollinear(self, x, y):
         return self.getRelativeSlope(x, y) >= 0


     def isPointAbove(self, x, y):
         return self.getRelativeSlope(x, y) < 0


     def isPointAboveOrCollinear(self, x, y):
         return self.getRelativeSlope(x, y) <= 0


     def isPointCollinear(self, x, y):
         return self.getRelativeSlope(x, y) == 0


     def isLineCollinear(self, line):
         return self.isPointCollinear(line.startX, line.startY) and self.isPointCollinear(line.endX, line.endY)


     def getRelativeSlope(self, x, y):
         return (self.dy * (self.endX - x)) - (self.dx * (self.endY - y))


def checkQuadrant(visited, mapGrid, startX, startY, dx, dy, 
        extentX, extentY, visibleFunc):
    active = []

    shallowLine = Line(0, 1, extentX, 0)
    steepLine = Line(1, 0, 0, extentY)

    active.append(View(shallowLine, steepLine, None, None))
    viewIndex = 0

    # Visit the tiles diagonally and going outwards
    #
    # .
    # .
    # .           .
    # 9        .
    # 5  8  .
    # 2  4  7
    # @  1  3  6  .  .  .
    maxI = extentX + extentY
    i = 1
    while i != maxI + 1 and len(active) > 0:
        startJ = max(0, i - extentX)
        maxJ = min(i, extentY)

        j = startJ
        while j != maxJ + 1 and viewIndex < len(active):
            x = i - j
            y = j
            visitCoord(visited, mapGrid, startX, startY, x, y, dx, dy, 
                    viewIndex, active, visibleFunc)
            j += 1

        i += 1

def visitCoord(visited, mapGrid, startX, startY, x, y, dx, dy, 
        viewIndex, active, visibleFunc):
    # The top left and bottom right corners of the current coordinate.
    tl = (x, y + 1)
    br = (x + 1, y)

    while viewIndex < len(active) and active[viewIndex].steepLine.isPointBelowOrCollinear(br[0], br[1]):
        # The current coordinate is above the current view and is
        # ignored.  The steeper fields may need it though.
        viewIndex += 1

    if viewIndex == len(active) or active[viewIndex].shallowLine.isPointAboveOrCollinear(tl[0], tl[1]):
        # Either the current coordinate is above all of the fields
        # or it is below all of the fields.
        return

    # It is now known that the current coordinate is between the steep
    # and shallow lines of the current view.

    isBlocked = False

    # The real quadrant coordinates
    realX = (x * dx)
    realY = (y * dy)

    if (startX + realX, startY + realY) not in visited:
        visited.add((startX + realX, startY + realY))
        visibleFunc(startX + realX, startY + realY)

    isBlocked = bool(mapGrid[startX + realX, startY + realY])

    if not isBlocked:
        # The current coordinate does not block sight and therefore
        # has no effect on the view.
        return

    if active[viewIndex].shallowLine.isPointAbove(br[0], br[1]) and active[viewIndex].steepLine.isPointBelow(tl[0], tl[1]):
        # The current coordinate is intersected by both lines in the
        # current view.  The view is completely blocked.
        del active[viewIndex]
    elif active[viewIndex].shallowLine.isPointAbove(br[0], br[1]):
        # The current coordinate is intersected by the shallow line of
        # the current view.  The shallow line needs to be raised.
        addShallowBump(tl[0], tl[1], active, viewIndex)
        checkView(active, viewIndex)
    elif active[viewIndex].steepLine.isPointBelow(tl[0], tl[1]):
        # The current coordinate is intersected by the steep line of
        # the current view.  The steep line needs to be lowered.
        addSteepBump(br[0], br[1], active, viewIndex)
        checkView(active, viewIndex)
    else:
        # The current coordinate is completely between the two lines
        # of the current view.  Split the current view into two views
        # above and below the current coordinate.

        shallowViewIndex = viewIndex
        viewIndex += 1
        steepViewIndex = viewIndex

        active.insert(shallowViewIndex, copy.deepcopy(active[shallowViewIndex]))

        addSteepBump(br[0], br[1], active, shallowViewIndex)
        if not checkView(active, shallowViewIndex):
            viewIndex -= 1
            steepViewIndex -= 1

        addShallowBump(tl[0], tl[1], active, steepViewIndex)
        checkView(active, steepViewIndex)

def addShallowBump(x, y, active, viewIndex):
    active[viewIndex].shallowLine.endX = x
    active[viewIndex].shallowLine.endY = y

    active[viewIndex].shallowBump = ViewBump(x, y, active[viewIndex].shallowBump)

    curBump = active[viewIndex].steepBump
    while curBump is not None:
        if active[viewIndex].shallowLine.isPointAbove(curBump.x, curBump.y):
            active[viewIndex].shallowLine.startX = curBump.x
            active[viewIndex].shallowLine.startY = curBump.y

        curBump = curBump.parent

def addSteepBump(x, y, active, viewIndex):
    active[viewIndex].steepLine.endX = x
    active[viewIndex].steepLine.endY = y

    active[viewIndex].steepBump = ViewBump(x, y, active[viewIndex].steepBump)

    curBump = active[viewIndex].shallowBump
    while curBump is not None:
        if active[viewIndex].steepLine.isPointBelow(curBump.x, curBump.y):
            active[viewIndex].steepLine.startX = curBump.x
            active[viewIndex].steepLine.startY = curBump.y

        curBump = curBump.parent

def checkView(active, viewIndex):
    """
        Removes the view in active at index viewIndex if
            - The two lines are coolinear
            - The lines pass through either extremity
    """

    shallowLine = active[viewIndex].shallowLine
    steepLine = active[viewIndex].steepLine

    if shallowLine.isLineCollinear(steepLine) and (shallowLine.isPointCollinear(0, 1) or
                                                 shallowLine.isPointCollinear(1, 0)):
        del active[viewIndex]
        return False
    else:
        return True

if __name__ == "__main__":
    import numpy
    width = 40
    height = 20
    mapGrid = numpy.zeros((width, height))
    mapGrid[10,11] = 1
    mapGrid[11,11] = 1
    mapGrid[9,9] = 1
    mapGrid[12,9] = 1
    radius = 40
    start = (10, 10)

    visible = [False] * height * width

    def visit_tile(x, y): visible[x * height + y] = True
    def isvisible(x, y): return visible[x * height + y]

    print 'running fov'
    setFieldOfView(mapGrid, start, radius, visit_tile)
    print 'done'

    import sys
    for y in range(0, height):
        sys.stdout.write('|')
        for x in range(0, width):
            b = bool(mapGrid[x, y])
            v = isvisible(x, y)
            if (x, y) == start:
                sys.stdout.write('@')
            elif v and b:
                sys.stdout.write('#')
            elif b:
                sys.stdout.write('x')
            elif v:
                sys.stdout.write('.')
            else:
                sys.stdout.write('o')
        sys.stdout.write('|\n')
