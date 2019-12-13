import container
import gui
import proc
import procData.element
import procData.spell
import procUtil
import things.stats
import things.synthetics.marker
import things.synthetics.timer
import util.evaluator
import util.fieldOfView
import util.geometry

import numpy
import random

# SpellProcs are just Procs, really; they're in this file to maintain some
# semblance of organization. Procs in this file should deal with magical 
# effects, from spells, items, special attacks, and the like.



## Invoke the effect of a creature spell (c.f. procData/spell.py). 
class CastCreatureSpellProc(proc.Proc):
    def trigger(self, source, gameMap, *args, **kwargs):
        spellName = self.params['spellName']
        # Generate a new dict for the spell data based on our params dict.
        spellData = dict(self.params)
        # Replace the 'name' field with the spell name, since getSpell() relies
        # on that field.
        spellData['name'] = spellName
        del spellData['spellName']
        # Remove the 'code' field since that should be provided by the Spell
        # instance.
        del spellData['code']
        # Ensure we have a valid target, if needed.
        if procData.spell.getNeedsTarget(spellData) and source.curTarget is None:
            source.curTarget = gui.prompt.resolvePrompt(gui.prompt.TargetPrompt())
        # \todo For now setting level = 0. 
        # We don't update recall because we assume that anyone using this
        # Proc is not a creature casting a spell. 
        procData.spell.castSpell(spellData, source, 0, gameMap, 
                altTarget = source.curTarget, shouldUpdateRecall = False)
        


## Fire a projectile that explodes when it hits the target.
class ExplosiveProjectileProc(proc.Proc):
    def trigger(self, source, target, level, gameMap, *args, **kwargs):
        element = procData.element.getElement(self.params['element'])
        damage = util.evaluator.run(self.params['damage'], 
                {'level': level, 'hp': source.curHitpoints})
        radius = util.evaluator.run(self.params['radius'], 
                {'level': level, 'hp': source.curHitpoints, 'damage': damage})
        radius = int(radius)
        path = util.geometry.getLineBetween(source.pos, target.pos)
        # The path may be interrupted by an obstruction, so walk along it and
        # see what we hit.
        finalTile = path[-1]
        # Skip the first tile, which contains us and is thus always valid.
        for i, tile in enumerate(path[1:]):
            blockers = gameMap.filterContainer(
                    gameMap.getContainer(tile), container.BLOCKERS)
            if blockers:
                # Found the true end of the path.
                finalTile = tile
                break
        # Figure out what tiles are hit by the explosion.
        affectedTiles = []
        blockedMap = gameMap.getAccessibilityMap(container.BLOCKERS)
        util.fieldOfView.setFieldOfView(blockedMap, finalTile, radius,
                lambda x, y: affectedTiles.append((x, y)))
        gui.animation.drawExplosiveProjectile(source.pos, finalTile, 
                affectedTiles, element.display)
        # Deal damage to any creatures in the affected tiles; potentially
        # destroy items on the floor.
        for tile in affectedTiles:
            tileContents = gameMap.getContainer(tile)
            for target in gameMap.filterContainer(
                    tileContents, container.CREATURES):
                # No damaging yourself with your own explosion.
                if target is not source:
                    procUtil.dealDamage(target, gameMap, source, damage, element)
            for item in gameMap.filterContainer(
                    tileContents, container.ITEMS):
                procUtil.destroyItemWithElement(item, element, gameMap)



## Teleport the target a short distance away.
class PhaseDoorProc(proc.Proc):
    def trigger(self, target, gameMap, **kwargs):
        # Get all locations that are between 4 and 10 spaces away.
        validSpaces = []
        for cellPos in util.geometry.generateSpiral(*target.pos):
            distance = util.geometry.gridDistance(target.pos, cellPos)
            if distance > 10:
                # All points from here out are too far away.
                break
            if distance < 4 or not gameMap.getIsInBounds(cellPos):
                # Not a valid cell.
                continue

            contents = gameMap.getContainer(cellPos)
            if not (gameMap.filterContainer(contents, container.BLOCKERS) or
                    gameMap.filterContainer(contents, container.CREATURES)):
                validSpaces.append(cellPos)
        gameMap.moveMe(target, target.pos, random.choice(validSpaces))



