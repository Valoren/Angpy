## This module includes all the basic functions for dungeon generation
# including basic terrain handling, room formation, and interfacing
# with the generationMap

# Please keep all functions in alphabetical order

import container
import gameMap
import generationMap
import things.terrain.terrainLoader
import things.creatures.player
import things.creatures.creatureLoader
import things.creatures.creatureAllocator
import things.items.itemLoader
import things.items.itemAllocator
import util.geometry

import random


## Destroy all terrain in the specified cell. Except that we treat differently
# anything whose "pos" field is None, since that indicates that the Thing in
# question is an alias of a Thing, not a real one (for performance purposes). 
# So we remove the alias instead of destroying the Thing.
def clearCell(curMap, x, y):
    things = curMap.getContainer((x, y), container.TERRAIN)
    for thing in list(things):
        if thing.pos is None:
            curMap.removeSubscriber(thing, (x, y))
        else:
            curMap.destroy(thing)
            

## Finds a location for a rectangular region.  Returns the NW corner
#  for the region.  
#  \param xWest and yNorthm will be randomized if not set.  Allowing setting
#  of only one allows the user to specify a feature at a specific latitude or
#  longitude, such as an "entry level" room and an "exit level" room on opposite
#  sides of the map.
#  If it fails to find a region after enough random tries, or if
#  both xWest and yNorth or set and it fails, the code will return
#  None for the room location.  (Do you have a better idea for how
#  to handle this Derakon?)
def findPlaceableRectangle(genMap, width, height, priority, xWest = None, yNorth = None):
    # Handle forced location
    if xWest is not None and yNorth is not None:
        if isRectanglePlaceable(genMap, xWest, yNorth, width, height, priority):
            # The rectangle is free
            return xWest, yNorth
        else:
            # The rectangle does not fit, the feature cannot be placed
            return None

    # Maximum number of tries
    maxTries = 10

    # Make several attempts to place the rectangle
    for tries in xrange(maxTries):
        # Choose an x location, or use the set one
        curX = xWest
        if curX is None:
            curX = random.randint(1, genMap.width - width - 1)
        # Choose a y location, or use the set one
        curY = yNorth
        if curY is None:
            curY = random.randint(1, genMap.height - height - 1)
        # Does our location fit?
        if isRectanglePlaceable(genMap, curX, curY, width, height, priority):
            # Yes, return it
            return curX, curY
            
    # Did not find a placeable rectangle, the feature cannot be placed
    return None

    
## See if a rectangle is placeable in the grid
def isRectanglePlaceable(genMap, xWest, yNorth, width, height, priority):
    # If this is slow we can speed it up by not checking every cell
    for x in xrange(xWest, xWest + width):
        for y in xrange(yNorth, yNorth + height):
            if genMap.grid[x][y].priority >= priority: 
                return False
    return True
    

## Create a rectangle of the designated terrain type.
# This can be used for the surrounding walls of rooms
# or for the border of permanent walls around a level
#
# \todo allow the option to avoid setting the corners, this will prevent
# rooms from connecting through the corner cell.
def makeRectangleHollow(curMap, genMap, xWest, yNorth, 
        width, height, terrainType, priority = 0, isPierceable = False,
        isRoom = False, doErasePrevious = True, cost = 10):
    # Maybe a paranoia bounds check?
    
    # Load up the terrain
    if terrainType is not None:
        terrainFactory = things.terrain.terrainLoader.getTerrainFactory(terrainType)
        terrain = terrainFactory.makeTerrain(curMap, None, 0)
    
    # Some helpful definitions
    xEast = xWest + width - 1
    ySouth = yNorth + height - 1
    
    # Debugging statements
    #print "Hollow Rectangle", terrainType
    #print "xWest, xEast", xWest, xEast + 1
    #print "yUp, YDown", yNorth, ySouth + 1
    
    # Make the top and bottom rows
    for x in xrange(xWest, xEast + 1):
        if terrainType is None:
            clearCell(curMap, x, yNorth)
            clearCell(curMap, x, ySouth)
        else:
            # Granite walls + permanent walls were being displayed as granite walls
            # Is this a bug?  For now we're going to clear cells when placing
            # terrain with a keyword.
            if doErasePrevious:
                clearCell(curMap, x, yNorth)
                clearCell(curMap, x, ySouth)
            curMap.addSubscriber(terrain, (x, yNorth))
            curMap.addSubscriber(terrain, (x, ySouth))
        
        genMap.setGridInfo(x, yNorth, priority = priority, 
                isPierceable = isPierceable, isRoom = isRoom, cost = cost)
        genMap.setGridInfo(x, ySouth, priority = priority,  
                isPierceable = isPierceable, isRoom = isRoom, cost = cost) 

    
    # Make the West and East columns
    for y in xrange(yNorth + 1, ySouth):
        if terrainType is None:
            clearCell(curMap, xWest, y)
            clearCell(curMap, xEast, y)
        else:
            if doErasePrevious:
                clearCell(curMap, xWest, y)
                clearCell(curMap, xEast, y)
            curMap.addSubscriber(terrain, (xWest, y))
            curMap.addSubscriber(terrain, (xEast, y))            

        genMap.setGridInfo(xWest, y, priority = priority, 
                isPierceable = isPierceable, isRoom = isRoom, cost = cost)
        genMap.setGridInfo(xEast, y, priority = priority, 
                isPierceable = isPierceable, isRoom = isRoom, cost = cost)
        
        
