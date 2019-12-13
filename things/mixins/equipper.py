import carrier
import container


## This class allows Things to equip items. All Things that can equip items
# can also carry them -- they have implicit inventories, though those
# inventories might have a maximum size of 0.
class Equipper(carrier.Carrier):
    def __init__(self, gameMap, *args):
        carrier.Carrier.__init__(self, gameMap, *args)
        ## Maps our equipment slot descriptions to the items in those slots.
        # Keys are e.g. "around your neck", "on left finger", etc.
        # These are also keys in self.equipDescToSlot.
        self.equipment = gameMap.makeContainerMap()
        ## Maps different types of equipment slots to lists of descriptions
        # of slots. E.g. "finger" maps to ["on left finger", "on right finger"].
        self.equipSlotToDescs = dict()
        ## Maps descriptions of equipment slots to the specific slot type.
        # E.g. "on left finger" maps to "finger". 
        self.equipDescToSlot = dict()
        ## Maps equipment slot descriptions to sets of functions to invoke 
        # when items are equipped to or unequipped from those slots.
        self.equipDescToTriggers = dict()


    ## Equip an Item to the specified slot, moving any already-equipped item
    # to our inventory.
    def equipItem(self, item, slotDesc):
        removedItem = self.equipment.get(slotDesc, None)
        self.equipment.subscribe(slotDesc, item)
        for trigger in self.equipDescToTriggers.get(slotDesc, set()):
            trigger(self, item, True)
            if removedItem is not None:
                trigger(self, removedItem, False)
        item.onEquip(self, self.gameMap, slotDesc)
        if removedItem is not None:
            self.addItemToInventory(removedItem)
            removedItem.onUnequip(self, self.gameMap)


    ## Remove whatever is in the specified slot, and add it to our inventory
    # unless told otherwise.
    def unequipItem(self, slotDesc, shouldTransferToInventory = True):
        removedItem = self.equipment.get(slotDesc, None)
        if removedItem is not None:
            for trigger in self.equipDescToTriggers.get(slotDesc, set()):
                trigger(self, removedItem, False)
            self.equipment.unsubscribe(slotDesc)
            if shouldTransferToInventory:
                self.addItemToInventory(removedItem)
            removedItem.onUnequip(self, self.gameMap)


    ## Attach a trigger to one of our equipment slots, that will get called
    # whenever an item enters or exits that slot.
    def addEquipTrigger(self, slotDesc, func):
        if slotDesc not in self.equipDescToTriggers:
            self.equipDescToTriggers[slotDesc] = set()
        self.equipDescToTriggers[slotDesc].add(func)
        item = self.equipment.get(slotDesc, None)
        if item is not None:
            func(self, item, False)


    ## Remove a trigger from one of our equipment slots.
    def removeEquipTrigger(self, slotDesc, func):
        self.equipDescToTriggers[slotDesc].remove(func)
        item = self.equipment.get(slotDesc, None)
        if item is not None:
            func(self, item, True)


    ## Drop an item, removing it from our inventory or equipment as appropriate.
    def dropItem(self, item):
        for slotDesc, equippedItem in self.equipment.iteritems():
            if item is equippedItem:
                self.unequipItem(item, shouldTransferToInventory = False)
        if item in self.inventory:
            self.removeItemFromInventory(item)
        item.pos = self.pos
        self.gameMap.addSubscriber(item, item.pos)
        item.onDrop(self, self.gameMap)


    ## Retrieve all items equipped to the slots of the specified type.
    def getItemsInSlotsOfType(self, slotType):
        result = []
        for desc in self.equipSlotToDescs.get(slotType, []):
            if desc in self.equipment:
                result.append(self.equipment[desc])
        return result

