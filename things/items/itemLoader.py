## Load item records from object.txt and object_template.txt, and create
# ItemFactories for them.

import allocatorRules
import itemFactory
import affix
import loot
import util.record
import util.extend
import theme

import copy
import json
import os


## A list of the major item types
ITEM_TYPES = []
## A map from major item types to the subtypes available for each major type
# Lazily constructed.
ITEM_SUBTYPE_MAP = dict()
## A list of all the artifacts
ARTIFACTS = []

## Maps (type, subtype) tuples, or artifact names, to the factories
# needed to instantiate them.
ITEM_FACTORY_MAP = dict()


## Directly access the factory with the given tuple or name
def getFactory(key):
    # Paranoia
    if isinstance(key, list):
        key = tuple(key)
    if key not in ITEM_FACTORY_MAP:
        raise RuntimeError("Invalid item tuple or artifact name: %s" % unicode(key))
    return ITEM_FACTORY_MAP[key]


## Instantiate an Item, rolling all necessary dice to randomize it.
def makeItem(key, itemLevel, gameMap, pos = None):
    factory = getFactory(key)
    return factory.makeItem(itemLevel, gameMap, pos)


## Get a list of the item types, and cache it for future calls
def getTypes():
    global ITEM_TYPES
    if not ITEM_TYPES:
        uniqueTypes = set()
        for key in ITEM_FACTORY_MAP:
            if type(key) == tuple:
                itemType = key[0]
                uniqueTypes.add(itemType)
        ITEM_TYPES = list(uniqueTypes)
    return ITEM_TYPES


## Get a list of the available subtypes for a particular major type
# and cache the result for later use.
def getSubTypes(itemType):
    if not itemType in ITEM_SUBTYPE_MAP:
        ITEM_SUBTYPE_MAP[itemType] = []
        for key in ITEM_FACTORY_MAP:
            if type(key) is tuple and key[0] == itemType:
                ITEM_SUBTYPE_MAP[itemType].extend(key[1])
    return ITEM_SUBTYPE_MAP[itemType]


## Get a list of all the artifact keys.
# Check each item factory for 'artifact' in its categories.
# \todo - Core engine shouldn't know/care about artifacts.
# Do not include templates.
def getArtifacts():
    global ARTIFACTS
    if not ARTIFACTS:
        ARTIFACTS = [key for key, factory in ITEM_FACTORY_MAP.iteritems()
                     if factory.categories.has('artifact') and not factory.isTemplate]
    return ARTIFACTS


## Maps template names to the factories that can apply them.
TEMPLATE_NAME_MAP = dict()
def getItemTemplate(name):
    if name not in TEMPLATE_NAME_MAP:
        raise RuntimeError("Invalid item template: [%s]" % str(name))
    return TEMPLATE_NAME_MAP[name]


## Maps affix names to the objects that can apply them.
AFFIX_NAME_MAP = dict()
def getAffix(name):
    if name not in AFFIX_NAME_MAP:
        raise RuntimeError("Invalid item affix: [%s]" % str(name))
    return AFFIX_NAME_MAP[name]


## Request a specific affix type
AFFIX_LEVELS = dict()
AFFIX_TYPES = dict()
def getAffixType(key):
    if key not in AFFIX_TYPES:
        raise RuntimeError("Invalid item key %s" % unicode(key))
    return AFFIX_TYPES[key]


## Maps theme names to the objects that can apply them.
THEME_NAME_MAP = dict()
def getTheme(name):
    if name not in THEME_NAME_MAP:
        raise RuntimeError("Invalid item theme: [%s]" % str(name))
    return THEME_NAME_MAP[name]


## Maps loot template names to the factories that can apply them.
LOOT_TEMPLATE_MAP = dict()
def getLootTemplate(name):
    if name not in LOOT_TEMPLATE_MAP:
        raise RuntimeError("Invalid loot template: [%s]" % str(name))
    # Return a copy of the template to allow resolution of formulae
    return copy.deepcopy(LOOT_TEMPLATE_MAP[name])