## Create a filled rectangle of the designated terrain type.
#  /todo get default cost from somewhere else.                
def makeRectangleFilled(curMap, genMap, xWest, yNorth,
        width, height, terrainType, priority = 0, isRoom = False,
        doErasePrevious = True, cost = 10):
    # Probably should put a bounds check here
    
    # Debugging statements
    #print "FilledRectangle", terrainType
    #print "xWest, xEast", xWest, xWest + width - 1
    #print "yUp, yDown", yNorth, yNorth + height - 1
    
    # Load up the terrain
    if terrainType is not None:
        terrainFactory = things.terrain.terrainLoader.getTerrainFactory(terrainType)
        terrain = terrainFactory.makeTerrain(curMap, None, 0)
        
    for x in xrange(xWest, xWest + width):
        for y in xrange(yNorth, yNorth + height):
            if terrainType is None:
                clearCell(curMap, x, y)
            else:
                # see note in makeRectangleHollow
                if doErasePrevious:
                    clearCell(curMap, x, y)
                curMap.addSubscriber(terrain, (x, y))
            
            genMap.setGridInfo(x, y, priority = priority, isRoom = isRoom, cost = cost)
        
        
## Return a random cell in the range ([1, width - 2], [1, height - 2])
def randomCell(curMap, width, height):
    x = random.randint(1, width - 2)
    y = random.randint(1, height - 2)
    return curMap.getContainer((x, y))
    

## Remove all centers in a given rectangle.  Used when a region is
#  partially overwritten    
def removeCentersInRectangle(genMap, xWest, yNorth, width, height):
    for center in list(genMap.centers):
        if (center[0] >= xWest and center[0] < xWest + width and
                center[1] >= yNorth and center[1] <= yNorth + height):
            genMap.removeCenter(center[0], center[1])
    
    
## Given a partially filled in connection map and a starting point
#  find if all points are connected.  This is a binary check
#  we may want to write a general one to calculate arbitrary transit 
#  times to given locations for monster pathing and sound traveling
#  in the future.
#
#  The basic idea is to start with a list of "old" points and then check to 
#  see if any points are valid and unconnected.  If they are add
#  them to a set of "new" points.  At the beginning of each iteration
#  the new points from the last run become the old points of the current
#  one   
def updateConnectionMap(genMap, connectionMap, start):
    # Make an empty set to chart all the new points and 
    new = set()
    # The starting point is automatically connected
    new.add(start)
    connectionMap[start[0]][start[1]] = True

    while(new):
        old = new.copy()
        new.clear()
        # iterate over cells
        for cell in list(old):
            # iterate over all adjacent cells including diagonals
            for x in xrange(cell[0] - 1, cell[0] + 2):
                for y in xrange(cell[1] - 1, cell[1] + 2):
                    # Bounds check
                    if not genMap.isInBounds(x, y): 
                        continue
                    # Add it if it's addable and hasn't been seen yet
                    if (not connectionMap[x][y]) and (genMap.isRoom(x, y) or genMap.isTunnel(x, y)):
                        connectionMap[x][y] = True
                        new.add((x, y))

    return connectionMap
    

## Look through all the connected rooms and remove those that are connected    
def updateUnconnectedRooms(unconnectedRooms, connectionMap):
    for room in list(unconnectedRooms):
        if connectionMap[room[0]][room[1]]:
            unconnectedRooms.remove(room)
            
    return unconnectedRooms        