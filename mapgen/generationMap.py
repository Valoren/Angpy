import util.geometry

import random

## This class is used to store and manipulate all the temporary
#  data that is necessary for map generation.  Nothing in this
#  class will be kept around after generation is complete, so
#  anything that needs to be kept for gameplay should be 
#  included elsewhere, such as in gameMap.

class GenerationMap:
    def __init__(self, width, height):
        ## Number of columns
        self.width = width
        ## Number of rows
        self.height = height
        ## Information needed for all grids
        # Value of background cost
        self.defaultCost = 20
        self.grid = ([[GenCell(self.defaultCost) for i in xrange(height)] 
                for j in xrange(width)])
        ## List of (x,y) tuples specifying all the room centers that need to 
        #  be connected.  
        self.centers = set()
        ## List of centers for vaults and other special rooms with simple
        #  entrances.  
        self.vaultCenters = set()
        # Set of (x,y) tuples specifying junction squares (either corridor corridor or
        # room corridor
        self.junctions = set()
        # Print debug messages
        self.debug = False


    
    ## The set of definitions below are used to check and manipulate the
    # priority grid
    
    ## Can only overwrite squares that have a strictly lower
    # priority
    def isHigherPriority(self, x, y, priorityValue, equalIsOK = False):
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")
        if not equalIsOK:
            return priorityValue > self.grid[x][y].priority
        else:
            return priorityValue >= self.grid[x][y].priority
    
    
    ## Check if we can overwrite priority, then do it
    def setPriority(self, x, y, priorityValue):
        # Paranoia, check bounds
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")     
        if self.isHigherPriority(x, y, priorityValue):
            self.grid[x][y].priority = priorityValue
            

    ## Overwrite priority regardless of whether we should
    def overwritePriority(self, x, y, priorityValue):
        # Paranoia, check bounds
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")    
        self.grid[x][y].priority = priorityValue

        
    ## The set of functions below are used to check and manipulate the
    #  room center list
        
    ## Check to see if location is a room center
    def isCenter(self, x, y):
        return (x, y) in self.centers
        
    
    ## Add a center to the list    
    def addCenter(self, x, y):
        # Paranoia, make sure the center is in the grid
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")
        # Add it
        self.centers.add((x, y))
       
    
    ## Add a set of centers to the list
    #  This function does not have a bounds check, so be careful!
    def addSeveralCenters(self, centerSet):
        self.centers.update(centerSet)
    
    
    ## Remove a room center from the list
    def removeCenter(self, x, y):
        if self.isCenter(x, y):
            self.centers.remove((x, y))
                
            
    ## Get a random center location
    def getRandomCenter(self):
        # Paranoia, make sure there's an element
        if not self.centers:
            return -1, -1
        return random.choice(list(self.centers))
        
    
    def addVaultCenter(self, x, y):
        # Paranoia, make sure the center is in the grid
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")           
        # Add it
        self.vaultCenters.add((x, y))
    
    
    ## Setting and manipulating Junctions
    # Check to see if location is a room junction
    def isJunction(self, x, y):
        return (x, y) in self.junctions
        
    
    ## Add a junction to the list    
    def addJunction(self, x, y):
        # Paranoia, make sure the junction is in the grid
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")            
        # Add it
        self.junctions.add((x, y))
        
        
    ## Remove a room junction from the list
    def removeJunction(self, x, y):
        if self.isJunction(x, y):
            self.junctions.remove((x, y))
                
            
    ## Get a random junction location
    def getRandomJunction(self):
        # Paranoia, make sure there's an element
        if not self.junctions:
            raise RuntimeError("Attempt to get junction when there are none")
        return random.choice(list(self.junctions))
       

    ## The set of functions below are used to check and manipulate the
    # pierceable location list    
      
    ## Check if wall is pierceable
    def isPierceable(self, x, y):
        # Paranoia, ensure in bounds
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")        
        return self.grid[x][y].isPierceable
        
    
    ## Set location as pierceable
    def setPierceable(self, x, y, value, priority = 0):
        # Paranoia, ensure in bounds
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")
        if (not priority) or self.isHigherPriority(x, y, priority):
            self.grid[x][y].isPierceable = value
                   
            
    ## Check whether any squares in the nearby "marchingSquare" are higher priority
    # and pierceable.  
    # This is used when tunnelling (or pathing) around an obstacle.  An obstacle is
    # defined as a higher priority region than whatever is doing the tunneling.  It finds
    # grid locations in the object structure that are pierceable.  These are
    # entrance locations into the object.
    # It returns a set of all possible entrances into the obstacle
    def adjacentPierceableObstacle(self, x, y, obstacleDirection, clockwise = False, 
            priority = 1):
            
        entrances = set()
        # Get northwest corner
        xNW, yNW = self.marchingSquareNW(x, y, obstacleDirection, clockwise = clockwise)
                
        for x in xrange(xNW, xNW + 2):
            for y in xrange(yNW, yNW + 2):
                # only add places that are both obstacles and pierceable
                if (not self.isHigherPriority(x, y, priority) and 
                        self.isPierceable(x, y)):
                    entrances.add((x, y))
                    
        return entrances
    
    
    ## Functions to deal with tunnels
    def isTunnel(self, x, y):
        if not self.isInBounds(x, y):
            print "out of bounds", x, y
            print "width, height", self.width, self.height
            raise RuntimeError("out of bounds")
        return self.grid[x][y].isTunnel
        
        
    def setTunnel(self, x, y, value):
        # Paranoia, ensure in bounds
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")            
        self.grid[x][y].isTunnel = value
    
    
    ## The set of functions below are used to check and manipulate
    #  room locations
    def isRoom(self, x, y):
        if not self.isInBounds(x, y):
            print "out of bounds", x, y
            print "width, height", self.width, self.height
            raise RuntimeError("out of bounds")
        return self.grid[x][y].isRoom
        
        
    def setRoom(self, x, y, value):
        # Paranoia, ensure in bounds
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")            
        self.grid[x][y].isRoom = value
        
    
    ## Get the number of rooms adjacent (including diagonals)
    #  to the given location.
    def getNumAdjacentRooms(self, xCenter, yCenter):
        count = 0
        # We check all adjacent squares, being careful not to trespass over
        # the boundary
        for x in xrange(max(0, xCenter - 1), min(self.width, xCenter + 2)):
            for y in xrange(max(0, yCenter - 1), min(self.height, yCenter + 2)):
                # Don't count the center square
                if x == xCenter and y == yCenter:
                    continue
                if self.isRoom(x, y):
                    count += 1
        return count

    
    ## Set the cost for a grid square
    def setCost(self, x, y, value):
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")
        self.grid[x][y].cost = value
        
        
    ## Return the cost for a grid square
    def getCost(self, x, y):
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")
        return self.grid[x][y].cost
        
    
    ## add the cost to the already existing cost
    def addCost(self, x, y, value):
        if not self.isInBounds(x, y):
            print "x, y", x, y
            raise RuntimeError("Out of bounds")
        self.grid[x][y].cost += value
    
    ## General purpose functions
    
    ## Set everything with a single call
    def setGridInfo(self, x, y, priority = 0, isRoom = False, isPierceable = False, 
            isTunnel = False, cost = None):
        if cost is None:
            cost = self.defaultCost
        self.setPriority(x, y, priority)    
        self.setPierceable(x, y, isPierceable)    
        self.setRoom(x, y, isRoom)
        self.setTunnel(x, y, isTunnel)
        self.setCost(x, y, cost)
        
    
    ## Check if the location is in bounds
    def isInBounds(self, x, y):
        return (0 <= x < self.width) and (0 <= y < self.height)
        
        
    ## Check if the location is on the boundary    
    def isBoundary(self, x, y):
        return x == 0 or x == self.width - 1 or y == 0 or y == self.width
        
     
    ## check if the location is clear (either a room or tunnel)
    def isClear(self, x, y):
        return self.isRoom(x, y) or self.isTunnel(x, y)
        
        
    ## Get a random cell that fits user given restrictions
    #  we set a default number of tries so the function doesn't get
    #  caught in an infinite loop if it fails to find one.
    def getRandom(self, tries = 1000, isRoom = False, isPierceable = False):
        for i in xrange(tries):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if isRoom and not self.grid[x][y].isRoom: 
                continue
            if isPierceable and not self.grid[x][y].isPierceable: 
                continue
            return x, y
        # Return something indicating failure
        raise RuntimeError("failed to get a cell that fits requirements")
        

    ## Helper function for both makeMarchingSquare and adjacentPierceableObstacle
    #  returns the x and y coordinates for the northWest corner of the marching square
    #  Depending on where the obstacle is relative to the current location, the 
    #  marching square can be any of 4 possibilities.
    #  remember: south is positive
    def marchingSquareNW(self, x, y, obstacleDirection, clockwise = False):
        
        # There probably is an codewise efficient way to do this, but for clarity and testing
        # we'll write out the cases explicitly.  /todo clean up.
        
        # Case 1: starting location is in the SouthEast
        if ((not clockwise and obstacleDirection == (-1, 0)) or
                (clockwise and obstacleDirection == (0, -1))):
            return (x - 1, y - 1)
        # Case 2: starting location is in SouthWest
        elif ((not clockwise and obstacleDirection == (0, -1)) or
                (clockwise and obstacleDirection == (1, 0))):
            return (x, y - 1)
        # Case 3: starting location is in NorthEast
        elif ((not clockwise and obstacleDirection == (0, 1)) or
                (clockwise and obstacleDirection == (-1, 0))):
            return (x - 1, y)
        # case4: starting location is in NorthWest
        elif ((not clockwise and obstacleDirection == (1, 0)) or
                (clockwise and obstacleDirection == (0, 1))):
            return (x, y)
        else:
            print "Inappropriate direction:", direction
            raiseRuntimeError("Non-unitary or non-cardinal direction")
            
    
    ## This constructs an array used for the marchingSquares function in util.Geometry.
    #  It is used specifically for pathfinding around arbitrarily shaped obstacles.
    #  The input is a starting square, a cardinal direction indicating which square is the obstacle,
    #  a preference for traversing clockwise or counterclockwise, and
    #  a value for the priority threshold with which to consider an obstacle.
    #  The function will raise an error if any square is out of bounds (should not be possible if
    #  boundary has a high priority!) or if the direction is bogus    
    def makeMarchingSquare(self, x, y, obstacleDirection, clockwise = False, priority = 1):

        # Get northwest corner
        xNW, yNW = self.marchingSquareNW(x, y, obstacleDirection, clockwise = clockwise)
        
        # Construct the matrix
        # /todo assignations are merely for clarity (and testing), could combine 
        # the matrix construction and the return in one line.
        northWest = self.isHigherPriority(xNW, yNW, priority)
        northEast = self.isHigherPriority(xNW + 1, yNW, priority)
        southWest = self.isHigherPriority(xNW, yNW + 1, priority)
        southEast = self.isHigherPriority(xNW + 1, yNW + 1, priority)
        
        
        return [[northWest, southWest], [northEast, southEast]]
        
        
## This class is for information that is stored in a grid map
#  and is used for dungeon generation.  Information stored here
#  will disappear after dungeon generation.  Stuff that needs
#  to stay around until later, needs to go elsewhere.
class GenCell:
    def __init__(self, cost):
        # cost is the background cost for tunneling through something
        self.cost = cost
        # Room cells include obstacles that should be treated as connected
        # e.g. vault cells that should be tunneled through.  It does *not*
        # include vault cells that are permanent walls
        self.isRoom = False
        # These cells surround rooms and are the angband style tunnel's way
        # of knowing that it hit a new area to connect to.
        self.isPierceable = False
        # Tunnel cells may contain doors and rubble.
        self.isTunnel = False
        # An area should be allowed to overwrite another area if it's higher priority.
        # Exception: tunnel cells clearing pierceable cells.
        self.priority = 0

        