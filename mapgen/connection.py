## This module handles connecting the dungeon.  There are currently
#  two possible methods.  One is the old style Angband tunnel generation
#  that starts at a place and makes a meandering tunnel towards a 
#  target.  This method has difficulties avoiding complicated obstacles
#  and may fail.
#  
#  The second is the A* connection algorithm which is an efficiency
#  improvement over the Dijkstra algorithm for finding a short path
#  between an origin and a target, given an array of costs for each
#  grid.  A* has no problem with obstacles but is marginally slower
#  and doesn't make angband style tunnels.  

import generationMap
import genUtility
import util.geometry

import heapq
import random
        
        
## This is the main conection algorithm for the Angband dungeon.
#
#  It starts by obtaining a list of places that need to be connected to each other.
#  Then it creates a "color" map which is a list of sets where each set contains
#  points that are already connected.  For rectangular rooms without tunnels, these
#  sets would have all the points in the room.  Each disjoint region is in a
#  separate set in the list.  
#   
#  The algorithm chooses two disjoint sets randomly and then chooses points in the sets
#  that are reasonably close to each other.  Then it obtains the points for a tunnel with 
#  the style chosen with param tunnelStyle.  If the tunnel is successful, we then construct 
#  the tunnel.  A tunnel can fail if it ends on a value that is not in the colorMap, or
#  if it's an empty list.  If the tunnel making failed, the loops restarts and two
#  new points are chosen.  Note, a tunnel does not need to intersect the correct target
#  to be successful, it only needs to end in a region that's disjoint from the starting
#  region.
#
#  After tunnel construction the colorMap is modified so that the two regions that have
#  been connected are in a single set.  The points in the tunnel are also added.  The 
#  result of this is that the total number of disjoint regions is reduced by one.   
#  The loop finishes when there is only one set in the colorMap list, or the maximum 
#  number of tunnel attempts has been reached.
#
#  \param tunnelStyle has two options currently.  'Angband' style, which makes tunnels
#  similar to those currently in V.  And 'AStar' which uses the A* connection algorithm.
#  Note that currently 'Angband' style does not attempt to connect special rooms like
#  vaults.
#  \param noise also has two options.  'random' adds a random cost to each square, this 
#  yields passages with many turns but not many detours.  'block' noise yields angband
#  style dungeons with many straight passages.    
def connectRooms(curMap, genMap, tunnelStyle = 'AStar', noise = None,
        unconnectedLocations = None):
    
    # Make a set of unconnected places or use the one passed to us
    if unconnectedLocations is None:
        unconnectedLocations = genMap.centers.copy()
    # 'angband' style connection does not connect up vaults
    if tunnelStyle == 'Angband':
        unconnectedLocations = unconnectedLocations.difference(genMap.vaultCenters)
    if genMap.debug:
        print "Initializing color map."
    # Get the list of what is connected to what.
    # /todo refactor the colorMap out.
    colorMap, preconnectedLocations = getColorMap(genMap, unconnectedLocations)
    # Subtract the locations that were already connected from the set
    # of unconnectedLocations.
    unconnectedLocations = unconnectedLocations.difference(preconnectedLocations)
    if genMap.debug:
        print len(colorMap)," regions detected."
    
    # There's a chance we're already all connected
    if len(colorMap) < 2:
        return
    
    # Add random noise to cost for AStar
    # This probably should be done on initialization, especially
    # if this becomes the main connection routine
    if noise:
        if genMap.debug:
            print "Adding noise."
        if noise == 'random':        
            addCostNoise(genMap, noiseType = 'random')
        if noise == 'block':
            addCostNoise(genMap, noiseType = 'block')
    
    tries = 1
    
    # As long as there are at least 2 regions, connect them together
    while len(colorMap) > 1 and tries < 100:
        tries += 1
        # get two different indices into colorMap
        startIndex, targetIndex = random.sample(range(len(colorMap)), 2)
        # Find two nearby points to start from
        startPoint, endPoint = util.geometry.getClosestPoints(
                colorMap[startIndex], colorMap[targetIndex])
        
        if tunnelStyle == 'AStar':
            tunnelPath = getAStarTunnel(genMap, colorMap, startPoint, 
                    endPoint, startIndex)
        elif tunnelStyle == 'Angband':
            tunnelPath = getAngbandTunnel(genMap, colorMap, startPoint,
                    endPoint, startIndex)
        else:
            print "unknown style: ", style
            return
        
        # if we got a tunnel add it on.
        if tunnelPath:
            if genMap.debug:
                print "Making tunnel between ", tunnelPath[-1], " and ", tunnelPath[0]
                print "Tunnel length: ", len(tunnelPath)
            constructTunnelFromPath(curMap, genMap, tunnelPath)

            updateColorMap(colorMap, tunnelPath)

    if len(colorMap) > 1:
        # failure :(
        if genMap.debug:
            print "connection failed"
        return False
    else:
        # success!
        return True
            

