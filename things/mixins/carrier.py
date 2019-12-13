import container
import util.extend

## This class allows Things to pick up, carry, and drop items.
class Carrier:
    ## \param numSlots How many unique items the Thing can carry. 
    # \todo Pick a better default?
    def __init__(self, gameMap, numSlots = 23, maxCount = None):
        ## Holds items we're carrying.
        self.inventory = gameMap.makeContainer()
        ## Categories of objects that we can carry.
        # If this is empty, can carry any item.
        self.carriableCategories = util.extend.Categories()
        ## Max size of inventory, in terms of slots (i.e. unique item types)
        self.maxCarriedSlots = numSlots
        ## Max size of inventory, in terms of total individual items (e.g. no
        # more than 40 arrows).
        self.maxCarriedCount = maxCount
        ## Functions to trigger when we pick up / drop items.
        self.inventoryTriggers = set()


    ## Add us back to any appropriate Containers in the GameMap.
    def resubscribe(self, gameMap):
        if self.maxCarriedCount or self.maxCarriedSlots:
            gameMap.addSubscriber(self, container.CARRIERS)


    ## Return true if there's room for a specific Item in our inventory, and
    # it's of a type we can carry.
    # \todo Handle stack merging.
    def getCanCarryItem(self, item):
        # Paranoia: don't put things into themselves.
        if item is self:
            return False
        # If we're an immutable container, then we pretend we can't carry
        # anything.
        if not self.getCanModifyInventory():
            return False
        # See if we're allowed to carry objects of this type.
        # If carriableCategories is empty then there are no category restrictions.
        if not self.carriableCategories or self.carriableCategories.has(item.categories):
            if (self.maxCarriedSlots is not None and 
                    len(self.inventory) >= self.maxCarriedSlots):
                # All slots are occupied.
                return False
            if (self.maxCarriedCount is not None and 
                    self.getNumberCarriedItems() + item.quantity >= self.maxCarriedCount):
                # We've exceeded our max count of items.
                return False
            # Ok, we can carry this item
            return True

        # If we reached here, we can't carry the item.
        return False


    ## Get the total number of items we are carrying.
    def getNumberCarriedItems(self):
        return sum([i.quantity for i in self.inventory])


    ## Return True iff we're allowed to change the contents of our inventory.
    def getCanModifyInventory(self):
        return not bool(self.stats.getStatValue('FIXED_CONTENTS'))


    ## Add an Item to our inventory, if possible; otherwise drop it.
    def addItemToInventory(self, item):
        if len(self.inventory) >= self.maxCarriedSlots:
            self.dropItem(item)
            item.onDrop(self, self.gameMap)
        else:
            self.inventory.subscribe(item)
            item.pos = None
            item.onPickup(self, self.gameMap)
            for trigger in self.inventoryTriggers:
                trigger(self, item, False)


    ## Remove an Item from our inventory (either to move it elsewhere or
    # because it's been destroyed). The caller is responsible for where it ends
    # up afterwards. We also recurse through our children if they are
    # containers. 
    # Return True if we are successful.
    def removeItemFromInventory(self, target):
        didSucceed = False
        if target in self.inventory:
            self.inventory.unsubscribe(target)
            didSucceed = True
        else:
            for item in self.inventory:
                if item.isContainer() and item.removeItemFromInventory(target):
                    didSucceed = True
        if didSucceed:
            for trigger in self.inventoryTriggers:
                trigger(self, target, True)
        return didSucceed


    ## Attach a function to our inventory, that gets called whenever an item
    # enters or leaves it.
    def addInventoryTrigger(self, func):
        self.inventoryTriggers.add(func)
        # Retroactively apply the function to all inventory items.
        for item in self.inventory:
            func(self, item, False)
            if item.isContainer():
                item.addInventoryTrigger(func)


    ## Remove a function from our inventory triggers.
    def removeInventoryTrigger(self, func):
        self.inventoryTriggers.remove(func)
        # Let the function clean up any changes it might have made.
        for item in self.inventory:
            func(self, item, True)
            if item.isContainer():
                item.removeInventoryTrigger(func)


    ## Drop an item, removing it from our inventory.
    def dropItem(self, item):
        self.removeItemFromInventory(item)
        item.pos = self.pos
        self.gameMap.addSubscriber(item, item.pos)
        item.onDrop(self, self.gameMap)


    ## Return True if we contain the specified item, or a container we contain
    # contains it, etc.
    def contains(self, target):
        for item in self.inventory:
            if item is target or (item.isContainer() and item.contains(target)):
                return True
        return False


    ## Return True if any item in ourselves matches the specified container key.
    def containsMatch(self, key):
        if self.gameMap.filterContainer(self.inventory, key):
            return True
        for item in self.inventory:
            if item.isContainer() and item.containsMatch(key):
                return True
        return False


    ## Get how many slots of items are in the inventory.
    def getNumUsedSlots(self):
        return len(self.inventory)


    ## Get how many total items are in the inventory.
    def getNumContainedItems(self):
        return sum([i.quantity for i in self.inventory])



## Yield items from the provided container. When we encounter a container, we
# recurse (if recursionDepth allows), yielding a tuple of 
# (parent item, child item). Of course this tuple may achieve arbitrary 
# length depending on recursionDepth.
# \param recursionDepth If we are carrying other containers, and
# recursionLevel is at least 1, and those containers are open, then we list
# their contents too.
# \param shouldIgnoreOpenness: If True, then we recurse into containers even if 
#        they aren't currently "open" (since "open" is merely a display 
#        property). 
def generateItemList(inventory, recursionDepth = 2, shouldIgnoreOpenness = False):
    for item in inventory:
        yield (item,)
        if (item.isContainer() and recursionDepth > 1 and 
                (item.isOpen() or shouldIgnoreOpenness)):
            for subItem in generateItemList(item.inventory, recursionDepth - 1, shouldIgnoreOpenness):
                yield (item,) + subItem


## Index into a provided container, with recursion, like in generateItemList.
def indexIntoInventory(inventory, index, recursionDepth = 2, curCount = 0):
    amTopLevel = curCount == 0
    contents = inventory
    if isinstance(inventory, container.ContainerMap):
        # We want to iterate over the Things, not their labels.
        contents = inventory.values()
    for item in contents:
        if curCount == index:
            return item
        curCount += 1
        if item.isContainer() and item.isOpen() and recursionDepth > 1:
            result = indexIntoInventory(item.inventory, index, 
                    recursionDepth - 1, curCount)
            if type(result) is int:
                # No result; just update curCount
                curCount = result
            else:
                return result
    if amTopLevel:
        # No item exists at that index.
        return None
    # Otherwise we're in one of the recursion layers; return curCount so that
    # our caller knows how many items we've iterated over.
    return curCount

