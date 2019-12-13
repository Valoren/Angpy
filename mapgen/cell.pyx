## Cells are simply Containers that have a fixed position in the GameMap.

import container
import util.serializer



class Cell(container.Container):
    ## \param pos (X, Y) tuple of our position.
    def __init__(self, pos):
        container.Container.__init__(self)
        self.pos = pos
        ## Set of functions that want to know whenever the contents of the
        # Cell change. 
        # Each must accept three arguments: ourselves, the item in question (or
        # None to initialize an "empty" cell), and
        # a boolean indicating if the item is entering or leaving.
        self.updateCellFuncs = set()


    ## Receive new update funcs, and let them know about all of our contents.
    def addUpdateFuncs(self, funcs):
        for func in funcs:
            if func in self.updateCellFuncs:
                # Don't need to tell it twice.
                continue
            self.updateCellFuncs.add(func)
            func(self, None, None) # Start with an empty cell
            for item in self:
                # Add each item in turn.
                func(self, item, True)


    ## Passthrough, but call our update funcs.
    def subscribe(self, member):
        container.Container.subscribe(self, member)
        for func in self.updateCellFuncs:
            func(self, member, True)


    ## Passthrough, but call our update funcs.
    def unsubscribe(self, member):
        container.Container.unsubscribe(self, member)
        for func in self.updateCellFuncs:
            func(self, member, False)


    ## Generate a ready-to-be-serialized dict of our data. See the 
    # util.serializer module for more information.
    def getSerializationDict(self):
        result = self.__dict__.copy()
        # This will have to be restored later.
        del result['updateCellFuncs']
        return result


    def __unicode__(self):
        return u"<Cell %s with contents: %s>" % (self.id, self.members)



## Create a "blank" (no data filled in) Cell instance, needed for the 
# deserialization process. See util.serializer for more information. 
def makeBlankCell(*args, **kwargs):
    return Cell((-1, -1))


# Register the Cell class as being eligible for [de]serialization.
util.serializer.registerObjectClass(Cell.__name__, makeBlankCell)
