import container
import gui
import things.mixins.carrier
import util

import collections
import random
import string

## This module contains utility functions that many Procs will want to refer
# to. 


## Deal damage to the target. Check for resistance to the element (if 
# element is None, then deal physical damage). Apply any secondary effects
# associated with the element. Teach the source of the damage about any 
# resistances the target may have. 
# Return the actual damage dealt, as modified by resistances and procs.
def dealDamage(target, gameMap, source, damage, element = None):
    if target.curHitpoints < 0:
        # Target is already dead; do nothing.
        return 0
    stats = target.getStats()
    hasResistance = False
    if element is None:
        # Subtract off absorption from armor.
        absorption = stats.getStatValue('absorption')
        damage -= absorption
        # Record knowledge of absorption.
        source.setKnowledge(('creature', target.name, 'absorption'),
                absorption)
    else:
        damageFactor = element.getDamageFactor(target)
        hasResistance = damageFactor < 1
        damage *= damageFactor
        # Record knowledge of resistance.
        source.setKnowledge(('creature', target.name, 
                'resist %s' % element.name), hasResistance)

    if element is not None and not hasResistance:
        # Follow up with additional effects due to the element used.
        damage = element.applyProcs(target, damage, gameMap)
    
    damage = int(damage)
    target.curHitpoints -= damage
    if target.curHitpoints < 0:
        target.die(source)
        # If the player is the killer, and can see what they did, record the
        # kill in their memory.
        # \todo This means that normal creatures don't record their kills since
        # they don't have canSee().
        player = gameMap.getContainer(container.PLAYERS)[0]
        if source is player and player.canSee(target.pos):
            player.incrementKnowledge('creature', target.name, 'kills')

    if element is not None:
        # Damage any items the target is carrying.
        damageItems(target, gameMap, damage, element)
    return damage


## Damage any items the target is carrying in their inventory.
def damageItems(target, gameMap, damage, element):
    if target not in gameMap.getContainer(container.CARRIERS):
        # Target has no inventory.
        return
    # Target has an inventory; damage its contents.
    # Get the entire list at the start so we don't have to worry about
    # destroying the contents as we iterate over them.
    itemChains = [i for i in things.mixins.carrier.generateItemList(
            target.inventory, shouldIgnoreOpenness = True)]
    for itemChain in itemChains:
        item = itemChain[-1]
        if not isItemVulnerableToElement(item, element):
            continue
        # \todo For now each item has a flat 20% chance of destruction.
        numDestroyed = sum(
                [random.randint(0, 4) == 0 for i in xrange(item.quantity)])
        if numDestroyed:
            verb = ['were', 'was'][numDestroyed == 1]
            gui.messenger.message(getDestructionString(item, numDestroyed))
            item.quantity -= numDestroyed
            if item.quantity == 0:
                # Item has been completely destroyed.
                # \todo Should we provide a different message in this case?
                target.removeItemFromInventory(item)
                gameMap.destroy(item)


## Destroy the specified item with the provided element, if applicable.
def destroyItemWithElement(item, element, gameMap):
    if isItemVulnerableToElement(item, element):
        gui.messenger.message(getDestructionString(item))
        gameMap.destroy(item)


## Generate a string for destroying the specified number of the given item.
def getDestructionString(item, numDestroyed = None):
    if numDestroyed is None:
        numDestroyed = item.quantity
    verb = ['were', 'was'][numDestroyed == 1]
    return "%s %s destroyed!" % (string.capitalize(item.getShortDescription(numDestroyed)), verb)


## An item is vulnerable to an element if it has the "damaged by X" flag
# and doesn't have the "ignores X" flag or the "indestructible" flag. 
def isItemVulnerableToElement(item, element):
    return (item.getStat('damaged by %s' % element.name) and 
            not item.getStat('ignores %s' % element.name) and
            not item.getStat('indestructible'))



## Represents the result of calling addTimeredStat, below.
TimeredStatResult = collections.namedtuple('TimeredStatResult', 
        ['didStart', 'didStack', 'timer'])

## Add a temporary stat modifier to the target, or stack with an existing
# modifier if it's already there. 
# Depending on the value of the stackMode parameter, we can combine with
# existing temporary stat modifiers in different ways:
# - "stack": add our duration to the existing duration.
# - "reset": reset to our duration (if greater than the existing duration).
# - "multiple": multiple stat modifiers of this type can exist simultaneously.
# - "ignore": don't do anything if a previous stat mod already exists.
# \param modAmount Addend to apply to the stat.
# \param modFactor Multiplicative factor to apply to the stat.
# Return a tuple of booleans: (did we create a new StatMod, did we extend an
# existing StatMod).
def addTimeredStat(target, gameMap, statName, duration, modAmount = 0,
        modFactor = 0, stackMode = 'reset'):
    # Check if the target already has this stat modifier.
    modName = "temporary %s %s" % (statName, ['penalty', 'bonus'][modAmount > 0])
    timerId = "%s for %s" % (modName, target.id)
    oldMod = target.getStats().getModWithName(modName)
    if oldMod is not None and stackMode != 'multiple':
        if stackMode == 'ignore': 
            # Nothing to do.
            return TimeredStatResult(False, False, None)
        # Find the existing timer for when this statmod wears out, and
        # tweak its duration.
        timer = gameMap.getThingWithName(timerId)
        if timer is not None:
            if stackMode == 'reset':
                if timer.duration < duration:
                    timer.setDuration(duration)
                    return TimeredStatResult(False, True, timer)
                return TimeredStatResult(False, False, timer)
            else:
                timer.duration += duration
                return TimeredStatResult(False, True, timer)

    # Otherwise we create a new StatMod and associated timer.
    # \todo Picking an arbitrary high tier here (the 100).
    newMod = things.stats.StatMod(100, addend = modAmount, 
            multiplier = modFactor, name = modName)
    target.addStatMod(statName, newMod)
    # Ask the game to call us back when we expire, so we can remove the 
    # modifier we created.
    timer = things.synthetics.timer.Timer(gameMap, duration,
            target.getStats().removeMod, (statName, newMod), 
            name = timerId)
    # Register our timer so that its duration can be modified by other
    # Procs later, if necessary.
    if stackMode != 'multiple':
        gameMap.registerThingByName(timer)
    return TimeredStatResult(True, False, timer)


## Display a formatted message string of an action done by an creature
# (e.g. "The Filthy street urchin is confused."). 
# \param text A list of message formatting strings, e.g. 
#        ["{verb} confused", "are"]
# \param target The creature performing the action.
def showCreatureMessage(text, gameMap, target):
    message = util.grammar.getConjugatedPhrase(
        "{creature} %s" % text[0], gameMap, target, text[1])
    gui.messenger.message(message)
