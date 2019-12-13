## Class that creates an Item on demand.

import affix
import allocatorRules
import gui.flavors
import item
import itemAllocator
import itemLoader
import procs.procLoader
from .. import stats
import util.boostedDie
import util.record


## Order we want to print out components of the item record when we serialize.
# None denotes a newline.
FIELD_ORDER = ['index', 'type', 'subtype', None,
        'templateName', 'randomize', None,
        'templates', None,
        'categories', None,
        'nameInfo', None,
        'display', None,
        'stats', None,
        'flags', None,
        'mods', None,
        'procs', None,
        'useVerb', None,
        'equipSlots', None,
        'carriableCategories', None,
        'maxCapacity', None,
        'allocatorRules', None,
        'description', None,
]

## Fields that we just copy verbatim over to newly-created Items.
COPIED_FIELDS = ['index',
                 'type', 'subtype', 'categories',
                 'nameInfo', 'flavor', 'display', 'description',
                 'useVerb', 'equipSlots',
                 'carriableCategories', 'maxCarriedSlots', 'maxCarriedCount'
                ]


class ItemFactory:
    ## \param record A dictionary containing our instantiation data.
    def __init__(self, record):
        ## We need to hold onto this in case we're being used as a template, 
        # and for later serialization.
        self.record = record
        ## Names of templates that specify some of our information.
        self.templates = []
        # Explicit listing of our possible fields, since not all of them
        # are in the record.
        ## Unique identifying integer.
        self.index = None
        ## Broad typing for the object (e.g. potion, polearm, missile)
        self.type = None
        ## Name of the object
        self.subtype = None
        ## Categories that describe the item
        self.categories = util.extend.Categories()
        ## The item's general name information
        self.nameInfo = dict()
        ## Flavor of the object, if applicable
        self.flavor = None
        ## Display metadata
        self.display = dict()
        ## Stats instance containing all stats for the item.
        self.stats = stats.Stats()
        ## Information on how we allocate ourselves.
        self.allocatorRules = []
        ## Dictionaries used to make the procs the item can trigger.
        self.procRecords = []
        ## List of bonuses.
        self.mods = []
        ## List of flags
        self.flags = []
        ## Amount of charges
        self.charges = None
        ## Verb for invoking the item (e.g. "quaff", "read", "zap") if 
        # applicable.
        self.useVerb = None
        ## Slots item is equipped to, if equippable.
        self.equipSlots = []
        ## Categories of items that this object can carry
        self.carriableCategories = util.extend.Categories()
        ## Maximum number of slots of items this item can contain.
        self.maxCarriedSlots = None
        ## Maximum total number of items this item can contain.
        self.maxCarriedCount = None
        ## Prose description
        self.description = ''
        ## Boolean for whether we ever randomise this item
        self.randomize = False
        ## Whether this factory is for a unique item that has been created
        self.artifactCreated = False

        # Build a full record based on the current object and all ancestor 
        # templates.
        completeRecord = util.record.buildRecord(self, 
                itemLoader.getItemTemplate)
        # Apply that record to ourselves, setting appropriate attributes in 
        # place.
        util.record.applyRecord(self, completeRecord)

        # Mark this factory as a template if it has a template name.
        self.isTemplate = hasattr(self, 'templateName')

        # Retain the first category added per object as the object's 'subtype'.
        # This is used for determining the getFactoryName value.
        if 'subtype' not in self.record:
            if 'categories' in self.record and self.record['categories']:
                self.subtype = self.record['categories'][0]

        # Generate itemAllocatorRules from our allocatorRules field.
        self.allocatorRules = []
        if 'allocatorRules' in completeRecord:
            self.allocatorRules = [allocatorRules.ItemAllocatorRule(a)
                    for a in completeRecord['allocatorRules']]

        # Convert certain entries into BoostedDie instances. These may not
        # actually exist; in that case we create a dummy BoostedDie anyway 
        # that always rolls 0.
        self.charges = util.boostedDie.BoostedDie(
                completeRecord.get('charges', {}))

        # Fill in our stats.
        self.stats = stats.deserializeStats(completeRecord.get('stats', {}))
        # Apply flags as -1/+1 modifiers, depending on if they begin with a 
        # '-'
        for flag in self.flags:
            if flag.startswith('-'):
                self.stats.addMod(flag, stats.StatMod(0, -1))
            else:
                self.stats.addMod(flag, stats.StatMod(0, 1))

        # Remember procs to apply to items.
        self.procRecords = completeRecord.get('procs', [])

        # Expand out our carrying capacity limits and
        # place in top-level fields for copying to items.
        if 'maxCapacity' in completeRecord:
            if 'count' in completeRecord['maxCapacity']:
                self.maxCarriedCount = completeRecord['maxCapacity']['count']
            if 'slots' in completeRecord['maxCapacity']:
                self.maxCarriedSlots = completeRecord['maxCapacity']['slots']

        # Chose a flavor if the object is marked as FLAVORED.
        if "FLAVORED" in self.flags:
            # Don't generate flavors for templates.
            if not self.isTemplate:
                # The object has to specify flavorTypes values in order to
                # properly select a flavor to apply.
                if 'flavorTypes' in self.nameInfo:
                    self.flavor = gui.flavors.chooseFlavorFromCategory(self.nameInfo['flavorTypes'])


    ## Apply random properties to items
    def applyMagic(self, item, lootRules = None):
        # Test that we have some loot rules to apply, and can apply them
        # (items with no equipSlots cannot be worn, so cannot have affixes)
        if lootRules is None or not item.equipSlots:
            # Nothing to do
            return

        # Temporary hack - we don't yet generate jewelry using affixes/themes
        # \todo Generate jewelry using affixes
        if item.categories.has(['ring', 'amulet']):
            return

        # Set number of affixes to apply
        remaining = lootRules.numAffixes
        # Effective generation level for all post-creation modification
        itemLevel = lootRules.magicLevel

        # Apply any affixes and/or theme specified explicitly
        for affixName in lootRules.affixes:
            affix = itemLoader.getAffix(affixName)
            affix.applyAffix(itemLevel, item)
        if lootRules.themeName:
            theme = itemLoader.getTheme(lootRules.themeName)
            theme.applyTheme(itemLevel, item)
            return

        # Address any minimum requirements for this itemLevel
        limits = itemLoader.getAffixLimits(itemLevel)
        limits.minAffixLevel = lootRules.minAffixLevel
        limits.maxAffixLevel = lootRules.maxAffixLevel
        # Deal with lootRules which override global limits
        # subdict names are levelsMin, levelsMax, typesMin, typesMax
        for name, subdict in lootRules.affixLimits.iteritems():
            for key, value in subdict.iteritems():
                limits.__dict__[name][key] = value
        # Apply affixes until minima are met or we run out
        while (limits.levelsMin or limits.typesMin) and remaining:
            # Create an allocator which meets the requirements
            allocator = itemAllocator.AffixAllocator(item.categories,
                    lootRules, limits, item.affixes)
            # Ask it for an affix
            affix = allocator.allocate()
            if affix is not None:
                remaining -= 1
                affix.applyAffix(itemLevel, item)
                # Decrement the requirements it meets, removing when done
                if affix.affixType in limits.typesMin:
                    limits.typesMin[affix.affixType] -= 1
                    if limits.typesMin[affix.affixType] == 0:
                        del limits.typesMin[affix.affixType]
                if affix.affixLevel in limits.levelsMin:
                    limits.levelsMin[affix.affixLevel] -= 1
                    if limits.levelsMin[affix.affixLevel] == 0:
                        del limits.levelsMin[affix.affixLevel]
            else:
                # Allocator could not provide any affixes
                gui.messenger.message("%s Minima:" % item.categories)
                for key, value in limits.levelsMin.iteritems():
                    gui.messenger.message("%s %s" % (key, value))
                for key, value in limits.typesMin.iteritems():
                    gui.messenger.message("%s %s" % (key, value))
                gui.messenger.message("Unable to meet minimum affix requirements")
                break

        # Try for a theme, if we have at least two affixes
        if len(item.affixes) > 1:
            self.tryTheme(item, lootRules)

        # Now apply the remaining affixes, with free choice
        while remaining and not item.theme:
            allocator = itemAllocator.AffixAllocator(item.categories,
                    lootRules, limits, item.affixes)
            affix = allocator.allocate()
            remaining -= 1
            if affix is not None:
                affix.applyAffix(itemLevel, item)
                if len(item.affixes) > 1:
                    self.tryTheme(item, lootRules)
            else:
                print "No affix available! That shouldn't happen!"
                # \todo - Crash in production version    


    ## Short method to create a themeAllocator and apply the theme
    def tryTheme(self, item, lootRules):
        allocator = itemAllocator.ThemeAllocator(item.categories,
                                                 lootRules, item.affixes)
        theme = allocator.allocate()
        if theme is not None:
            theme.applyTheme(lootRules.magicLevel, item)


    ## Instantiate an item based on us, and put it at the given
    # location, if applicable.
    # We assume that we have at least one valid allocatorRule.
    # \param itemLevel The level to use when generating the item -- this can 
    # determine modifiers (e.g. bonuses to stats, number of charges, pile size).
    def makeItem(self, itemLevel, gameMap, pos = None, lootRules = None):
        newItem = item.Item(gameMap, pos)
        for field in COPIED_FIELDS:
            newItem.__dict__[field] = self.__dict__[field]
        # Copy our stats across.
        newItem.stats = self.stats.copy()

        # Apply mods -- these may vary on a per-item basis, so we have to wait
        # to calculate them until now.
        for mod in self.mods:
            bonus = util.boostedDie.BoostedDie(mod['bonus']).roll()
            statMod = stats.StatMod(0, bonus)
            for flag in mod['flags']:
                newItem.stats.addMod(flag, statMod)
        # Calculate any modifiers that were in BoostedDie format.
        newItem.stats.roll(itemLevel)
        
        # Decide which allocatorRule to use based on the level -- we pick
        # the last eligible one.
        if self.allocatorRules:
            allocatorRuleToUse = self.allocatorRules[0]
            for allocatorRule in self.allocatorRules[1:]:
                if allocatorRule.isValidAtItemLevel(itemLevel):
                    allocatorRuleToUse = allocatorRule
            newItem.quantity = allocatorRuleToUse.getQuantity(itemLevel)
        
        # Determine charges (and other variable non-mod properties)
        newItem.charges = self.charges.roll(itemLevel)

        # \todo - Core engine shouldn't know/care about artifacts.
        # Figure a better way to handle.
        # If we're an artifact, mark us as created.
        if self.categories.has("artifact"):
            self.artifactCreated = True
            # Ensure that we have a valid display field
            # \todo Allow colour tuples to overwrite those in templates - issue #7
            if 'color' not in newItem.display['ascii'].keys():
                newItem.display['ascii']['color'] = [128, 128, 128]
        else:
            # Apply any affixes and theme
            self.applyMagic(newItem, lootRules)

        # Generate procs from our proc records.
        newItem.procs = []
        for record in self.procRecords:
            # \todo For now, manually checking for valid procs since all
            # artifact activations are not valid proc records yet.
            if 'name' in record or 'code' in record:
                newItem.procs.append(procs.procLoader.generateProcFromRecord(record, itemLevel))

        # If the nameInfo provides us with a proc name, and the object
        # has specified a noun to define itself, we can create a proc
        # to generate its name.
        if self.nameInfo and 'proc' in self.nameInfo:
            newItem.procs.append(procs.procLoader.getProc(
                                 self.nameInfo['proc'], 'get name', self.nameInfo, None))

        newItem.init(gameMap)

        # If the item starts with other items inside it, create those items
        # now and add them to its inventory.
        # NB there's no checks for recursion here, so don't make items that
        # contain themselves (or contain items that contain this item, etc.)! 
        if 'containerContents' in self.record:
            for typeInfo in self.record['containerContents']:
                subItem = itemLoader.makeItem(typeInfo, itemLevel, gameMap)
                # \todo Defaulting quantity to 1 for now.
                subItem.quantity = 1
                newItem.addItemToInventory(subItem)
        return newItem


    ## Generate a name for this factory instance that 'should'
    #  be unique, and immutable (thus suitable for hashing).
    #  Simple strings get converted to 1-item tuples
    def getFactoryName(self):
        # A factory for a template is defined solely by the template name.
        if self.isTemplate:
            return self.templateName

        # A factory for a named item can be uniquely defined by that name.
        if 'properName' in self.nameInfo:
            return self.nameInfo['properName']

        # Otherwise we construct a tuple of: templates this object
        # was derived from, subtype (the category added by this type),
        # and nameInfo['variantName'].

        tupleList = []
        if isinstance(self.templates, list):
            tupleList.extend(self.templates)
        else:
            tupleList.append(self.templates)
        # Make sure we don't duplicate values
        if self.subtype and self.subtype not in tupleList:
            tupleList.append(self.subtype)
        # Make sure we don't duplicate values
        if 'variantName' in self.nameInfo and self.nameInfo['variantName'] not in tupleList:
            tupleList.append(self.nameInfo['variantName'])

        return tuple(tupleList)


    ## Serialize us. We use the JSON format, but we output keys in a specific
    # order and try to compact things as much as possible without sacrificing
    # legibility.
    def getSerialization(self):
        return util.record.serializeRecord(self.record, FIELD_ORDER)


    ## Compare us against another ItemFactory, for sorting.
    def __cmp__(self, alt):
        return cmp(self.getFactoryName(), alt.getFactoryName())


    ## For debugging purposes, convert to string.
    def __unicode__(self):
        return "<ItemFactory for subtype %s, template %s>" % (self.subtype, self.templateName)

