import container
import things.thing
import things.mixins.updater
import util.serializer



## A Timer is an entity that waits a certain number of normal-speed turns, 
# calls a function, and then dies. It can be updated before it times out to
# also call other functions, if desired. 
class Timer(things.thing.Thing, things.mixins.updater.Updateable):
    ## \param duration How many turns to wait.
    # \param func Function to call when our time runs out.
    # \param funcArgs Tuple of arguments to pass to the function when it is
    #        called.
    # \param speed Rate at which turns pass 
    #        (1 = normal speed, 2 = double, etc.).
    def __init__(self, gameMap, duration, func, funcArgs, name = None, 
            speed = 1):
        things.thing.Thing.__init__(self, name = name)
        things.mixins.updater.Updateable.__init__(self, gameMap, 
                name = name, speed = speed, energy = 0)
        self.gameMap = gameMap
        self.duration = duration
        ## List of (function, args tuple) of functions to call when the 
        # trigger event occurs. 
        self.triggerFuncs = [(func, funcArgs)]


    def update(self, *args):
        self.duration -= 1
        self.energy = 0
        if self.duration <= 0:
            for func, args in self.triggerFuncs:
                func(*args)
            self.gameMap.destroy(self)


    ## Change the duration to the specified value.
    def setDuration(self, newDuration):
        self.duration = newDuration


    ## Add an extra function to invoke when we trigger.
    def doAlso(self, func, *args):
        self.triggerFuncs.append((func, args))


    ## Generate a ready-to-be-serialized dict. See util.serializer for more
    # info.
    def getSerializationDict(self):
        return self.__dict__



## Generate a "blank" Timer as part of the deserialization process.
def makeBlankTimer(gameMap):
    return Timer(gameMap, 0, None)


util.serializer.registerObjectClass(Timer.__name__, makeBlankTimer)