## Make an angband style tunnel in the direction of the target.  Angband style tunnels
#  are wandering tunnels that go roughly in the direction of the target and stop when
#  they hit a pierceable cell, even one from the room they started in.  There are
#  two kind of tunnels used here, the normal kind for tunneling through free rock,
#  getTunnel and the obstacle avoidance kind that traces around an obstacle,
#  tunnelAroundObstacle.  getTunnel is called first and if it ends on something
#  that is not a room, tunnelAroundObstacle is called.  tunnelAroundObstacle
#  ends when it can freely head off to the target and getTunnel is then called to 
#  continue the tunnel.
#
#  If the tunnel ends on a pierceable cell the loops completes and the tunnel, a list
#  of points with all the tunnel squares from start to finish, is returned.                 
def getAngbandTunnel(genMap, colorMap, start, target, startIndex,
        priority = 1):
    tunnel = [start]
    complete = False
    tries = 0
    # Loop ends if the tunnel ends on a room or we've encountered 10 or more
    # obstacles along the way.
    while not complete and tries < 10:
        tries += 1
        newTunnel = getFreeTunnel(genMap, start, target)
        # Handle receiving a low tunnel (i.e. failure)
        if len(newTunnel) < 2:
            return[]
        tunnel += newTunnel
        # check if we ended up in a room
        endPoint = tunnel[-1]
        if genMap.isRoom(endPoint[0], endPoint[1]):
            # new region?
            if getColorFor(colorMap, endPoint) != startIndex:
                # success!
                return tunnel
            else:
                # failure, the tunnel intersected itself
                return []
        # Did we hit a boundary somehow
        if genMap.isBoundary(endPoint[0], endPoint[1]):
            # failure
            return []
        # This option shouldn't be possible, here for debugging
        if genMap.isHigherPriority(endPoint[0], endPoint[1], 
                priority):
            if genMap.debug:
                print "Unexplained tunnel end:"
                print endPoint
            return []
        # A higher priority cell is an obstacle 
        else:
            # Store the length to compare afterwards
            prevLength = len(tunnel) - 1
            tunnel = tunnelAroundObstacle(genMap, tunnel, target)
            # did we get anything new besides just removing the first
            # location?
            if len(tunnel) == prevLength:
                # failure
                if genMap.debug:
                    print "failed tunnel"
                return []
            # update the start    
            else: 
                start = tunnel[-1]
                
                
