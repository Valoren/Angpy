
import container
import gui
from .. import thing
from .. import stats
import things.mixins.updater
import things.mixins.equipper
import util.extend
import util.serializer



## Creatures are active Things that can move about, participate in fighting, 
# etc. They must implement the update() function, which performs whatever state
# updates are needed each turn.
class Creature(thing.Thing, 
        things.mixins.updater.Updateable, things.mixins.equipper.Equipper):
    def __init__(self, gameMap, pos, name):
        thing.Thing.__init__(self, pos)
        things.mixins.updater.Updateable.__init__(self, gameMap, 
                name)
        things.mixins.equipper.Equipper.__init__(self, gameMap)

        ## Start out with a bunch of default values; these should get
        # filled in as we are created by outside forces.
        self.index = None
        ## Categories the creature falls into.
        self.categories = util.extend.Categories()
        self.display = {}
        ## When this reaches 0 we die.
        self.curHitpoints = None

        ## Stats instance for all of our modifiable numbers.
        self.stats = stats.Stats()
        self.nativeDepth = None
        self.rarity = None
        self.experienceValue = None
        self.blows = []
        self.flags = []
        self.description = ''
        self.category = None
        
        ## Currently targeted Thing for ranged abilities.
        self.curTarget = None

        ## Maps creature names to how many of them have been killed by this 
        # specific Creature. Note this is the true number killed, not the 
        # number the creature is known to have killed (which may be inaccurate
        # due to e.g. being blind at the time).
        self.killCountMap = {}

        ## The creature's database of observations. Maps strings to information 
        # the creature knows; the information stored may be binary, a data 
        # range, textual, etc. This is mostly only relevant for the player, but
        # we track it for all creatures since it may come in handy at some
        # point (e.g. for creatures that can learn).
        self.keyToKnowledge = dict()

        ## Maps trigger conditions to lists of Procs to invoke when those 
        # triggers occur.
        self.procs = {}

        ## We'll need to have this available for AI and the like.
        self.gameMap = gameMap
        gameMap.addSubscriber(self, self.pos)
        self.resubscribe(gameMap)
        

    ## Add us to any appropriate Containers in the GameMap, except for the 
    # positional Container -- because our position may not be valid when
    # this function is called (e.g. because a new level has been created and
    # we're not actually on it yet).
    def resubscribe(self, gameMap):
        things.mixins.carrier.Carrier.resubscribe(self, gameMap)
        gameMap.addSubscriber(self, container.ATTACKERS)
        gameMap.addSubscriber(self, container.BLOCKERS)
        gameMap.addSubscriber(self, container.UPDATERS)
        gameMap.addSubscriber(self, container.CREATURES)
        gameMap.addSubscriber(self, container.INTERESTING)


    ## Attack the specified Thing in melee combat.
    def meleeAttack(self, alt):
        self.triggerProcs('on attack', self, alt, self.gameMap)


    # Return True if this is acceptable, False otherwise.
    # Default implementation is to reject movement attempts.
    def canMoveThrough(self, alt):
        return False


    ## Update state -- call any procs with a "creature update" trigger.
    def update(self):
        self.triggerProcs('update', self, self.gameMap)


    ## Use an item.
    def useItem(self, item):
        item.onUse(self, self.gameMap)


    ## Tweak an item. Probably doesn't belong here.
    def tweakItem(self, item):
        # Prompt for this
        depth = 100
        # Apply a random theme
        lootRules = things.items.loot.LootTemplate({})
        lootRules.magicLevel = depth
