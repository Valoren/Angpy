import container
import gui
import proc
import procData.element
import procData.status
import procLoader
import procUtil
import things.creatures.creatureAllocator
import things.mixins.equipper
import things.stats
import util.boostedDie
import util.randomizer

import random

# Damage procs are procs that deal with causing damage or the consequences
# thereof.



## Handles attacks by creatures with their natural weapons. Compare
# WeaponAttackProc later in this module.
class CreatureAttackProc(proc.Proc):
    def trigger(self, source, target, gameMap, **kwargs):
        blows = []
        totalDamage = 0
        player = gameMap.getContainer(container.PLAYERS)[0]
        canPlayerSee = player.canSee(source.pos)
        for i, blow in enumerate(source.blows):
            # Check if attack hits.
            if not didMeleeHit(source, target):
                blows.append('miss')
                continue
            # Calculate damage if any.
            damRoll = blow.get('damage', '')
            damage = util.boostedDie.roll(damRoll, source.nativeDepth)
            element = blow.get('element', None)
            if element is not None:
                element = procData.element.getElement(element)
            trueDamage = procUtil.dealDamage(target, gameMap, source, damage,
                    element)
            totalDamage += trueDamage
            if element is not None:
                blows.append("%s %s %s" % (element.name, blow['verb'], damage))
            else:
                blows.append("%s %s" % (blow['verb'], damage))
            # Invoke any procs. Since most procs haven't been implemented
            # yet, this is a bit more failsafe than usual.
            if 'proc' in blow:
                try:
                    proc = procLoader.generateProcFromRecord(blow['proc'])
                    proc.trigger(source = source, target = target, 
                            damage = trueDamage, element = element, 
                            gameMap = gameMap)
                except Exception, e:
                    print "Failed to do proc [%s]: %s" % (blow['proc'], e)
            # Update player memory, if they can see the attacker. Note the 
            # player remembers the initial damage, as unmodified by 
            # procUtil.dealDamage.
            if canPlayerSee:
                player.setKnowledgeRange(('creature', source.name, 'blows', i),
                        damage)
        if canPlayerSee:
            phrase = '{creature} {verb} {creature} (%d) [%s].' % (totalDamage, ', '.join(blows))
            gui.messenger.message(
                    util.grammar.getConjugatedPhrase(phrase, 
                        gameMap, source, 'attack', target)
            )


## Reduce the effectiveness of equipment.
class DamageEquipmentProc(proc.Proc):
    def trigger(self, target, damage, element, gameMap, **kwargs):
        if not isinstance(target, things.mixins.equipper.Equipper):
            # Target has no equipment to damage.
            return
        # Select an item to damage, based on the equipment slots we can
        # affect.
        potentialTargets = []
        for desc, slot in target.equipDescToSlot.iteritems():
            if slot in self.params['validSlots']:
                if desc in target.equipment:
                    potentialTargets.append(target.equipment[desc])
                else:
                    # Dummy slot; if we hit it nothing happens.
                    potentialTargets.append(None)
        # Select a random item to damage.
        targetItem = random.choice(potentialTargets)
        if targetItem is None:
            # Nothing happens
            return

        # Select a stat to damage on the item.
        damagedStat = self.params['damagedStats']
        if isinstance(damagedStat, list):
            # Have multiple to choose from.
            damageStat = random.choice(damagedStat)

        # Damage the item; permanently reduce a stat. Only if the item is
        # normally vulnerable to that damage type, doesn't ignore it, and
        # the penalty doesn't exceed the capStat or minValue if any.
        itemStats = targetItem.getStats()
        minValue = self.params.get('minValue', None)
        cap = None
        if 'capStat' in self.params:
            cap = itemStats.getStatValue(self.params['capStat'])
        if procUtil.isItemVulnerableToElement(targetItem, element):
            curValue = itemStats.getStatValue(damagedStat)
            if cap is None or (-curValue < cap and curValue > minValue):
                # Modify an existing mod if one exists.
                name = 'Damage from %s' % element.name
                mod = itemStats.getModWithName(name)
                if mod is None:
                    mod = things.stats.StatMod(0, id = id)
                    itemStats.addMod(self.params['damagedStat'], mod)
                mod.addend += self.params.get('damageAmount', -1)
                # Damaging the item reduces the damage the target receives.
                damage *= self.params.get('HPDamageMultiplier', 1)
                gui.messenger.message("%s %s" % (targetItem.getShortDescription(), self.params['message']))
            # Else: item is vulnerable but cannot be further damaged; 
            # nothing happens.
        else:
            # Hitting an impossible-to-damage item also reduces damage received.
            damage *= self.params.get('HPDamageMultiplier', 1)
            if 'failMessage' in self.params:
                gui.messenger.message("%s %s" % (targetItem.getShortDescription(), self.params['failMessage']))
        return damage



## Apply a timered status effect to the target, based on the amount of damage
# dealt.
class DamageStatusProc(proc.Proc):
    def trigger(self, target, damage, element, gameMap, **kwargs):
        duration = damage / self.params.get('divisor', 1)
        procData.status.applyStatus(self.params['status'], target, gameMap, 
                duration, self.params.get('modAmount', 1), 
                self.params.get('modFactor', 0), 
                self.params.get('stackMode', 'reset'))
           


