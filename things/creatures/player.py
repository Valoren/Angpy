import mapgen.cell
import container
import creature
import gui
import util.fieldOfView
import util.cmap

import numpy
import sys



## The Player is just another Creature; however, we keep track of what the
# player can see and remember about the map, and they're stored in a special
# Container (the PLAYERS Container, natch) so that lots of other code refers
# to them.
class Player(creature.Creature):
    def __init__(self, gameMap, pos, name):
        creature.Creature.__init__(self, gameMap, pos, name)
        self.resubscribe(gameMap)
        ## This is set to True if the user ever uses the debug commands, 
        # which are cheating.
        self.hasUsedDebugCommands = False
        
        ## 2D Numpy array of which cells we can currently see.
        self.fovMap = numpy.zeros(gameMap.getDimensions(), dtype = numpy.bool)
        ## Boolean to track if we need to recreate the FOV.
        self.haveMadeFOV = False
        
        ## 2D Numpy array describing the paths to the player.
        self.heatMap = None

        ## The player's memory of the state of the game map, implemented as a
        # 2D array (list of lists) of Cells. Doesn't include
        # known-transient entities (anything in the UPDATERS container), but
        # everything else is remembered as of the last time the player "saw"
        # them by any means (e.g. detection, not just line-of-sight).
        # \todo Probably we should have a MOBILE container or something for
        # transient objects instead, since there might be stationary UPDATERS.
        self.mapMemory = []
        ## Maps (x, y) coordinates to corresponding Cells, for ease of lookup.
        self.coordsToCell = dict()
        for x in xrange(gameMap.width):
            self.mapMemory.append([])
            for y in xrange(gameMap.height):
                newCell = mapgen.cell.Cell((x, y))
                self.mapMemory[x].append(newCell)
                self.coordsToCell[(x, y)] = newCell
        gameMap.addUpdateCellFunc(self.onCellChange)


    def resubscribe(self, gameMap):
        creature.Creature.resubscribe(self, gameMap)
        gameMap.addSubscriber(self, container.PLAYERS)
        gameMap.addSubscriber(self, container.PERSISTENT)


    ## Special things happen when the player dies.
    def die(self, *args):
        response = gui.prompt.resolvePrompt(gui.prompt.YesNoPrompt(
            message = "http://www.sadtrombone.com/ Would you like your possessions identified? y/n"))
        while response:
            response = gui.prompt.resolvePrompt(gui.prompt.YesNoPrompt(
                message = "Too bad, identification isn't implemented yet. y/n"))
        sys.exit()


    ## A Cell has been modified. We only find out about it if the Cell is
    # visible.
    def onCellChange(self, cell, newThing, wasAdded):
        if newThing is None:
            # Cell is empty.
            self.coordsToCell[cell.pos].setEmpty()
            return
        if self.fovMap[cell.pos]:
            if wasAdded:
                self.coordsToCell[cell.pos].subscribe(newThing)
            else:
                self.coordsToCell[cell.pos].unsubscribe(newThing)


    ## Update the player's knowledge of the game world.
    def update(self):
        # Trigger any procs we have that occur on update.
        creature.Creature.update(self)
        self.updateFOV()
        self.generateHeatMap()


    ## Update our internal knowledge of the game map, based on what is
    # currently in our field of view. As things enter our FOV, we need to 
    # update our mental model; as they leave, we need to prune out transient
    # objects.
    def updateFOV(self):
        # Make a copy of our map so we can compare before/after and see
        # what has changed.
        oldMap = numpy.array(self.fovMap)
        # Start all cells as not visible.
        self.fovMap[:] = 0
        # Get a simplified map of the game that marks the cells that obstruct
        # view.
        blockedMap = self.gameMap.getAccessibilityMap(container.OPAQUES)
        # Generate the map of cells that are visible from our position.
        # \todo Make the view radius more configurable.
        util.fieldOfView.setFieldOfView(blockedMap, self.pos, 20,
                self.markCellInFOV)
        # Find cells whose visibility status has changed
        changedCellLocs = oldMap != self.fovMap
        # Find cells that are newly visible.
        # Note use of & instead of 'and', a requirement for multiple
        # booleans in Numpy.
        xVals, yVals = numpy.where(self.fovMap & changedCellLocs)
        # Blow out our old knowledge of those cells and replace it with
        # what we can actually directly see.
        for x, y in zip(xVals, yVals):
            myCell = self.coordsToCell[(x, y)]
            myCell.setEmpty()
            myCell.unionAdd(self.gameMap.getContainer((x, y)))
        # Find cells that are newly no-longer-visible, and remove all
        # transient entries from our memory of their contents.
        xVals, yVals = numpy.where(numpy.invert(self.fovMap) & changedCellLocs)
        updaters = self.gameMap.getContainer(container.UPDATERS)
        for x, y in zip(xVals, yVals):
            myCell = self.coordsToCell[(x, y)]
            # Cast to list so we can remove elements as we iterate over the
            # contents.
            for oldThing in list(myCell.members):
                if oldThing in updaters:
                    myCell.unsubscribe(oldThing)


    ## Update our field-of-view map.
    def markCellInFOV(self, x, y):
        self.fovMap[x, y] = 1


    ## Return True iff we can see the specified position.
    def canSee(self, pos):
        if not self.haveMadeFOV:
            # Initialize the FOV now.
            self.updateFOV()
            self.haveMadeFOV = True
        return bool(self.fovMap[pos[0], pos[1]])


    ## Generate a heat map describing the valid paths to reach the player.
    def generateHeatMap(self):
        blockedMap = self.gameMap.getAccessibilityMap(container.BLOCKERS)
        self.heatMap = util.cmap.getHeatMap(blockedMap, [self.pos])


    ## Get the heat map. If it hasn't been generated yet, then generate it.
    def getHeatMap(self):
        if self.heatMap is None:
            # Initialize our heat map for the current map.
            self.generateHeatMap()
        return self.heatMap


    ## Generate a ready-to-be-serialized dict of our data. See the 
    # util.serializer module for more information.
    def getSerializationDict(self):
        result = dict(self.__dict__)
        # Remove the Numpy arrays, which util.serializer can't handle.
        del result['fovMap']
        del result['heatMap']
        return result



## Generate a "blank" Player object, as part of deserialization.
def makeBlankPlayer(gameMap):
    return Player(gameMap, (-1, -1), 'Blank player')


util.serializer.registerObjectClass(Player.__name__, makeBlankPlayer)


## Generate a test player.
def debugMakePlayer(gameMap):
    import creatureLoader
    import things.stats
    player = Player(gameMap, (0, 0), '<player>')
    creatureLoader.getTemplate('Half-Troll').applyAsTemplate(player)
    creatureLoader.getTemplate('Warrior').applyAsTemplate(player)
    creatureLoader.getFactory('<player>').applyAsTemplate(player)
    player.name = 'you'
    for flag in player.flags:
        player.stats.addMod(flag, things.stats.StatMod(0, 1))
    player.subtype = '<player>'
    player.stats.roll(0)
    player.stats.consolidateTier(0, 'fundamental %s')
    player.curHitpoints = 300
    player.stats.addMod('maxHitpoints', things.stats.StatMod(0, 300))
    player.energy = 1
    player.stats.addMod('creatureLevel', things.stats.StatMod(0, 50))
    player.stats.addMod('weaponFinesse', things.stats.StatMod(0, 20))
    player.stats.addMod('weaponProwess', things.stats.StatMod(0, 30))

