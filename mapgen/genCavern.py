## Functions for game-of-life style cavern generation, blatantly
#  stolen from d_m's implementation in V.
#
#  Caverns can take up a part of a level, and can, due to random
#  factors have very little empty space.  If this happens the
#  cavern is not rejected, but the area is open to other structures
#  since only the space occupied by the cavern floors is reserved.

import generationMap
import genUtility
import connection
import util.geometry

import random

## Create a cavern region in the dungeon.  
#  The code starts by finding a region
#  to place the cavern.  For now, we only we stick the cavern in a rectangular
#  bounding box, although the actual final structure is amorphous.
#  After a suitable location is found, a number of "seed" cells are cleared
#  The amount of cells is defined by the density, which right now is a random
#  value between hard-coded limits.  After the seed cells are there a simple
#  game of life is run where the areas are made into floors or walls depending
#  on the number of floors/walls surrounding them.
#
#  Once the cavern shape is complete, all the small regions less than 8 cells
#  are removed, and the rest are cleared.
#  
#  Then we place centers throughout the structure by first making
#  a mesh, and then adding the cavern square closest to that point as a center.
#  Finally, those centers are connected.
def createCavern(curMap, genMap, width = 100, height = 80, priority = 1):
    # The density in places
    density = random.randint(40, 50)
    # number of times to run cavern mutations
    mutations = 4
    # space between center points
    centerSpacing = 4
    
    # Find a place to stick the cavern
    xWest, yNorth = genUtility.findPlaceableRectangle(genMap, width, height, priority)
    
    if genMap.debug:
        print "Generating cavern at xWest, yNorth: ", xWest, yNorth
    
    # reset the area, erasing information of whatever was there, this region
    # will be blanked even if the cavern fails!
    for x in xrange(xWest + width - 1):
        for y in xrange(yNorth + height - 1):
            genMap.setGridInfo(x, y)
    # Inital seeding of room squares        
    initializeCavern(genMap, xWest, yNorth, width, height, density)
    # Mutate the cavern several times
    for i in xrange(mutations):
        mutateCavern(genMap, xWest, yNorth, width, height)
      
    colorMap = connection.getColorMapForArea(genMap, xWest, 
            yNorth, width, height)
    if genMap.debug:
        print "Pre-removal, ", len(colorMap), "regions"
    # remove all the small regions
    colorMap = removeSmallRegions(genMap, colorMap)
                
    # make sure we got something
    if not colorMap:
        if genMap.debug:
            print "Cavern failure due to no points"
        return
    
    if genMap.debug:
        print len(colorMap), "regions detected"
    # make a set of all points in the cavern
    cavernPoints = set()
    for region in colorMap:
        cavernPoints.update(region)
    # set information for all the cavern locations
    for location in cavernPoints:
        genMap.setPriority(location[0], location[1], priority)
        genUtility.clearCell(curMap, location[0], location[1])
    
    # Make a mesh of points
    centerMesh = util.geometry.getMesh(xWest, yNorth, width, height, centerSpacing)
    # find centers near the mesh
    cavernCenters = getCavernCenters(genMap, xWest, yNorth, width, height, 
            cavernPoints, centerMesh)
    # add the centers to the genMap 
    genMap.addSeveralCenters(cavernCenters)
        
    # Connect all the centers, using background noise
    connection.connectRooms(curMap, genMap, tunnelStyle= 'AStar', 
            unconnectedLocations = cavernCenters)
    
        
## Seed the cavern with room squares.  We set at most density% cells as rooms, by
#  setting (density / 100) * area random cells as rooms   
def initializeCavern(genMap, xWest, yNorth, width, height, density):
    area = width * height
    
    # number of squares to initially set as rooms
    clearSquares = area * density / 100
    
    for i in xrange(clearSquares):
        x = random.randint(xWest, xWest + width - 1)
        y = random.randint(yNorth, yNorth + height - 1)
        genMap.setRoom(x, y, True)
        
        
## Run the game of life rules (3, 4)  If 0, 1, or 2 surrounding
#  squares are floors, the next iteration will have a wall there.
#  If 5, 6, 7, or 8 squares are floors, the next iteration will
#  have a floor.  If 3 or 4 squares are floors, the next iteration
#  will retain whatever state it had.
def mutateCavern(genMap, xWest, yNorth, width, height):
    # make a new grid for the next evolution
    tempGrid = [[False for j in xrange(height)] for i in xrange(width)]
    
    for x in xrange(xWest, xWest + width - 1):
        for y in xrange(yNorth, yNorth + height - 1):
            adjacentRooms = genMap.getNumAdjacentRooms(x, y)
            if adjacentRooms < 3:
                tempGrid[x - xWest][y - yNorth] = False
            elif adjacentRooms > 4:
                tempGrid[x - xWest][y - yNorth] = True
            else:
                tempGrid[x - xWest][y - yNorth] = genMap.isRoom(x, y)
                
    # Update genMap            
    for x in xrange(xWest, xWest + width - 1):
        for y in xrange(yNorth, yNorth + height - 1):
            genMap.setRoom(x, y, tempGrid[x - xWest][y - yNorth])


## Remove all the small regions that aren't large enough
#  to consider as part of the cavern
def removeSmallRegions(genMap, colorMap, minimumSize = 8):
    regionNumber = 0
    
    while regionNumber < len(colorMap):
        if len(colorMap[regionNumber]) >= minimumSize:
            regionNumber += 1
            continue
        # pull out the region
        region = colorMap.pop(regionNumber)
        # remove the room settings
        for location in list(region):
            genMap.setRoom(location[0], location[1], False)
    return colorMap
    
            
## Find center points for the cavern.  This function scans through a 
#  list of points and returns the cavern square nearest to each point.
def getCavernCenters(genMap, xWest, yNorth, width, height, cavernPoints, centerMesh):

    cavernCenters = set()
    # Start scanning through the mesh
    for location in centerMesh:
        # add the closest point to the set of centers
        cavernCenters.add(util.geometry.getNearbyLocation(cavernPoints, location))

    return cavernCenters