## Database of Containers holding all the Things in the game. Includes a
# 2D grid of Cells for positional lookup.

import accessibilityMap
import cell
import container
import events
import mapgen.generator
import mapgen.genTown
import util.id
import util.serializer



class GameMap:
    def __init__(self, width, height):
        ## Unique identifier.
        self.id = util.id.getId()
        ## Number of columns in the map.
        self.width = width
        ## Number of rows in the map.
        self.height = height
        ## (width, height) list of lists of Cells.
        self.cells = []
        ## Maps Container IDs to the Containers. We also map our Cells' 
        # position tuples here even though those aren't their IDs. 
        self.idToContainerMap = dict()
        ## These functions want to know when we modify cells.
        self.updateCellFuncs = set()
        ## Maps tuples of Container IDs to AccessibilityMap instances. See
        # getAccessibilityMap().
        self.containerIdsToAccessibilityMap = dict()
        ## These containers are associated with functions used in the above.
        # See getFilterFunc().
        self.containerToFuncMap = dict()
        # We have one persistent container that we always keep around.
        self.idToContainerMap[container.PERSISTENT] = container.Container(
                container.PERSISTENT)
        self.makeCellArray()
        ## Maps Things to sets of containers they are in.
        self.thingToMemberships = {}
        ## Maps Thing names to those Things.
        self.nameToThing = {}


    ## Update dynamic elements of the map. We do this in order of the
    # updaters' energy ratings, until we get
    # to the player's turn, at which point we yield control back to the UI
    # layer (for input handling).
    def update(self):
        if container.UPDATERS not in self.idToContainerMap:
            return
        # We'll perform this loop until we get to the player's turn.
        while True:
            # Find the entity that has the least amount of "real" time left to
            # pass before they get a turn.
            sortedEntities = []
            updaters = self.getContainer(container.UPDATERS)
            minTimestep = None
            for thing in updaters:
                timestep = float(1 - thing.energy) / thing.getStat('speed')
                if minTimestep is None or timestep < minTimestep:
                    minTimestep = timestep
            if minTimestep > 0:
                # Add the requisite amount of energy to all entities.
                for thing in updaters:
                    thing.addEnergy(thing.getStat('speed') * minTimestep)

            # Sort entities by most energy, and if that's equal, by name.
            sortedUpdaters = sorted(list(updaters),
                    lambda a, b: cmp(b.energy, a.energy) or cmp(a.name, b.name))
            # Update entities with at least 1 energy, until we reach the player.
            player = self.getContainer(container.PLAYERS)[0]
            while sortedUpdaters[0].energy >= 1:
                curCreature = sortedUpdaters[0]
                # Ensure the creature is still valid -- other creatures may 
                # have destroyed it.
                if curCreature not in self.thingToMemberships:
                    del sortedUpdaters[0]
                    continue
                curCreature.update()
                if curCreature is player:
                    # All done updating things for now; return control to the
                    # UI layer.
                    return
                # Entity now has a new energy score, so insert them into their
                # proper location in the list. Assume their energy is probably
                # low, so start from the back.
                # \todo This requires a lot of iterating over the list, which
                # seems inefficient -- an O(N^2) algorithm, potentially. Still,
                # don't optimize it if it's not a problem.
                del sortedUpdaters[0]
                index = len(sortedUpdaters)
                while (index > 0 and
                        curCreature.energy > sortedUpdaters[index - 1].energy):
                    index -= 1
                sortedUpdaters.insert(index, curCreature)


    ## Fill in self.cells with an array of empty Containers.
    def makeCellArray(self):
        self.cells = []
        for x in xrange(self.width):
            self.cells.append([])
            for y in xrange(self.height):
                newCell = cell.Cell((x, y))
                self.cells[x].append(newCell)
                # We keep track of Cells both by their position and by their
                # unique Container IDs.
                self.idToContainerMap[(x, y)] = newCell
                self.idToContainerMap[newCell.id] = newCell
        # HACK: have a Cell at (-1, -1) for objects that need a position but
        # don't need a *valid* position (e.g. in the process of deserializing
        # saved games.
        newCell = cell.Cell((-1, -1))
        self.idToContainerMap[(-1, -1)] = newCell
        self.idToContainerMap[newCell.id] = newCell


    ## Create a new level at the specified depth. This first requires us to
    # delete the old one. In fact, much of the "map" (more like an object
    # database) is preserved whenever a new level is generated -- anything that
    # persists will stick around, including e.g. the player, all their items,
    # and any "object" that does not really exist in "reality"
    # (e.g. the object that handles refreshing the stores every so often).
    #
    # In the future this function will choose which level archetype to make.
    # For the meantime this is a trivial decision, the only archetypes are 
    # a town and a normal level (the Angband level).
    #
    # Width and Height should probably be set here too.
    def makeLevel(self, targetLevel):
        # \todo Does simply forgetting all our non-persistent objects suffice,
        # or should we be manually unsubscribing everyone?
        persisters = self.idToContainerMap[container.PERSISTENT]
        self.idToContainerMap = {container.PERSISTENT: persisters}
        self.makeCellArray()
        for member in persisters:
            member.resubscribe(self)

        if targetLevel <= 0:
            self.mapLevel = 0
            mapgen.genTown.makeTownLevel(self, self.width, self.height)
        else:
            self.mapLevel = targetLevel
            mapgen.generator.makeAngbandLevel(self, targetLevel, self.width, self.height)

        self.resetCellFuncs(self.updateCellFuncs)
        events.publish('new level generation')


    ## Receive a new update func.
    def addUpdateCellFunc(self, func):
        if func not in self.updateCellFuncs:
            self.updateCellFuncs.add(func)
            self.resetCellFuncs([func])


    ## Tell our cells about these functions they need to call when they 
    # get updated.
    def resetCellFuncs(self, funcs):
        for x in xrange(self.width):
            for y in xrange(self.height):
                self.cells[x][y].addUpdateFuncs(funcs)


    ## Get the accessibility map associated with the provided Container IDs.
    # If we don't have one, make one.
    def getAccessibilityMap(self, *containerIds):
        containerIds = tuple(sorted(containerIds))
        if containerIds not in self.containerIdsToAccessibilityMap:
            func = lambda cell, gameMap: bool(gameMap.filterContainer(cell, *containerIds))
            newMap = accessibilityMap.AccessibilityMap(self, func)
            self.containerIdsToAccessibilityMap[containerIds] = newMap
        return self.containerIdsToAccessibilityMap[containerIds].getMap()


    ## Try to move the given Thing from the first position to the second.
    # If there are obstructions, return a Container holding them. Otherwise,
    # update where we store the Thing (and its 'pos' field).
    def moveMe(self, thing, source, target):
        x, y = target
        blockers = self.getContainer((x, y), container.BLOCKERS)
        result = self.makeContainer()
        for blocker in blockers:
            if not blocker.canMoveThrough(thing):
                result.subscribe(blocker)
        if not result:
            # It can move there, so move it.
            self.cells[x][y].subscribe(thing)
            self.cells[source[0]][source[1]].unsubscribe(thing)
            self.thingToMemberships[thing].remove(source)
            self.thingToMemberships[thing].add(target)
            thing.pos = target
        return result


    ## Change the position of a thing.
    def moveThing(self, thing, fromPos, toPos):
        self.idToContainerMap[fromPos].unsubscribe(thing)
        self.idToContainerMap[toPos].subscribe(thing)
        self.thingToMemberships[thing].remove(fromPos)
        self.thingToMemberships[thing].add(toPos)


    ## Add a Thing to a Container. 
    def addSubscriber(self, subscriber, containerID):
        if containerID not in self.idToContainerMap:
            # Make sure the container exists first.
            self.makeContainer(containerID, notifyOnEmpty = self.containerIsEmpty)
        self.idToContainerMap[containerID].subscribe(subscriber)
        if subscriber not in self.thingToMemberships:
            self.thingToMemberships[subscriber] = set()
        self.thingToMemberships[subscriber].add(containerID)


    ## Register a Thing by its name, indicating that we want to keep track of 
    # it.
    def registerThingByName(self, thing):
        if thing.name in self.nameToThing:
            raise RuntimeError("Tried to register Thing with name %s with is already claimed" % thing.name)
        self.nameToThing[thing.name] = thing


    ## Remove a Thing from a Container.
    def removeSubscriber(self, subscriber, containerID):
        self.idToContainerMap[containerID].unsubscribe(subscriber)
        self.thingToMemberships[subscriber].remove(containerID)


    ## Destroy the specified Thing, removing it from all relevant containers
    # as we do.
    def destroy(self, thing):
        for containerID in self.thingToMemberships[thing]:
            self.idToContainerMap[containerID].unsubscribe(thing)
        if thing in self.thingToMemberships:
            del self.thingToMemberships[thing]
        if thing.name in self.nameToThing:
            del self.nameToThing[thing.name]


    ## Given a Thing and a position, either destroy that Thing, or remove
    # it from the specified position, depending on if the Thing's pos field
    # is None or not.
    # A None for position means that the Thing is just an alias, and is not
    # really in that location anyway; just pretending to be.
    def removeFrom(self, thing, pos):
        if thing.pos is None:
            self.removeSubscriber(thing, pos)
        else:
            self.destroy(thing)


    ## Container is empty, so destroy it.
    def containerIsEmpty(self, containerID):
        del self.idToContainerMap[containerID]


    ## Create a new Container. This is basically just a passthrough to the 
    # Container constructor, except that we then note down the Container for
    # later tracking. If you want a new Container for any non-transient 
    # purpose, you should use this function so the GameMap can keep track of 
    # the Container for you.
    def makeContainer(self, *args, **kwargs):
        newContainer = container.Container(*args, **kwargs)
        self.idToContainerMap[newContainer.id] = newContainer
        return newContainer


    ## Create a new ContainerMap. See makeContainer.
    def makeContainerMap(self, *args, **kwargs):
        newContainer = container.ContainerMap(*args, **kwargs)
        self.idToContainerMap[newContainer.id] = newContainer
        return newContainer


    ## Provided with an arbitrary number of Container IDs, return a Container
    # that is all the Things that are in the intersection of all of those
    # Containers (that is, for each additional provided ID, we prune down the
    # eligible Things).
    def getContainer(self, *containerIDs):
        result = self.idToContainerMap.get(containerIDs[0], 
                self.makeContainer())
        if len(containerIDs) == 1:
            # Already done.
            return result
        return self.filterContainer(result, *containerIDs[1:])


    ## Perform an intersection of the given container with the provided
    # container IDs.
    def filterContainer(self, targetContainer, *containerIDs):
        for containerID in containerIDs:
            targetContainer = targetContainer.getIntersection(self.getContainer(containerID))
        return targetContainer


    ## Generate a ready-to-be-serialized dict representing our data. See the
    # util.serializer module for more information.
    def getSerializationDict(self):
        result = dict(self.__dict__)
        # These will have to be recreated on load.
        del result['containerIdsToAccessibilityMap']
        del result['updateCellFuncs']
        return result


    ## Save the game. 
    def save(self):
        import time
        saver = util.serializer.Serializer()
        start = time.time()
        import cProfile
        saver.addObject(self)
        curTime = time.time()
        print "Adding objects took",(curTime - start)