## Transform creatures into different creatures.
class PolymorphProc(proc.Proc):
    def trigger(self, target, damage, element, gameMap, **kwargs):
        player = gameMap.getContainer(container.PLAYERS)[0]
        if target is player:
            # No polymorphing the player.
            return
        # Check if target is unique; no polymorphing unique creatures.
        if target.categories.has('unique'):
            return
        # Remove the old creature.
        gameMap.destroy(target)
        # Select a new non-unique creature of a similar level.
        allocator = things.creatures.creatureAllocator.CreatureAllocator(target.nativeDepth, 
                [lambda factory: not factory.categories.has('unique')])
        allocator.allocate(gameMap, target.pos)
        if 'message' in self.params:
            message = util.grammar.getConjugatedPhrase(
                    '{creature} %s' % self.params['message'], gameMap, target)
            gui.messenger.message(message)



## Handle attacks using equipped weapons.
class WeaponAttackProc(proc.Proc):
    def trigger(self, source, target, gameMap, **kwargs):
        weapons = source.getItemsInSlotsOfType('weapon')
        # List of attack descriptors, e.g. "hit 16", "miss", "smite 45", etc.
        blows = []
        numBlows = 1
        totalDamage = 0
        # Automatically learn target evasion.
        source.setKnowledge(('creature', target.name, 'evasion'),
                target.getStat('evasion'))
        if not weapons:
            # Deal a single damage with a punch.
            # \todo Should punching be useful? It's not, under these rules.
            if didMeleeHit(source, target):
                blows.append('punch 1')
                totalDamage = 1
        else:
            # \todo Handle multi-weapon combat; what should the energy costs be?
            weapon = weapons[0]
            balance = weapon.getStat('balance')
            heft = weapon.getStat('heft')
            # Calculate number of blows, as weapon balance * creature finesse.
            numBlows = 1 + balance * source.getStat('weaponFinesse') / 10
            # Calculate blow multiplier, as weapon heft * creature prowess.
            blowMultiplier = 1 + heft * source.getStat('weaponProwess') / 10
            # Add on the biggest relevant slay or elemental brand, if any. 
            # These can modify the verb used to describe the attack.
            verb = 'hit'
            bestSlay = 0
            for category in target.categories:
                bestSlay = max(bestSlay, source.getStat('slay %s' % category))
            if bestSlay:
                verb = 'smite'
            # Check for elemental brands.
            damageElement = None
            # Record all brands this weapon has so later, if we hit, we can
            # record the target's resistances in the player's memory.
            allBrands = []
            for element in procData.element.getAllElements():
                brand = source.getStat('%s brand' % element.name)
                # Allow for resistance/immunity/vulnerability.
                damageFactor = element.getDamageFactor(target)
                if brand != 0:
                    allBrands.append((element, damageFactor < 1))
                brand *= damageFactor
                if brand > bestSlay:
                    bestSlay = brand
                    verb = element.verb
                    damageElement = element

            blowMultiplier += bestSlay
            
            # Generate per-blow damage. We stop as soon as the target dies, or
            # we run out of blows, whichever comes first.
            numDice = weapon.getStat('numDice')
            dieSize = weapon.getStat('dieSize')
            for i in xrange(int(numBlows)):
                if not didMeleeHit(source, target, weapon):
                    # Attack missed.
                    blows.append('miss')
                    continue
                # Check for critical hits. 
                numCrits = 0
                while util.randomizer.oneIn(1.5 / (balance * heft)):
                    numCrits += 1
                damage = sum([random.randint(1, dieSize) for j in xrange(numDice)])
                damage *= blowMultiplier * (numCrits + 1)
                if damageElement is not None:
                    # The bonus damage is elemental; the rest is physical.
                    elementalDamage = damage / blowMultiplier * bestSlay
                    standardDamage = damage - elementalDamage
                    # Adjust our reported values based on what dealDamage
                    # says was actually applied.
                    elementalDamage = procUtil.dealDamage(target, gameMap, 
                            source, elementalDamage, 
                            element = damageElement)
                    standardDamage = procUtil.dealDamage(target, gameMap, 
                            source, standardDamage)
                    damage = elementalDamage + standardDamage
                else:
                    # All damage is physical.
                    procUtil.dealDamage(target, gameMap, source, damage)

                # Record knowledge of target resistances, whether or not they
                # affected damage dealt.
                for (element, hasResistance) in allBrands:
                    source.setKnowledge(('creature', target.name, 'resist %s' % element.name),
                        hasResistance)
                blows.append("%s%s %d" % (verb, '!' * numCrits, damage))
                totalDamage += damage
                if target.curHitpoints < 0:
                    # Target is dead; stop attacking it.
                    break
        player = gameMap.getPlayer()
        if player.canSee(source.pos):
            phrase = '{creature} {verb} {creature} (%d) [%s].' % (totalDamage, ', '.join(blows))
            message = util.grammar.getConjugatedPhrase(phrase, 
                    gameMap, source, 'attack', target)
            gui.messenger.message(message)
            if target.curHitpoints < 0:
                message = util.grammar.getConjugatedPhrase(
                        '{creature} {verb} slain {creature}.', 
                        gameMap, source, 'have', target)
                gui.messenger.message(message)

        # Charge energy for each blow we used -- blows use 1 / numBlows
        # energy apiece.
        source.addEnergy(-1 * int(numBlows) / numBlows)



## Utility function: test if the attacker succeeds in its attempt to hit the
# defender.
def didMeleeHit(attacker, defender, weapon = None):
    # Chance of hitting is 75% - target evasion.
    evasion = 25 + defender.getStat('evasion') - attacker.getStat('accuracy')
    return random.randint(0, 100) > evasion
