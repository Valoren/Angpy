import container
import things.stats

## This mixin provides the following attributes:
# - "name" and "energy" fields
# - a "stats" field if it doesn't already exist.
# - "addEnergy" method and "getStat" method.
# - a dummy "update" method.
class Updateable:
    def __init__(self, gameMap, name, speed = 0, energy = 0):
        self.name = name
        self.energy = energy
        if not hasattr(self, 'stats'):
            self.stats = things.stats.Stats()
        if speed:
            self.stats.addMod('speed', 
                    things.stats.StatMod(0, addend = speed))
        gameMap.addSubscriber(self, container.UPDATERS)

        
    ## Add some energy. When we pass 1 energy, we get a turn.
    def addEnergy(self, modifier):
        self.energy += modifier


    ## Get a stat out of our stats field.
    def getStat(self, statName):
        if self.stats.hasMod(statName):
            return self.stats.getStatValue(statName)
        raise RuntimeError("Thing named [%s] has no stat [%s]" % (self.name, statName))


    ## Update the entity. This should probably be overwritten by descendants.
    def update(self, *args, **kwargs):
        self.energy = 0
