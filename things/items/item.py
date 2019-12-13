## Items are Things that you can pick up, put into containers, etc.

import container
import things.thing
import things.mixins.carrier
import things.stats
import util.grammar
import util.randomizer
import util.serializer



class Item(things.thing.Thing, things.mixins.carrier.Carrier):
    def __init__(self, gameMap, pos = None):
        ## type and subtype are initialized by Thing
        things.thing.Thing.__init__(self, pos)
        things.mixins.carrier.Carrier.__init__(self, gameMap)
        ## Keep track of this for later use.
        self.gameMap = gameMap
        ## Display metadata
        self.display = dict()
        ## List of procs we can trigger.
        self.procs = []
        ## List of affixes on the item (will store name, type and level).
        self.affixes = []
        ## Stats instance describing our abilities.
        self.stats = things.stats.Stats()
        ## Categories that describe the item
        self.categories = util.extend.Categories()
        ## List of equip slots we can be wielded to.
        self.equipSlots = []
        ## Amount of the item.
        self.quantity = None
        ## Number of charges on the item.
        self.charges = None
        ## For items that can be invoked for a special effect, the verb to 
        # invoke them (e.g. "read", "quaff", "zap").
        self.useVerb = None
        ## For items that are containers, whether or not the item's contents
        # are on display.
        self.isContainerOpen = True
        ## Flavor of the object, if applicable.
        self.flavor = None
        ## The item's theme name/position
        self.theme = None
        ## Prose description
        self.description = ''
        ## The item's general name information
        self.nameInfo = dict()

        # cache description values (maybe?)
        self.cachedDescription = dict()

    
    ## Perform any necessary initialization now that our fields have been
    # set by an outside entity.
    def init(self, gameMap):
        self.resubscribe(gameMap)
        things.mixins.carrier.Carrier.resubscribe(self, gameMap)
    

    ## Add us to appropriate containers.
    def resubscribe(self, gameMap):
        if self.pos:
            gameMap.addSubscriber(self, self.pos)
        gameMap.addSubscriber(self, container.ITEMS)
        if self.equipSlots:
            gameMap.addSubscriber(self, container.WIELDABLES)
        for proc in self.procs:
            if proc.triggerCondition == 'item use':
                gameMap.addSubscriber(self, container.USABLES)
                break
        gameMap.addSubscriber(self, container.INTERESTING)


    ## Retrieve a particular stat, like whether or not we resist fire, or
    # our bonus to prowess.
    def getStat(self, statName):
        return self.stats.getStatValue(statName)


    ## Retrieve our entire Stats instance.
    def getStats(self):
        return self.stats


    ## Respond to the item being picked up.
    def onPickup(self, user, gameMap):
        self.triggerProcs('onPickup', source = user, gameMap = gameMap)


    ## Respond to being dropped.
    def onDrop(self, user, gameMap):
        self.triggerProcs('onDrop', source = user, gameMap = gameMap)


    ## Respond to being equipped.
    def onEquip(self, user, gameMap, equipSlot):
        self.triggerProcs('item wield', equipSlot = equipSlot, source = user, 
                gameMap = gameMap)
        user.addStats(self.stats)


    ## Respond to being unequipped.
    def onUnequip(self, user, gameMap):
        self.triggerProcs('item removal', source = user, gameMap = gameMap)
        user.removeStats(self.stats)


    ## Return True if we are equippable.
    def canEquip(self):
        return bool(self.equipSlots)


    ## Use us -- invoke any appropriate onUse procs.
    def onUse(self, user, gameMap):
        # \todo How do we handle items that have targets other than the user?
        self.triggerProcs('item use', source = user, target = user, 
                gameMap = gameMap)


    ## Return True if we have any procs that trigger on item use.
    def canUse(self):
        for proc in self.procs:
            if proc.triggerCondition == 'item use':
                return True
        return False


    ## Get the verb string that describes *how* the item is used.
    def getUseVerb(self):
        return self.useVerb


    ## Return True if the item is a container.
    def isContainer(self):
        return self.maxCarriedSlots or self.maxCarriedCount


    ## Toggle display of the container's contents.
    def setIsOpen(self, value):
        self.isContainerOpen = value


    ## Return True if the item is a container that is currently "open" (i.e.
    # its contents are on display.
    def isOpen(self):
        return self.isContainer() and self.isContainerOpen

    
    ## Trigger procs that have the specified trigger.
    def triggerProcs(self, trigger, *args, **kwargs):
        for proc in self.procs:
            if proc.triggerCondition == trigger:
                proc.trigger(item = self, *args, **kwargs)


    ## Return a string describing the item
    # \param quantity Optional parameter to set the quantity to display.
    #        Defaults to the item's normal quantity.
    def getShortDescription(self, quantity = None):
        if quantity is None:
            quantity = self.quantity
        name = u''

        # proc version of naming
        alterCallbacks = [p for p in self.procs if p.triggerCondition == 'alter name']
        for proc in self.procs:
            if proc.triggerCondition == 'get name':
                name = proc.trigger(self, quantity, alterCallbacks)

        if self.isContainer():
            # Add information on how much we're carrying.
            numSlots = self.getNumUsedSlots()
            if not numSlots:
                name += u' {empty}'
            else:
                numItems = self.getNumContainedItems()
                pluralizer = [u'', u's'][numSlots != 1]
                name += u' {%d slot%s, %d total}' % (numSlots, pluralizer, numItems)

        return name


    ## Generate a ready-to-be-serialized dict of our data. See the 
    # util.serializer module for more information.
    def getSerializationDict(self):
        return self.__dict__


    ## For debugging purposes, convert to string.
    def __unicode__(self):
        return u"<Item: %s>" % (self.getShortDescription())



## Generate a "blank" Item as part of the deserialization process.
def makeBlankItem(gameMap):
    return Item(gameMap)


util.serializer.registerObjectClass(Item.__name__, makeBlankItem)
