import util.id
## "Physical object" existing in the game world. This is a base class that
# should be subclassed from instead of being instantiated directly. Subclasses
# are responsible for subscribing to containers.


class Thing:
    ## \param pos Position in the game map, or None if this doesn't make sense
    #        (e.g. for items held in inventory).
    # \param name Unique name, or None if none is needed.
    def __init__(self, pos = None, name = None):
        self.pos = pos
        ## Broad category type of the item, e.g. dragon, potion, wall
        self.type = None
        ## Specific subcategory type of the item, e.g. Young Red Dragon, 
        # Potion of Cure Light Wounds, Quartz Vein.
        self.subtype = None
        self.name = name
        self.id = util.id.getId()


    ## Update the type information.
    def setTypeInfo(self, type, subtype):
        self.type = type
        self.subtype = subtype