## Fire a projectile that deals damage when it hits the target (if any).
class ProjectileProc(proc.Proc):
    def trigger(self, source, target, level, gameMap, *args, **kwargs):
        element = procData.element.getElement(self.params['element'])
        damage = util.evaluator.run(self.params['damage'], {'level': level})
        path = util.geometry.getLineBetween(source.pos, target.pos)
        # The path may be interrupted by an obstruction, so walk along it and
        # see what we hit.
        finalTile = path[-1]
        # Skip the first tile, which contains us and is thus always valid.
        for i, tile in enumerate(path[1:]):
            blockers = gameMap.filterContainer(
                    gameMap.getContainer(tile), container.BLOCKERS)
            if blockers:
                # Found the true end of the path.
                finalTile = tile
                break
        gui.animation.drawProjectile(source.pos, finalTile, element.display)
        # Deal damage to any creatures in that tile.
        for target in gameMap.filterContainer(
                gameMap.getContainer(finalTile), container.CREATURES):
            # No damaging yourself with your own projectile.
            if target is not source:
                procUtil.dealDamage(target, gameMap, source, damage, element)
      


## Permanently swap some stats of the target.
class SwapStatsProc(proc.Proc):
    def trigger(self, target, gameMap, *args, **kwargs):
        options = set(['STR', 'INT', 'WIS', 'DEX', 'CON'])
        first = random.choice(options)
        options.remove(first)
        second = random.choice(options)
        targetStats = target.getStats()
        firstMod = targetStats.getModWithName('fundamental %s' % first)
        firstMod.addend -= 3
        secondMod = targetStats.getModWithName('fundamental %s' % second)
        secondMod.addend += 3



## Teleport the target to a random location that isn't close to their current
# location, nor to the "landing sites" of previous teleport attempts. We pick
# a random location near the edge of the map until we get a good result.
class TeleportAwayProc(proc.Proc):
    def trigger(self, source, target, gameMap, *args, **kwargs):
        recentTargets = gameMap.getContainer('Teleportation targets')
        recentTargets = sorted(recentTargets, key = lambda m: m.age)
        if len(recentTargets) >= 8:
            # Remove the oldest marker.
            gameMap.removeSubscriber(recentTargets[-1], 'Teleportation targets')
        # Add a new marker for our position.
        marker = things.synthetics.marker.Marker(target.pos, gameMap)
        gameMap.addSubscriber(marker, 'Teleportation targets')
        recentTargets.append(marker)
        
        width, height = gameMap.getDimensions()
        for i in xrange(1000):
            xVals = random.choice([(2, 22), (width - 22, width - 2)])
            yVals = random.choice([(2, 22), (height - 22, height - 2)])
            x = random.randint(*xVals)
            y = random.randint(*yVals)
            contents = gameMap.getContainer((x, y))
            if (gameMap.filterContainer(contents, container.BLOCKERS) or 
                    gameMap.filterContainer(contents, container.CREATURES)):
                # Invalid teleportation target
                continue
            isValid = True
            for marker in recentTargets:
                if util.geometry.distanceSquared(marker.pos, (x, y)) < 225:
                    # Within 15 squares of the marker; invalid location.
                    isValid = False
                    break
            if isValid:
                # Teleport the target to the location.
                gameMap.moveMe(target, target.pos, (x, y))
                break



## Send the target to an open space close to the source.
class TeleportToProc(proc.Proc):
    def trigger(self, source, target, gameMap, *args, **kwargs):
        # Find an open space near to the source that the target can be 
        # moved to. We want to move to the closest space to the target, but
        # if multiple options are available that are the same distance, we
        # want to select a random one from the options.
        validSpaces = []
        for space in util.geometry.generateSpiral(*source.pos):
            # Check for termination: we have valid spaces and this space is
            # further away than any of them, or we're too far away from
            # source.
            sourceDistance = util.geometry.gridDistance(source.pos, space)
            if (sourceDistance > 5) or (validSpaces and 
                    sourceDistance > util.geometry.gridDistance(source.pos, validSpaces[0])):
                break
            contents = gameMap.getContainer(space)
            if (gameMap.filterContainer(contents, container.BLOCKERS) or 
                    gameMap.filterContainer(contents, container.CREATURES)):
                # Space is blocked; cannot use.
                continue
            # Space is free.
            validSpaces.append(space)
        # Move to a random available space.
        if validSpaces:
            gameMap.moveMe(target, target.pos, random.choice(validSpaces))



## Apply a temporary stat modifier to the target.
class TemporaryStatModProc(proc.Proc):
    def trigger(self, target, gameMap, *args, **kwargs):
        # \todo Allow scaled durations based on level -- what exactly should
        # level be?
        procUtil.addTimeredStat(target, gameMap, 
                self.params['statName'], 
                util.boostedDie.roll(self.params['duration']), 
                self.params.get('modAmount', 1),
                self.params.get('modFactor', 0),
                self.params.get('stackMode', 'reset'))



## Apply a temporary status effect to the target.
class TemporaryStatusEffectProc(proc.Proc):
    def trigger(self, target, gameMap, **kwargs):
        procData.status.applyStatus(self.params['status'], target, gameMap, 
            util.boostedDie.roll(self.params['duration']),
            stackMode = self.params['stackMode'])