## This is a free tunnel used to navigate through the background dungeon.
#  It terminates when it encounters an obstacle or a pierceable wall.  
#
#  \param turnPct is the percentage chance that a tunnel turns at a given square.
#  \param randDirectionPct is the percentage chance that a turn goes off in a random
#  direction.  Otherwise the turn is so that the tunnel heads in the proper direction.
#  The default values are Angband style tunnels.
#  \param minTunnelLength is the minimum amount of straight squares a tunnel must
#  go after turning.
#
#  Caution: high priority tunnels will barrel through anything.
#
#  We return a list of all points in the tunnel.  In the case of failure, which 
#  can occur if the tunnel travels some large distance without encountering anything
#  we return an empty tunnel and the code will try again with new starting points.    
def getFreeTunnel(genMap, start, target, turnPct = 30, 
        randDirectionPct = 10, priority = 1, minTunnelLength = 1):

    # keep track of all points in the tunnel    
    tunnel = []
    x = start[0]
    y = start[1]
    tunnelLength = 0
    if genMap.debug:
        print "attempting tunnel", start, target
    
    # Get the direction
    direction = util.geometry.getCardinalDirection(start, target)
        
    # Hopefully we hit something before 1000 steps!
    for count in xrange(1000):    
        # Move to the next square
        x += direction[0]
        y += direction[1]
        tunnelLength += 1
        # Add the current point to the tunnel
        tunnel.append((x, y))
        
        # We hit something, decide what to do next
        if not genMap.isHigherPriority(x, y, priority):
            # Did we end on a pierceable cell?
            if genMap.isPierceable(x, y) and len(tunnel) > 1:
                # move into the room
                x = x + direction[0]
                y = y + direction[1]
                tunnel.append((x, y))
            # We hit some obstacle.
            # \todo if a pierceable square is not the first square
            # we should probably also abort.
            elif len(tunnel) > 1:
                return tunnel

        # Do we turn?
        if (random.randint(1, 100) <= turnPct and tunnelLength > minTunnelLength):
            # Random turning?
            if (random.randint(1, 100) <= randDirectionPct):           
                direction = util.geometry.changeCardinalDirection(direction)
                
            # Turning directed towards target. to-do: don't allow u-turns
            else:
                direction = util.geometry.getCardinalDirection((x, y), target)
            # we just turned
            tunnelLength = 0
    
    # We wandered way too far.
    return []

            
## This routine makes a special tunnel around an obstacle.  It will hug the outside
#  of the obstacle using the marching squares algorithm.  At any point, if the target
#  direction is the opposite of the obstacle direction, it will peel off and head 
#  towards the target.  
#
#  Note: this will fail on convex structures like the following:
#
#  ...#####...
#  .B.#^>v#...
#  ...#<Ax#...
#  ...#.......
#  ...#...#...
#  ...#...#...
#  ...#####...
#  Here the tunnel will peel off at x and head towards B, it will do this until the
#  loop limit in getAngbandTunnel is reached, at which point it will give up and
#  try a different point.

#  /todo enable clockwise traversals
def tunnelAroundObstacle(genMap, tunnel, target, priority = 1):
    # paranoia, tunnel never got started
    if len(tunnel) < 2:
        return []
    # find the direction of the obstacle    
    obstacleDirection = util.geometry.getCardinalDirection(tunnel[-2], 
            tunnel[-1])
    # remove the last entry
    
    tunnel.pop(-1)
    # the new last entry is the tunnel start
    x, y = tunnel[-1]
    # set entrance to obstacle as a junction
    if genMap.debug:
        print "starting tunnel around object at x, y:", x, y
    
    # /todo give option for CW or CCW here.
    # Get the initial tunnel direction
    tunnelDirection = util.geometry.changeCardinalDirection(obstacleDirection, clockwise = 0)
    
    # Limit how many tries we can have
    for tries in xrange(1000):
        # See if we can get in the obstacle (counterclockwise direction forced)
        entranceDirections = genMap.adjacentPierceableObstacle(
                x, y, obstacleDirection, priority = 1)
        if entranceDirections:
            # We can get in!
            entranceLocation = random.choice(list(entranceDirections))
            tunnel.append((x, y))
            # Now move to that square.
            x = entranceLocation[0]
            y = entranceLocation[1]
            tunnel.append((x, y))
            if genMap.debug:
                print "obstacle entrance x, y:", x, y
            return tunnel
        # Get the marching square
        newMarchingSquare = genMap.makeMarchingSquare(x, y,
                obstacleDirection, priority = 1)
        # Find the appropriate directions
        newDirection, exitDirections = util.geometry.marchingSquare(
                newMarchingSquare)
            
        # First check if we should exit.  /todo this may fail on complicated convex 
        # structures, so we may need a better algorithm
        targetDirection = util.geometry.getCardinalDirection((x, y), target)
        if targetDirection in exitDirections:
            # move to the new tunnel location
            x += targetDirection[0]
            y += targetDirection[1]
            tunnel.append((x, y))
            if genMap.debug:
                print "leaving obstacle heading towards target"
                print "current location, target", x, y, target
            return tunnel
        
        # In the case that we're going straight, we should continue the tunnel
        if newDirection == tunnelDirection:
            x += tunnelDirection[0]
            y += tunnelDirection[1]
            tunnel.append((x, y))
            #print "going straight:", x, y
            continue
        
        # If we turned CCW it means we've hit an "outer" corner
        # /todo make this work for CW traversals also
        if not util.geometry.isClockwise(tunnelDirection, newDirection):
            # Make the corner square a tunnel
            x += tunnelDirection[0]
            y += tunnelDirection[1]
            tunnel.append((x, y))
            # Change the obstacle direction 
            obstacleDirection = util.geometry.changeCardinalDirection(obstacleDirection,
                    clockwise = 0)
            tunnelDirection = newDirection
            if genMap.debug:
                print "reached outer corner:", x, y    
            continue
            
        # If we turned CW it means we've hit an inner corner
        # in this case we need to just turn the obstacle direction without
        # deleting anything. /todo generalize to either direction
        if util.geometry.isClockwise(tunnelDirection, newDirection):
            obstacleDirection = util.geometry.changeCardinalDirection(obstacleDirection,
                    clockwise = 100)
            tunnelDirection = newDirection
            continue
            
        # The final option is that we're reversed 180, but that should never occur
        raise RuntimeError("tunnelAroundObjects got a reverse direction")               
    # Failure
    return []   
        

