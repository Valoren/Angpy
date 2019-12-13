import container
import gui
import proc

# Filters are Procs that cause program flow to diverge -- they return True or 
# False and thus are used to decide which of two branches to take. 



## This Filter prevents allocation of a creature if it has previously been
# killed, or if it already exists in the gameMap.
class AllocationPreventionDeathClauseFilter(proc.Proc):
    def trigger(self, factory, gameMap, *args, **kwargs):
        # \todo This is just copied straight from AllocationPreventionDoubleClauseFilter...
        for creature in gameMap.getContainer(container.UPDATERS):
            if creature.name == factory.name:
                return False
        player = gameMap.getContainer(container.PLAYERS)[0]
        return (factory.name not in player.killCountMap or
                player.killCountMap[factory.name] == 0)


## This Filter prevents allocation of a creature if it's already running around
# in-game.
class AllocationPreventionDoubleClauseFilter(proc.Proc):
    def trigger(self, factory, gameMap, *args, **kwargs):
        for creature in gameMap.getContainer(container.CREATURES):
            if creature.name == factory.name:
                return False
        return True



## This Filter simply returns False.
class FalseFilter(proc.Proc):
    def trigger(self, *args, **kwargs):
        return False
    

