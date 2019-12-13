import container
import gui
import proc
import procData.spell
import procLoader
import things.creatures.creatureLoader
import util.geometry

import random

# AI Procs handle AI, naturally. They are responsible for state
# modifications to autonomous actors (creatures, sentient items, etc.). In
# practice they behave like baseline Procs.



class BasicAIProc(proc.Proc):
    ## Update the creature's state. Cast a spell, or move towards the player,
    # or (if already in melee range) make a melee attack.
    def trigger(self, creature, gameMap, **kwargs):
        # Assuming a single player.
        player = gameMap.getContainer(container.PLAYERS)[0]
        record = things.creatures.creatureLoader.getRecordForCreature(creature)
        # Check for spellcasting -- only if the player can see the creature's
        # tile.
        if (player.canSee(creature.pos) and 'magic' in record and 
                random.randint(0, record['magic']['frequency'] - 1) == 0):
                # Cast a spell. 
                self.castSpell(creature, gameMap, player, record['magic'])
        else:
            # Move towards the player, or attack in melee.
            # Check for adjacency
            if util.geometry.gridDistance(creature.pos, player.pos) <= 1:
                # Attack the player.
                creature.meleeAttack(player)
            else:
                # Find an adjacent cell that takes us closer to the player.
                heatMap = player.getHeatMap()
                bestDistance = heatMap[creature.pos]
                bestNeighbor = None
                for x, y in util.geometry.getAdjacent(*creature.pos, 
                        grid = heatMap):
                    if heatMap[x, y] == -1:
                        # This cell is inaccessible; skip it.
                        continue
                    if (bestDistance == -1 or 
                            heatMap[x, y] <= bestDistance):
                        # Found a square we can move to that takes us closer, 
                        # or is at least equivalent (so we don't stand still).
                        # \todo Randomly select from equally-good choices.
                        bestDistance = heatMap[x, y]
                        bestNeighbor = (x, y)
                if bestNeighbor is not None:
                    gameMap.moveMe(creature, creature.pos, bestNeighbor)
        creature.addEnergy(-1)


    ## Cast a spell. We select a spell at random, determine targeting 
    # (either the creature, or the player), and invoke the spell's proc.
    # \param record The "magic" subsection of the creature record. 
    def castSpell(self, creature, gameMap, player, record):
        if 'spells' not in record:
            raise RuntimeError("%s tried to use magic but has no spells." % str(creature))
        spellName = record['spells']
        # The record can have either a single spell, or a list of spells. 
        if isinstance(spellName, list):
            spellName = random.choice(spellName)
        procData.spell.castSpell(spellName, creature, creature.nativeDepth, 
                gameMap, player, shouldUpdateRecall = True)



## This proc handles basic status updates that all creatures do. Mostly this
# involves checking for damage-over-time effects and the like.
class BasicStatusUpdateProc(proc.Proc):
    def trigger(self, creature, gameMap, **kwargs):
        stats = creature.getStats()
        canRegenerate = True
        for key, divisor in [('poison', 50), ('cut', 10)]:
            val = stats.getStatValue(key)
            if val:
                # Creature has a damage-over-time effect that also nulls regen.
                canRegenerate = False
                creature.curHitpoints -= val / divisor + 1

        if canRegenerate:
            # Creature regains some amount of hitpoints. By default,
            # regen .1% of max HP/turn, or .1HP/turn, whichever is higher.
            maxHP = stats.getStatValue('maxHitpoints')
            regenRate = stats.getStatValue('regeneration') + max(.1, maxHP / 1000.0)
            creature.curHitpoints = min(maxHP, creature.curHitpoints + regenRate)


