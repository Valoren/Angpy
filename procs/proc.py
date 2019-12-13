## Procs are, more or less, functions that we invoke at different times in the
# game engine, but which are inserted by the game data. 
# We make classes out of them because they may need to pre-process their 
# arguments (e.g. ensuring that an equipment bonus is consistent).

import gui
import procs.procLoader
import things.stats
import things.synthetics.timer
import things.terrain.terrainLoader
import util.boostedDie
import util.grammar
import util.id
import util.randomizer
import util.serializer

import random


## A Proc is a bit of code that can be invoked at specific trigger conditions,
# as specified by some entity defined in the data files. In other words, when
# the game engine reaches certain conditions (e.g. an item is used, or a 
# monster is hit), the relevant entities are consulted to see if they have
# any Procs associated with the condition. If they do, those Procs are invoked.
class Proc:
    ## Create the Proc. In addition to setting basic member fields, we also
    # prepare the Proc to be serializable with a couple of default functions.
    # If these functions don't work for you then you can replace them by 
    # calling util.serializer.registerObjectClass again. 
    # \param triggerCondition When the Proc is invoked.
    # \param params Maps parameter names to values for those parameters. 
    # Parameter interpretation is left up to the specific proc.
    # \param level The level of the effect -- may affect interpretation of 
    #        some of the parameters.
    def __init__(self, triggerCondition, params = None, procLevel = None):
        self.triggerCondition = triggerCondition
        self.params = params
        self.procLevel = procLevel
        self.id = util.id.getId()

        ## Generate a "blank" instance of the Proc.
        def makeBlankProc(gameMap):
            # self.__class__ is the class constructor of the object, taking
            # inheritance into account.
            return self.__class__(triggerCondition = None, params = None, procLevel = None)
        # Register this proc type as serializable. 
        util.serializer.registerObjectClass(self.__class__.__name__, 
                makeBlankProc)


    ## Trigger the Proc, with any appropriate parameters.
    # The trigger function is typically called when the triggerCondition 
    # happens (e.g. if triggerCondition is "item use" then the function will
    # be called when an item is used). That code in turn may provide different
    # parameter sets to the trigger() call. For example:
    # - "item use" provides the "item", "user", and "gameMap" parameters
    # - "tunnel" provides the "terrain", "actor", "gameMap", and "pos"
    #   parameters
    # The Proc code may not actually need any or all of these parameters to 
    # function. For example, a "print message" Proc just displays a message
    # from its params dictionary, so it can be called with any trigger 
    # condition. Thus some Procs can be re-used with multiple different 
    # triggerConditions; as long as the parameters the Proc actually needs 
    # are available, it is able to run. 
    # Note that this means that when you write a new Proc's trigger function,
    # you should ensure that you include the "*args" and "**kwargs" parameters,
    # so that the Proc can be provided with any number of extra parameters
    # which it will ignore.
    def trigger(self, *args, **kwargs):
        raise RuntimeError("Proc of type [%s] didn't implement its trigger function." % type(self))


    ## Generate a dict that is ready for serialization. See the util.serializer
    # module for more information. 
    # By default, we assume that a Proc can be safely reconstructed from its
    # parameters, level, and trigger condition. If this is not true for your
    # new Proc then you need to override this function.
    def getSerializationDict(self):
        return self.__dict__



## Prints a message when used.
class MessageProc(Proc):
    ## Just display our message string; we don't care about any passed-in
    # parameters.
    def trigger(self, *args, **kwargs):
        gui.messenger.message(self.params['messageString'])
        return True



## Prints a message that performs some string substitutions.
class SmartMessageProc(Proc):
    ## Replace e.g. <actor> with the value of the "actor" parameter in 
    # kwargs.
    def trigger(self, **kwargs):
        string = self.params['messageString']
        for key, value in kwargs.iteritems():
            string = string.replace('<%s>' % key, str(value))
        gui.messenger.message(string)
        return True



## Reduce the quantity of the invoked item.
class ReduceQuantityProc(Proc):
    def trigger(self, item, gameMap, *args, **kwargs):
        item.quantity -= 1
        if item.quantity == 0:
            # No more of the item.
            # \todo For now assuming this always only applies to the player.
            message = util.grammar.getConjugatedPhrase(
                    '{creature} {verb} no more {item}',
                    gameMap, gameMap.getPlayer(), 'have', item)
            gui.messenger.message(message)
            gameMap.destroy(item)
            return True
        elif item.quantity < 0:
            raise RuntimeError("Item quantity less than 0; how did this happen?")
            return False



## This Proc handles attempts to tunnel through terrain.
class TunnelProc(Proc):
    def trigger(self, terrain, actor, gameMap, pos, *args, **kwargs):
        if util.randomizer.oneIn(self.params['difficulty']):
            gameMap.removeFrom(terrain, pos)
            message = util.grammar.getConjugatedPhrase(
                    '{creature} {verb} through the %s' % terrain.name,
                    gameMap, actor, 'tunnel')
            gui.messenger.message(message)
            return True
        else:
            message = util.grammar.getConjugatedPhrase(
                    '{creature} {verb} to tunnel through the %s' % terrain.name,
                    gameMap, actor, 'fail')
            gui.messenger.message(message)
            return False



