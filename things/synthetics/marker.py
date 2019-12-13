import container
import things.thing
import things.mixins.updater
import util.serializer



## A Marker just marks a location on the map. It has a location and an age;
# that's it.
class Marker(things.thing.Thing, things.mixins.updater.Updateable):
    def __init__(self, pos, gameMap, name = None, speed = 1):
        things.thing.Thing.__init__(self, name = name)
        things.mixins.updater.Updateable.__init__(self, gameMap, 
                name = name, speed = speed, energy = 0)
        self.pos = pos
        self.gameMap = gameMap
        self.age = 0


    def update(self, *args):
        self.age += 1
        self.energy = 0


    ## Generate a ready-to-be-serialized dict of our information. See the 
    # util.serializer module for more information. 
    def getSerializationDict(self):
        return self.__dict__


    def __unicode__(self):
        return "<Marker at %s with age %d>" % (str(self.pos), self.age)



## Generate a "blank" Marker with no information filled in.
def makeBlankMarker(gameMap):
    return Marker((-1, -1), gameMap)


util.serializer.registerObjectClass(Marker.__name__, makeBlankMarker)