#        cProfile.runctx('saver.writeFile("save.txt")', locals(), globals(), 'profiling.pro')
        saver.writeFile('save.txt')
        print "Writing took",(time.time() - curTime)


    ## Load the game. Technically this doesn't require any GameMap instance
    # to exist, and certainly doesn't need to be a member function of the 
    # GameMap, but this is a convenient location, right next to save(). 
    # \todo Is this really the best place for load()?
    def load(self):
        loader = util.serializer.Deserializer()
        loader.loadFile('save.txt')
        newMap = loader.getGameMap()
        # Because the map's cells weren't necessarily around when the entities
        # that create update-cell funcs are created, we need to reset all of
        # them now.
        newMap.resetCellFuncs(newMap.updateCellFuncs)
        # Let other entities know about the new GameMap.
        events.publish('new game map', newMap)


    ## Utility function to make accessing the player easy.
    def getPlayer(self):
        return self.getContainer(container.PLAYERS)[0]


    ## Return a synthetic container of all Things adjacent to the specified
    # position.
    def getAdjacentThings(self, pos):
        result = self.makeContainer()
        for xOffset in [-1, 0, 1]:
            for yOffset in [-1, 0, 1]:
                result.unionAdd(
                        self.getContainer((pos[0] + xOffset, pos[1] + yOffset))
                )
        return result


    ## Get the container IDs for the containers the given Thing is in.
    def getMembershipsFor(self, thing):
        return self.thingToMemberships[thing]


    ## Get a Thing, given its name.
    def getThingWithName(self, name):
        return self.nameToThing.get(name, None)


    ## Simple getter
    def getDimensions(self):
        return (self.width, self.height)


    ## Return True if the given location is in-bounds.
    def getIsInBounds(self, loc):
        return (0 <= loc[0] < self.width) and (0 <= loc[1] < self.height)



## Create a "blank" GameMap, as part of the deserialization process.
def makeBlankGameMap(width, height):
    return GameMap(width, height)


util.serializer.registerObjectClass(GameMap.__name__, makeBlankGameMap)