## Replace the source terrain with a new terrain object.
class ReplaceTerrainProc(Proc):
    def trigger(self, terrain, gameMap, pos, *args, **kwargs):
        newTerrain = things.terrain.terrainLoader.makeTerrain(
                self.params['newTerrain'], 
                gameMap, terrain.pos, terrain.mapLevel)
        gameMap.removeFrom(terrain, pos)
        return True
       


## Generate a new level.
class ChangeLevelProc(Proc):
    def trigger(self, terrain, gameMap, *args, **kwargs):
        targetLevel = terrain.mapLevel
        if self.params['newLevel'][0] in ('+', '-'):
            # Apply an offset
            targetLevel += int(self.params['newLevel'])
        else:
            # Move to a specific level.
            targetLevel = int(self.params['newLevel'])
        gameMap.makeLevel(targetLevel)



## Perform one of several different Procs, selected at random but with a 
# weighting. We pass all of our invocation parameters along to the selected
# Proc.
class WeightedRandomChoiceProc(Proc):
    def trigger(self, *args, **kwargs):
        # Determine the total available weighting.
        totalWeight = 0
        for record in self.params['procs']:
            totalWeight += record.get('weight', 1)
        selection = random.randint(0, totalWeight)
        # Find the corresponding proc to execute.
        for record in self.params['procs']:
            totalWeight -= record.get('weight', 1)
            if totalWeight <= 0:
                # Make a copy of the record that has everything except the 
                # "weight" field, to make the Proc instance from.
                procRecord = dict(record)
                if 'weight' in procRecord:
                    del procRecord['weight']
                procToExec = procs.procLoader.generateProcFromRecord(procRecord)
                procToExec.trigger(*args, **kwargs)



# These imports must be delayed until the Proc class is defined, but we don't
# actually need them until this point anyway.
import aiProc
import calculatorProc
import damageProc
import displayProc
import filterProc
import nameProc
import spellProc
import statusProc


## Mapping of proc names to the functions that invoke them. Normally this would
# go at the top of the file, but of course none of these symbols are defined
# at that point.
PROC_NAME_MAP = {
        # Miscellaneous procs
        "change level": ChangeLevelProc,
        "print message": MessageProc,
        "print smart message": SmartMessageProc,
        "reduce quantity": ReduceQuantityProc,
        "replace terrain": ReplaceTerrainProc,
        "tunnel": TunnelProc,
        "weighted random choice": WeightedRandomChoiceProc,
        # AI procs
        "standard AI": aiProc.BasicAIProc,
        "basic status update": aiProc.BasicStatusUpdateProc,
        # Calculator procs
        "percentage stat mod": calculatorProc.PercentageStatModCalculator,
        "combining stat mod": calculatorProc.LinearCombinationStatModCalculator,
        # Damage procs
        "damage equipment": damageProc.DamageEquipmentProc,
        "damage-based status effect": damageProc.DamageStatusProc,
        "do creature attack": damageProc.CreatureAttackProc,
        "do weapon attack": damageProc.WeaponAttackProc,
        "polymorph": damageProc.PolymorphProc,
        # Display procs
        "display creature recall": displayProc.CreatureRecallProc,
        # Filter procs
        "don't allocate if already dead": filterProc.AllocationPreventionDeathClauseFilter,
        "don't allocate if already existing": filterProc.AllocationPreventionDoubleClauseFilter,
        "stop": filterProc.FalseFilter,
        # Item name procs
        "default name": nameProc.DefaultItemNamer,
        "unique name": nameProc.UniqueItemNamer,
        "spell name": nameProc.SpellItemNamer,
        # Various spell effects.
        "cast creature spell": spellProc.CastCreatureSpellProc,
        "launch explosive": spellProc.ExplosiveProjectileProc,
        "launch projectile": spellProc.ProjectileProc,
        "phase door": spellProc.PhaseDoorProc,
        "swap stats": spellProc.SwapStatsProc,
        "teleport away": spellProc.TeleportAwayProc,
        "teleport to": spellProc.TeleportToProc,
        "temporary stat mod": spellProc.TemporaryStatModProc,
        "temporary status effect": spellProc.TemporaryStatusEffectProc,
        # Status effects
        "prevent item use": statusProc.PreventItemUseProc,
        "randomize movement": statusProc.RandomizeMovementProc,
}


## If a Proc has one of these triggers, then it's a "static" Proc, i.e.
# not specific to an instantiated Thing, but rather associated with all 
# Things of that type/subtype. Generally this is needed when we need to make
# decisions about that class of Thing but don't an instanced one handy.
# NOTE: these procs are assumed to only exist to modify game logic, not to 
# have any effect on the game world. There is no guarantee that a given 
# Proc using one of these triggers will be invoked, if an earlier Proc
# with the same trigger returned False. 
STATIC_TRIGGERS = set([
    "allocation table creation",
    "allocation table selection",
    "display recall",
])

