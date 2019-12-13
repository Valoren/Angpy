## This module handles regenerating the map of the game world. 
# In fact, much
# of the "map" is preserved whenever a new level is generated -- anything that
# persists will stick around, including e.g. the player, all their items, and
# anything that exists in the GameMap but does not really exist in "reality"
# (e.g. the "object" that handles refreshing the stores every so often).

import container
import connection
import gameMap
import generationMap
import genCavern
import genUtility
import things.terrain.terrainLoader
import things.creatures.player
import things.creatures.creatureLoader
import things.creatures.creatureAllocator
import things.items.itemLoader
import things.items.itemAllocator
import util.geometry

import copy
import random
 

## Make a debug vault for testing purposes
def makeDebugVault(curMap, genMap, priority = 7):
    width = 50
    height = 40
    #x = random.randint(1, curMap.width - width - 1)
    #y = random.randint(1, curMap.height - height - 1)
    x = 100
    y = 50
    genUtility.makeRectangleHollow(curMap, genMap, x, y, width, height,
            'permanent wall', priority = priority, cost = 10**4)
    genUtility.makeRectangleFilled(curMap, genMap, x + 1, y + 1,
            width - 2, height - 2, None, priority = priority, isRoom = False, cost = 0)
    # /todo there is still difficulty dealing with connecting up obstacle rooms        
    # set a single pierceable square on the western wall
    # This doesn't seem to be working for now, so don't even allow
    # the normal connection to get in here
    #genMap.setPierceable(x, y + (height / 2), True)
    genMap.setCost(x, y + (height / 2), 0)
    # force the vault to connect up
    genMap.addCenter(x + 1, y + (height / 2))
    genMap.addVaultCenter(x + 1, y + (height / 2))
    
    
## Make a rectangular room at a possible random location with a 
#  possible random size
#
#  Arguably this is general enough that it should go in genUtility.
#
#  /todo properly handle overwriting old areas for connection purposes
def makeRoom(curMap, genMap, priority, width = None, height = None, xWest = None, 
        yNorth = None, forcedLocation = False):

    # Get a random width and height, unless specified
    if width is None:
        width = random.randint(8, 14)
    if height is None:
        height = random.randint(8, 14)
            
    xWest, yNorth = genUtility.findPlaceableRectangle(genMap, width, height, 
            priority, xWest = xWest, yNorth = yNorth) 
    
    # Make sure we got a valid placement
    if xWest is None:
        return
    # Remove any centers in the region in case we're overwriting
    genUtility.removeCentersInRectangle(genMap, xWest, yNorth, width, height)
    
    # Set the middle square of the room as the center
    genMap.addCenter(xWest + width / 2, yNorth + height / 2)
        
    # Make the walls outside
    genUtility.makeRectangleHollow(curMap, genMap, xWest, yNorth, width, height, 
        'granite wall', priority = priority, isPierceable = True)
        
    # Clear the floor
    genUtility.makeRectangleFilled(curMap, genMap, xWest + 1, yNorth + 1, 
        width - 2, height - 2, None, priority = priority, isRoom = True, cost = 0)


## Place a terrain of a given type in a room
def placeTerrainInRoom(curMap, genMap, feature, targetLevel, priority = 0):
    x, y = genMap.getRandom(isRoom = True)
        
    things.terrain.terrainLoader.makeTerrain(feature, curMap, 
        (x, y), targetLevel)
    genMap.setGridInfo(x, y, priority = priority)
        
    
## Make a "standard" dungeon map.
def makeAngbandLevel(curMap, targetLevel, width, height):

    # Make a new generation map
    genMap = generationMap.GenerationMap(width, height)
    # Make the surrounding wall
    genUtility.makeRectangleHollow(curMap, genMap, 0, 0, 
        width - 1, height - 1, 'permanent wall', priority = 10, cost = 10**10)
    # Fill the entire map with walls
    genUtility.makeRectangleFilled(curMap, genMap, 1, 1,
        width - 3, height - 3, 'granite wall')

    ## At this point we load the rules that define what features to place
    #  in this archetype.  For the meantime we'll just make some rooms 
    #  and corridors.
    
    # debug vault for testing pathing
    if targetLevel % 12 == 0:
        makeDebugVault(curMap, genMap)
   
    # debug, make a cavern
    if targetLevel % 5 == 0:
        genCavern.createCavern(curMap, genMap)
    
    # Make some rooms of priority 2
    for room in xrange(15):
        makeRoom(curMap, genMap, 2)
    
    # This is the old connection algorithm, likely to be removed.
    # Room connection, first try normal V style
    #if not connection.connectRooms(curMap, genMap) or genMap.vaultCenters:
        # Either we failed or there's some complicated geometry
        # to hook up, use A* connection
    #    connection.connectRooms(curMap, genMap, tunnelStyle = 'AStar', noise = 'random')
    
    # Connect the rooms using A* algorithm with block-type noise
    connection.connectRooms(curMap, genMap, tunnelStyle = 'AStar', noise = 'block')
    
    # debug info
    if genMap.debug:
        print "Number of junctions:", len(genMap.junctions)

    # Put some stairs into some of the rooms.
    for i in xrange(random.randint(2, 4)):
        placeTerrainInRoom(curMap, genMap, 'down staircase', targetLevel, priority = 8)
    for i in xrange(random.randint(1, 3)):
        placeTerrainInRoom(curMap, genMap, 'up staircase', targetLevel, priority = 8)
            
    # Put the player in somewhere.
    player = curMap.getContainer(container.PLAYERS)[0]
    player.pos = genMap.getRandomCenter()
    if genMap.debug:
        print "player.pos",player.pos
    curMap.addSubscriber(player, player.pos)
    
    # Scatter some items about.
    i = 0
    numTries = 0
    itemAllocator = things.items.itemAllocator.ItemAllocator(targetLevel)
    while i < 50 and numTries < 1000:
        cell = genUtility.randomCell(curMap, width, height)
        if not cell:
            itemAllocator.allocate(curMap, cell)
            i += 1
        numTries += 1

    ## Scatter some creatures about.
    i = 0
    numTries = 0
    creatureAllocator = things.creatures.creatureAllocator.CreatureAllocator(targetLevel)
    while i < 10 and numTries < 200:
        cell = genUtility.randomCell(curMap, width, height)
        if not cell:
            creatureAllocator.allocate(curMap, cell.pos)
            i += 1
        numTries += 1