## Update the color map by taking the union of two of the sets
#  and adding in the tunnelPath    
def updateColorMap(colorMap, tunnelPath):
    # find the indices for the start and endpoints
    startIndex = getColorFor(colorMap, tunnelPath[-1])
    region = colorMap.pop(startIndex)
    # Now get the other index
    endIndex = getColorFor(colorMap, tunnelPath[0])
    # paranoia
    if startIndex == None or endIndex == None:
        raise runtimeError("Location not in color map")
    # Add in the second region
    region = region.union(colorMap.pop(endIndex))
    # This is a union between a set and a list, but it seems to work
    region = region.union(tunnelPath)
    colorMap.append(region)
        
        
## Returns a set of points yielding the A* approximation for the
#  shortest point between the start and the first connected region
#  we hit.
#  Note from d_m: tuples are faster, if connection is slow, we can
#  optimize by using them instead of dicts.
def getAStarTunnel(genMap, colorMap, startPoint, endPoint, startColor):
    
    # triedLocations is a dictionary where the key is the location
    # and the value is itself a dict that includes keys 'cost' with the cost from 
    # start to the current location and 'previous' with the location of 
    # the previous point in the tunnel.
    triedLocations = {startPoint: {'cost': 0, 'previous': None}}
    # activeHeap is a heap of (estimatedcost, dict) tuples.  The estimated cost
    # is the sum of the actual cost to the point for the shortest path found so
    # far, and the estimated cost from the point to the target.  The dict has keys
    # 'current', 'previous' and 'cost' indicating the current point, the previous
    # point, and the actual cost respectively
    activeHeap = []
    curHeapData = (getTunnelDistance(startPoint, endPoint) * genMap.defaultCost, 
            {'current': startPoint, 'previous': None, 'cost':0})
    heapq.heappush(activeHeap, curHeapData)
    curColor = startColor
    
    # Stop when we enter a zone with a new color
    while curColor == None or curColor == startColor:
        # Get a new point
        curHeapData = heapq.heappop(activeHeap)
        curX = curHeapData[1]['current'][0]
        curY = curHeapData[1]['current'][1]
        curColor = getColorFor(colorMap, (curX, curY))
        # Do not check boundary squares
        if genMap.isBoundary(curX, curY):
            continue
        # only check the cardinal directions
        for direction in util.geometry.cardinalDirections:
            newLocation = (curX + direction[0], curY + direction[1])
            newCost = curHeapData[1]['cost'] + genMap.getCost(curX, curY)
            
            # Find out if we've been here already and if so, if it was
            # cheaper down the previous path.
            if newLocation in triedLocations:
                if triedLocations[newLocation]['cost'] <= newCost:
                    continue
            
            # Add the new data to the heap
            heapq.heappush(activeHeap, 
                    (newCost + getTunnelDistance(newLocation, endPoint) * genMap.defaultCost, 
                    {'current': newLocation, 'previous': (curX, curY), 
                    'cost':newCost}))
                    
            # Update the triedLocations dict with the new data for this point
            triedLocations[newLocation] = {'cost': newCost, 'previous': (curX, curY)}
    
    return getTunnelPath((curX, curY), triedLocations)
    