#        allocator = things.items.itemAllocator.AffixAllocator(item.type, item.subtype, lootRules)
        allocator = things.items.itemAllocator.ThemeAllocator(item.type, item.subtype, lootRules, item.affixes)
        theme = allocator.allocate()
        if theme is not None:
            theme.applyTheme(depth, item)
            gui.messenger.message("added %s" % theme.name)
        else:
            gui.messenger.message("No available themes.")



    ## Remove the creature from the game.
    # \param killer The Creature responsible for killing us, if applicable.
    def die(self, killer = None):
        # Drop anything we're carrying
        while self.inventory:
            self.dropItem(self.inventory[0])
        # Remove ourselves from the map
        self.gameMap.destroy(self)
        if killer is not None:
            # Update the killer's kill count.
            if self.name not in killer.killCountMap:
                killer.killCountMap[self.name] = 1
            else:
                killer.killCountMap[self.name] += 1


    ## Get the value for one of our stats.
    def getStat(self, statName):
        return self.stats.getStatValue(statName)


    ## Add a stats.StatMod for the named stat.
    def addStatMod(self, statName, mod):
        self.stats.addMod(statName, mod)


    ## Clear a specific modifier for the named stat.
    def removeStatMod(self, statName, mod):
        self.stats.removeMod(statName, mod)


    ## Add an entire Stats instance to our own stats.
    def addStats(self, newStats):
        self.stats.addStats(newStats)


    ## Remove an entire Stats instance from our own stats.
    def removeStats(self, deadStats):
        self.stats.removeStats(deadStats)


    ## Retrieve our Stats instance for direct manipulation.
    def getStats(self):
        return self.stats


    ## Add a Proc with the specified trigger condition.
    def addProc(self, triggerCondition, proc):
        if triggerCondition not in self.procs:
            self.procs[triggerCondition] = []
        self.procs[triggerCondition].append(proc)


    ## Remove the specified Proc with the given trigger condition.
    def removeProc(self, triggerCondition, proc):
        if triggerCondition not in self.procs:
            raise ValueError("Attempted to destroy proc with invalid trigger condition %s" % triggerCondition)
        if proc not in self.procs[triggerCondition]:
            raise ValueError("Attempted to destroy proc %s with trigger condition %s when we don't have that proc under that trigger condition" % (proc, triggerCondition))
        index = self.procs[triggerCondition].index(proc)
        del self.procs[triggerCondition][index]


    ## Trigger procs with the specified trigger condition and parameters.
    def triggerProcs(self, triggerCondition, *args, **kwargs):
        for proc in self.procs.get(triggerCondition, []):
            proc.trigger(*args, **kwargs)


    ## Get the knowledge the creature has for the given key, or None if the 
    # creature knows nothing. Keys are sequences of strings (e.g. 
    # ('creature', 'Yellow mold', 'blows', 0); values are arbitrary.
    def getKnowledge(self, *args):
        return self.keyToKnowledge.get(args, None)


    ## Set the knowledge the creature has for the given key to the given value.
    def setKnowledge(self, key, value):
        self.keyToKnowledge[key] = value


    ## When knowledge is for a range of numbers (e.g. knowing that a melee 
    # attack does 4-6 damage), this function allows us to update that range.
    # The range will be as small as possible while including the given value.
    def setKnowledgeRange(self, key, value):
        curRange = self.keyToKnowledge.get(key, None)
        if curRange is None:
            # Must create a new range.
            self.setKnowledge(key, (value, value))
        else:
            # Update the existing range.
            self.setKnowledge(key,
                    (min(value, curRange[0]), max(value, curRange[1])))


    ## When knowledge is an incrementing value, increment that value. Values
    # implicitly start from 0.
    def incrementKnowledge(self, *args):
        curVal = self.getKnowledge(*args)
        if curVal is None:
            self.setKnowledge(args, 1)
        else:
            self.setKnowledge(args, curVal + 1)


    ## Generate a ready-to-be-serialized dict containing all pertinent data
    # for this Creature. See the util.serializer module for more info.
    def getSerializationDict(self):
        return self.__dict__


    ## For debugging purposes.
    def __unicode__(self):
        return u"<Creature of type %s at %s>" % (self.name, self.pos)



## Create a "blank" Creature as part of deserializing a savefile.
def makeBlankCreature(gameMap):
    return Creature(gameMap, (-1, -1), 'Blank creature')



util.serializer.registerObjectClass(Creature.__name__, makeBlankCreature)