## Returns affix minima and maxima for a given itemLevel, with caching
AFFIX_LIMITS = dict()
def getAffixLimits(itemLevel):
    # Check if we have already cached the results for this itemLevel
    if itemLevel not in AFFIX_LIMITS:
        AFFIX_LIMITS[itemLevel] = dict()
        AFFIX_LIMITS[itemLevel]['levelsMin'] = dict()
        AFFIX_LIMITS[itemLevel]['levelsMax'] = dict()
        AFFIX_LIMITS[itemLevel]['typesMin'] = dict()
        AFFIX_LIMITS[itemLevel]['typesMax'] = dict()
        # Iterate over all affix levels, check whether any have minima or
        # maxima at this itemLevel
        for key, level in AFFIX_LEVELS.iteritems():
            for allocatorRule in level['allocatorRules']:
                # Note that -1 means "no maximum"
                if (itemLevel >= allocatorRule['minDepth'] and
                        (itemLevel <= allocatorRule['maxDepth'] or
                        allocatorRule['maxDepth'] is -1)):
                    # 0 is irrelevant as a minimum so we ignore it ...
                    if allocatorRule['minNum'] > 0:
                        AFFIX_LIMITS[itemLevel]['levelsMin'][key] = allocatorRule['minNum']
                    # ... but it's a relevant maximum, so we don't
                    if allocatorRule['maxNum'] >= 0:
                        AFFIX_LIMITS[itemLevel]['levelsMax'][key] = allocatorRule['minNum']
        # Now do the same for affix types
        for key, affixType in AFFIX_TYPES.iteritems():
            for allocatorRule in affixType['allocatorRules']:
                if (itemLevel >= allocatorRule['minDepth'] and
                        (itemLevel <= allocatorRule['maxDepth'] or
                        allocatorRule['maxDepth'] is -1)):
                    if allocatorRule['minNum'] > 0:
                        AFFIX_LIMITS[itemLevel]['typesMin'][key] = allocatorRule['minNum']
                    if allocatorRule['maxNum'] >= 0:
                        AFFIX_LIMITS[itemLevel]['typesMax'][key] = allocatorRule['maxNum']
    # Return a copy so the caller can modify without affecting the cache
    return allocatorRules.AffixLimits(AFFIX_LIMITS[itemLevel])


## Load the data files we need.
def loadFiles():
    ## First load templates, so they're available when we load objects.
    #  loadRecords yields an iterable list so that templates can
    #  refer to previously completed templates.
    for templateFactory in util.record.loadRecords(
            os.path.join('data', 'object', 'object_template.txt'),
            itemFactory.ItemFactory):
        TEMPLATE_NAME_MAP[templateFactory.getFactoryName()] = templateFactory

    # Now load the object records.
    for objectFactory in util.record.loadRecords(
            os.path.join('data', 'object', 'object.txt'),
            itemFactory.ItemFactory):
        ITEM_FACTORY_MAP[objectFactory.getFactoryName()] = objectFactory

    # Load the object flag metadata.
    OBJECT_FLAGS = json.load(open(os.path.join('data', 'object',
            'object_flags.txt')))

    # Load the affix metadata.
    global AFFIX_LEVELS
    global AFFIX_TYPES
    AFFIX_LEVELS, AFFIX_TYPES = json.load(open(os.path.join('data', 'object',
            'affix_meta.txt')))

    # Now load the affixes.
    for newAffix in util.record.loadRecords(
            os.path.join('data', 'object', 'affix.txt'), affix.Affix):
        AFFIX_NAME_MAP[newAffix.name] = newAffix

    # Now load the themes.
    for newTheme in util.record.loadRecords(
            os.path.join('data', 'object', 'theme.txt'), theme.Theme):
        THEME_NAME_MAP[newTheme.name] = newTheme

    # Now load the artifacts, adding them to the base item map by name
    for artifactFactory in util.record.loadRecords(
            os.path.join('data', 'object', 'artifact.txt'), 
            itemFactory.ItemFactory):
        ITEM_FACTORY_MAP[artifactFactory.getFactoryName()] = artifactFactory

    # Load the loot templates.
    for lootTemplate in util.record.loadRecords(
            os.path.join('data', 'object', 'loot_template.txt'), 
            loot.LootTemplate):
        LOOT_TEMPLATE_MAP[lootTemplate.templateName] = lootTemplate