## Get a tunnel path given an end point and a dictionary that uses points as keys
#  and includes the previous point in the values. (see getAStarTunnel for details)  
def getTunnelPath(startLocation, triedLocations):
    location = startLocation
    tunnelPath = [startLocation]
    while triedLocations[location]['previous'] is not None:
        location = triedLocations[location]['previous']
        tunnelPath.append(location)
    return tunnelPath


## Make a tunnel given a tunnel path
def constructTunnelFromPath(curMap, genMap, tunnelPath, priority = 1):
    
    for i in xrange(len(tunnelPath)):
        x = tunnelPath[i][0]
        y = tunnelPath[i][1]
    
        # Don't clear tunnels in rooms
        if genMap.isRoom(x, y):
            continue
            
        # There's already a tunnel here, mark it as a junction.
        # /todo this doesn't quite work properly, since new tunnels
        # that follow old ones will mark them all as junctions
        if genMap.isTunnel(x, y):
            genMap.addJunction(x, y)

        # clear the cell and set it to tunnel
        genUtility.clearCell(curMap, x, y)
        genMap.setTunnel(x, y, True)
        # /todo handle tunnel intersections properly
        # genMap.setPriority(x, y, priority)
        
        # Pierceable cell setting
        if i > 1 and i < len(tunnelPath) - 2:
            previous = tunnelPath[i - 1]
            future = tunnelPath[i + 1]
            # if the previous or future squares were a room, but this is
            # not we are at a junction
            if (genMap.isRoom(previous[0], previous[1]) or
                    genMap.isRoom(future[0], future[1])):
                genMap.addJunction(x, y)
            # Go through all the adjacent directions, find the ones
            # that aren't on the path and set them to pierceable
            for direction in util.geometry.cardinalDirections:
                xWall = x + direction[0]
                yWall = y + direction[1]
                if (xWall, yWall) not in (previous, future):
                    genMap.setPierceable(xWall, yWall, True, 
                            priority = priority)
            
        
    
## Get estimated tunnel distance (maybe put this in geometry)
#  /todo allow diagonal
def getTunnelDistance(startPoint, endPoint):
    xDistance = abs(startPoint[0] - endPoint[0]);
    yDistance = abs(startPoint[1] - endPoint[1]);
    return xDistance + yDistance

    
## This makes a "colored" map of the dungeon.  Basically it returns
#  a list of sets, where all items in each set are room/tunnel places
#  that are connected to each other    
def getColorMap(genMap, unconnectedLocations):
    colorMap = []
    preconnectedLocations = set()
    for center in list(unconnectedLocations):
        # Check to see if we've already found this place
        if getColorFor(colorMap, center) is not None:
            preconnectedLocations.add(center)
            continue
        # Find all points connected to the center
        connectedPoints = getConnectedRegion(genMap, center)        
        # Append the list off all the connected locations to this center to the map
        colorMap.append(connectedPoints)
    
    return colorMap, preconnectedLocations


## Make a color map for a selected area.  Returns a colorMap, a list containing sets
# of connected regions and "centers" for each region.  This option is slower than
# getColorMap, but does not require seeding the region with center locations.
# Hence, it knows nothing about regions that you wish to keep unconnected.
# Used for cavern connection and other regions with complicated geometries.      
def getColorMapForArea(genMap, xWest, yNorth, width, height):
    colorMap = []
    for x in xrange(xWest + width - 1):
        for y in xrange(yNorth + height - 1):
            # only care about room spaces
            if not genMap.isRoom(x, y):
                continue
            color = getColorFor(colorMap, (x, y))
            # not there
            if color is None:
                # Find a connected region and add it
                connectedPoints = getConnectedRegion(genMap, (x, y))
                colorMap.append(connectedPoints)
    return colorMap
    
                               
