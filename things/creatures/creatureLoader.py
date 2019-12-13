## Load the creature_template.txt and creature.txt files.

import creatureFactory
import util.record

import json
import os
import re


## Maps creature name to a factory for that creature.
CREATURE_MAP = dict()
## Generate a creature of the given name at the specified position.
def makeCreature(name, gameMap, pos):
    if name not in CREATURE_MAP:
        raise RuntimeError("Invalid creature name %s" % name)
    CREATURE_MAP[name].makeCreature(gameMap, pos)


## Directly access the factory with the given name.
def getFactory(name, isCaseSensitive = True):
    if isCaseSensitive:
        return CREATURE_MAP.get(name, None)
    # Must scan through the entries manually to do case-insensitive matches.
    name = name.lower()
    for key, val in CREATURE_MAP.iteritems():
        if name == key.lower():
            return val
    # No match
    return None


## Retrieve the appropriate data record for the given creature.
def getRecordForCreature(creature):
    if creature.name not in CREATURE_MAP:
        raise RuntimeError("Invalid creature name %s" % name)
    return CREATURE_MAP[creature.name].record


## Retrieve all available CreatureFactories.
def getAllFactories():
    return CREATURE_MAP.values()


## Maps template names to CreatureFactory instances.
TEMPLATE_NAME_MAP = dict()
## Retrieve the appropriately-named template, or None if it doesn't exist.
def getTemplate(label):
    if label not in TEMPLATE_NAME_MAP:
        raise RuntimeError("Invalid creature template name %s" % label)
    return TEMPLATE_NAME_MAP[label]


## Load our data files.
def loadFiles():
    # First load the creature templates, because they'll be needed when we 
    # load the actual creatures.
    templates = util.record.loadRecords(
            os.path.join('data', 'creature_template.txt'), 
            creatureFactory.CreatureFactory)
    for template in templates:
        TEMPLATE_NAME_MAP[template.name] = template

    # Now load the creatures themselves.
    creatures = util.record.loadRecords(
            os.path.join('data', 'creature.txt'), 
            creatureFactory.CreatureFactory)
    for creature in creatures:
        CREATURE_MAP[creature.name] = creature

