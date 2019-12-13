## A class that creates a specific creature type as needed.

import creature
import creatureLoader
import procs.procLoader
from .. import stats
import things.items.itemAllocator
import things.items.loot
import util.boostedDie
import util.extend
import util.randomizer
import util.record

import collections
import copy
import random

## Order we put fields in when serializing. Fields that are not represented
# in this list will not be preserved when records are serialized. A None is
# inserted wherever we want a newline in the serialization.
FIELD_ORDER = ['index', 'name', None, 
'display', None,
'category', 'templates', None, 
'procs', None,
'equipDescToSlot', None,
'stats', None,
'type', 'nativeDepth', 'rarity', 'experienceValue', None,
'blows', None, 'flags', None, 'description', None]

## Fields where we blindly copy our value onto the creature when it is created.
COPY_FIELDS = ["nativeDepth", "rarity", "experienceValue", "type", 
        "description", "display"]

## Fields where, instead of us replacing the existing value when we apply
# as a template, we append onto the existing value.
EXTEND_FIELDS = ['blows', 'flags']



## This class is used to instantiate Creatures *or* to modify existing 
# Creatures (by applying a template to them). We do this because the records
# that describe creatures are almost identical to the ones that describe
# creature templates, so if they were to be split into two different
# classes then there'd be a lot of redundancy and frankly ugly code. 
class CreatureFactory:
    ## \param record A dictionary of data (deserialized JSON dictionary)
    #         containing all the information we have for this record.
    def __init__(self, record):
        ## Copy of the dict directly (i.e. without templates being applied) 
        # representing us. We may need this for later reserialization.
        self.record = record
        ## This dict represents all of our attributes, including those inherited
        # from our templates. 
        self.completeRecord = copy.deepcopy(record)

        # Start out with a bunch of default values; some of these (possibly
        # even all of them) will get filled in from record in a bit, but we
        # need to ensure they all exist.

        ## Unique integer identifying us.
        self.index = None
        ## Name of the creature
        self.name = None
        ## Categories the creature falls into. This also includes any 
        # templates we apply.
        self.categories = util.extend.Categories()
        ## Dict of display information for various display modes.
        self.display = {}
        ## Stats instance to hold modifiable statistics
        self.stats = stats.Stats()
        ## Where we normally show up in the dungeon.
        self.nativeDepth = None
        ## How likely we are to be generated.
        self.rarity = None
        ## How much XP we're worth.
        self.experienceValue = None
        ## List of melee attacks.
        self.blows = []
        ## Various characteristics we can have.
        self.flags = []
        ## String describing the creature (may be lengthy).
        self.description = ''
        ## Broad category we belong to (e.g. dragon, hydra, kobold)
        self.type = None
        ## Templates that apply to us. Templates are also CreatureFactory
        # instances; they apply base attributes that we then add to and
        # override.
        self.templates = []
        ## Mapping of slot description to slot type for items we can equip.
        # For example, "around your neck" maps to  "neck".
        self.equipDescToSlot = dict()
        ## Short text description of what we are (e.g. "Townsperson", 
        # "Creeping Coins"). Basically a slightly more verbose description
        # of self.type.
        self.category = None
        ## List of drop profiles from which we generate our drops. These set
        # the parameters of what is dropped - number of items, allowed types,
        # chances of affixes/theme etc. They are LootTemplate objects.
        self.drops = []

        ## Mapping of trigger conditions to procs.
        self.procs = {}

        ## Special procs that attach to the Factory instead of to a specific
        # Creature, because they only make sense to invoke before a Creature
        # has been created. This is a mapping of trigger condition to 
        # a list of the Procs to call.
        self.staticProcs = {}

        # Apply our templates to our complete record, and copy over
        # Effect instances.
        for template in map(creatureLoader.getTemplate, record.get('templates', [])):
            util.record.applyValues(template.completeRecord, self.completeRecord)
            util.record.applyValues(template.staticProcs, self.staticProcs)


        # Apply our now-updated complete record to ourselves; we're now a 
        # fully-specified definition for the Creature we represent.
        for key, value in self.completeRecord.iteritems():
            setattr(self, key, value)

        # Templates will overwrite our name, so restore it now. 
        # \todo This qualifies as a hack, yep.
        self.name = record['name']

        # Copy templates to our categories.
        self.categories.update(self.completeRecord.get('templates', []))

        # Convert our stats record into a Stats instance.
        if 'stats' in self.completeRecord:
            self.stats = stats.deserializeStats(self.completeRecord['stats'])

        # Convert flags into +1 stats.
        for flag in self.flags:
            self.stats.addMod(flag, stats.StatMod(0, 1))

        # Extract out static procs based on their trigger conditions. 
        # \todo This is a moderately ugly hack.
        # Make a copy of self.procs to iterate over so we can delete from
        # the original as we go.
        for procRecord in list(self.procs):
            # Generate a Proc instance -- most of the time we just throw this
            # away, so this is mildly wasteful, but it keeps the code tidy.
            # Note that we don't pass a specific level here -- static procs
            # should never need to correspond to any "level".
            proc = procs.procLoader.generateProcFromRecord(procRecord)
            if proc.triggerCondition in procs.proc.STATIC_TRIGGERS:
                if proc.triggerCondition not in self.staticProcs:
                    self.staticProcs[proc.triggerCondition] = []
                self.staticProcs[proc.triggerCondition].append(proc)
                # Remove the old record so that it's not attached to real
                # creatures when we make them.
                del self.procs[self.procs.index(procRecord)]

        # Turn our drop profiles into loot template objects
        # NB self.drops may be the same thing as self.completeRecord['drops']
        # at this stage, hence the secondary list.
        # \todo Track down why this happens and determine if this is the 
        # correct workaround.
        newDrops = []
        for drop in self.completeRecord.get('drops', []):
            lootTemplate = things.items.loot.LootTemplate(drop)
            newDrops.append(lootTemplate)
        self.drops = newDrops


    ## Create our creature at the specified position.
    def makeCreature(self, gameMap, pos):
        result = creature.Creature(gameMap, pos, self.name)
        result = self.applyAsTemplate(result)
        result.index = self.index
        result.subtype = self.name
        result.stats = self.stats.copy()
        result.categories.update(self.categories)
        # Roll any stats that use the BoostedDie format.
        # Use a default level of 0.
        result.stats.roll(0)
        # Consolidate tier-0 stats together into single values.
        self.stats.consolidateTier(0, 'fundamental %s')
        # Start at maximum health.
        result.curHitpoints = result.getStat('maxHitpoints')
        # Create any drops in inventory
        for drop in self.drops:
            # Finalise the loot rules
            drop.resolveValues(gameMap.mapLevel)
            # Actually create the items, if we pass the dropChance
            if util.randomizer.passPercentage(drop.dropChance):
                allocator = things.items.itemAllocator.ItemAllocator(gameMap.mapLevel, drop)
                numDrops = util.boostedDie.roll(drop.numDrops)
                for i in xrange(numDrops):
                    item = allocator.allocate(gameMap, result.inventory)

        return result


    ## Apply ourselves as a template to the given creature. Note that all of 
    # the templates in self.record were applied to us, in our constructor.
    def applyAsTemplate(self, creature):
        # Transfer our stat modifiers.
        creature.stats.mergeStats(self.stats)
        # Normally I wouldn't use getattr and setattr but the alternative
        # is a massive list of really repetitive "Do we have this attribute?
        # Okay, then set it on the creature." code.
        for field in COPY_FIELDS:
            setattr(creature, field, getattr(self, field))
        for field in EXTEND_FIELDS:
            getattr(creature, field).extend(getattr(self, field))

        # Instantiate Procs.
        for procRecord in self.procs:
            proc = procs.procLoader.generateProcFromRecord(procRecord, creature.nativeDepth)
            if proc.triggerCondition not in creature.procs:
                creature.procs[proc.triggerCondition] = []
            creature.procs[proc.triggerCondition].append(proc)

        # Here we need to set up the reverse-mapping.
        for slotDesc, slotType in self.equipDescToSlot.iteritems():
            creature.equipDescToSlot[slotDesc] = slotType
            if slotType not in creature.equipSlotToDescs:
                creature.equipSlotToDescs[slotType] = []
            creature.equipSlotToDescs[slotType].append(slotDesc)

        return creature


    ## Get the name of the creature.
    def getName(self):
        return self.name


    ## Get the specified stat for the creature. NB none of the stat values
    # have been rolled at this point.
    def getStat(self, statName):
        return self.stats.getStatValue(statName)


    ## Generate a string serialization of ourselves.
    # HACK: reorder self.record['stats'] so the sub-elements are in
    # alphabetical order.
    def getSerialization(self):
        recordToUse = self.record
        if 'stats' in self.record:
            newStats = collections.OrderedDict()
            for key in sorted(self.record['stats'].keys()):
                newStats[key] = self.record['stats'][key]
            newRecord = copy.deepcopy(self.record)
            newRecord['stats'] = newStats
            recordToUse = newRecord
        return util.record.serializeRecord(recordToUse, FIELD_ORDER)


    ## Trigger procs with the specified trigger condition and parameters.
    # We can only trigger StaticProcs from here, since those are the ones that
    # are not specific to an individual Creature.
    def triggerProcs(self, triggerCondition, *args, **kwargs):
        for proc in self.staticProcs.get(triggerCondition, []):
            proc.trigger(self, *args, **kwargs)


    ## Needed for sorting, when we want to display CreatureFactories in a 
    # sensible order.
    def __cmp__(self, alt):
        return cmp(self.nativeDepth, alt.nativeDepth) or cmp(self.name, alt.name)