# Check if something is in a list of sets, more general than our current use        
def getColorFor(colorMap, location):
    # return false if empty
    if not colorMap:
        return None
    # go through all the sets
    for i in xrange(len(colorMap)):
        if location in colorMap[i]:
            return i
    
    # not there
    return None
       

## Returns a list of connected points to a starting location
#  Used by getColorMap and getColorMapForArea.
#
#  /todo make option to not include tunnels        
def getConnectedRegion(genMap, start, maxSteps = 10000):       
    # this is the set of all points connected to the center location.        
    connectedPoints = set()
    # This is for the iteration loop, it's the set of locations
    # that need to be looked at on each iteration
    pointsQueue = set()
    pointsQueue.add(start)
    steps = 0
    # stop when there are no more points to look at
    while pointsQueue and steps < maxSteps:
        steps += 1
        curPoint = pointsQueue.pop()
        connectedPoints.add(curPoint)
        for x in xrange(curPoint[0] - 1, curPoint[0] + 2):
            for y in xrange(curPoint[1] - 1, curPoint[1] + 2):
                # Check if we've already been here
                if (x, y) in connectedPoints:
                    continue
                if genMap.isClear(x, y) and not genMap.isBoundary(x, y):
                    # Add this place to the queue
                    pointsQueue.add((x, y)) 
    
    return connectedPoints
                    
       
## Add noise to the cost.  Eventually we will allow or perlin or 
#  marbled noise.  Basically whatever d_m cooks up.    
def addCostNoise(genMap, noiseType = 'random'):

    noiseGrid = [[0 for i in xrange(genMap.height)] for j in xrange(genMap.width)]
    
    # add random noise between 0 and the default cost
    # This option is for debug testing only.
    if noiseType == 'random':
        for x in xrange(genMap.width):
            for y in xrange(genMap.height):
                noiseGrid[x][y] += random.randint(0, genMap.defaultCost)
                
    # Add blocky noise, in an attempt to get angband style tunnels
    if noiseType == 'block':
        noiseGrid = getBlockNoise(noiseGrid, genMap.width, genMap.height)
                       
    # Derakon: this will be much quicker with numpy allowing for
    # matrix addition.
    # add the noise to the background
    for x in xrange(genMap.width):
        for y in xrange(genMap.height):
            # skip open areas
            if genMap.isClear(x, y):
                continue
            genMap.addCost(x, y, noiseGrid[x][y])


## This function adds blocks of noise to the function
#  \param blockNumber is the number of blocks (squares) of noise to 
#  add to the noise array.
#  \param blockSizeMin is the minimum block size for each block and
#  \param blockSizeMax is the maximum block size.  
#  It chooses a random location in the
#  dungeon grid and then places a block.
#  \param blockCostMin is the mininmum cost and 
#  \param blockCostMax is the maximum.
#  Different choices for these params will yield very different tunnel styles.
#  The default values roughly mimic angband turn frequencies, although further
#  improvement is possible.  Feedback requested                   
def getBlockNoise(noiseGrid, width, height, blockNumber = 300, 
        blockCostMin = 100, blockCostMax = 500, blockSizeMin = 1,
        blockSizeMax = 15):

    for block in xrange(blockNumber):
        # Get the width and height
        blockWidth = random.randint(blockSizeMin, blockSizeMax)
        blockHeight = random.randint(blockSizeMin, blockSizeMax)
        # Pick a cost
        blockCost = random.randint(blockCostMin, blockCostMax)
        # Find a location that fits in the grid
        xWest = random.randint(0, width - blockWidth - 1)
        yNorth = random.randint(0, height - blockHeight - 1)
        # Add the block to the noiseGrid
        for x in xrange(xWest, xWest + blockWidth - 1):
            for y in xrange(yNorth, yNorth + blockHeight - 1):
                noiseGrid[x][y] += blockCost

    return noiseGrid