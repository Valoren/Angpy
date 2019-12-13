import numpy



## An AccessibilityMap is a 2D array of values that indicates how obstructed
# a given cell in the map is. 
# This is useful for e.g. pathfinding -- every creature that shares a given
# mode of transportation can use the same AccessibilityMap for plotting their
# routes.
class AccessibilityMap:
    ## \param gameMap The GameMap instance that we will be mapping.
    # \param filterFunc Function that accepts a Cell and the GameMap as 
    #        parameters, and returns a float indicating the degree to which
    #        the Cell is obstructed.
    def __init__(self, gameMap, filterFunc):
        self.gameMap = gameMap
        self.filterFunc = filterFunc
        ## These cells have been modified since we were last asked for 
        # our map.
        self.dirtyCells = set()
        # This will add every tile (that has anything in it) to self.dirtyCells.
        self.gameMap.addUpdateCellFunc(self.updateCell)
        ## The current state of the map. Note we use floating point values here
        # because we may want partial obstruction (e.g. for LOS, fog is not
        # entirely opaque, but also not entirely transparent). 
        self.map = numpy.zeros(gameMap.getDimensions(), dtype = numpy.float32)


    ## A cell's contents have changed, so it is now dirty.
    def updateCell(self, cell, newThing, wasAdded):
        self.dirtyCells.add(cell)


    ## Get the current map; at this time, we evaluate all of our dirty cells.
    def getMap(self):
        for cell in self.dirtyCells:
            self.map[cell.pos[0], cell.pos[1]] = self.filterFunc(cell, self.gameMap)
        self.dirtyCells = set()
        return self.map

