import container
import procs.procLoader
import terrainLoader
import things.thing
import things.stats
import util.boostedDie
import util.serializer

## Order in which we serialize records.
FIELD_ORDER = ['name', None,
        'templates', None,
        'display', None,
        'interactions', None,
        'flags', None,
        'mods', None
]

## Attributes that we copy verbatim over from the TerrainFactory to the 
# Terrain instance.
COPIED_FIELDS = ['name', 'display']

## TerrainFactories instantiate Terrain instances.
class TerrainFactory:
    ## \param record The record from terrain.txt defining the Terrain.
    def __init__(self, record):
        ## Keep a copy around for later reserialization.
        self.record = record
        ## Unique identifier
        self.name = None
        ## Display metadata.
        self.display = {}
        ## List of other Terrain types we descend from, which apply themselves
        # as templates to ourselves.
        self.templates = []
        ## Maps action names to lists of procs to invoke when those actions
        # occur.
        self.interactions = {}
        ## Binary modifiers, like whether or not something can be seen through.
        # These will be converted to +1 stat modifiers when actual Terrain is
        # created; this is purely a convenience for when writing out the
        # terrain records.
        self.flags = []
        ## Stats instance.
        self.stats = things.stats.Stats()

        if 'templates' in record:
            for name in record['templates']:
                template = terrainLoader.getTerrainFactory(name)
                self.updateFields(template.__dict__)
        self.updateFields(record)


    ## Apply all of the values in the provided dictionary to ourselves.
    def updateFields(self, record):
        for key, value in record.iteritems():
            if key == 'templates':
                # Don't do this one, since we don't ever directly inherit it.
                continue
            elif key == 'interactions':
                for interaction in value:
                    # Remap the provided list of dictionaries into a mapping of 
                    # the "action" value to a list of procs.
                    action = interaction['action']
                    if action not in self.interactions:
                        self.interactions[action] = []
                    if 'preProcs' in interaction:
                        self.interactions[action] = interaction['preProcs'] + self.interactions[action]
                    if 'procs' in interaction:
                        self.interactions[action].extend(interaction['procs'])
                    if 'postProcs' in interaction:
                        self.interactions[action].extend(interaction['postProcs'])
            elif type(value) is list:
                if not hasattr(self, key):
                    setattr(self, key, [])
                getattr(self, key).extend(value)
            else:
                # Assume scalar.
                setattr(self, key, value)
                

    ## Generate an appropriate Terrain instance of the given level.
    # Primarily this means instantiating Procs for the transitions.
    def makeTerrain(self, gameMap, pos, mapLevel):
        result = Terrain(gameMap, pos)
        for field in COPIED_FIELDS:
            setattr(result, field, getattr(self, field))

        # Stat modifiers may have values that need to be evaluated now.
        result.stats = self.stats.copy()
        result.stats.roll(mapLevel)
        # Merge binary values into the mods dict.
        for flag in self.flags:
            result.stats.addMod(flag, things.stats.StatMod(0, 1))

        # Procs need to be instantiated for all interactions, now.
        for action, procRecords in self.interactions.iteritems():
            newProcs = [procs.procLoader.generateProcFromRecord(procRecord, mapLevel) for procRecord in procRecords]
            result.interactions[action] = newProcs

        result.mapLevel = mapLevel

        result.init(gameMap)
        return result


    def getSerialization(self):
        return util.record.serializeRecord(self.record, FIELD_ORDER)



## Terrain are Things that don't move around or act autonomously, but have a 
# number of interactions that transform them into other Terrains or destroy
# them (e.g. opening doors, digging out walls).
class Terrain(things.thing.Thing):
    def __init__(self, gameMap, pos):
        things.thing.Thing.__init__(self, pos)
        if pos:
            gameMap.addSubscriber(self, pos)

        ## Name of the terrain
        self.name = None
        ## Level at which the terrain was created.
        self.mapLevel = None
        ## Display information.
        self.display = {}
        ## Relevant stats for the terrain instance.
        self.stats = things.stats.Stats()
        ## Maps action names to the procs that occur when something performs
        # that action on us.
        self.interactions = {}


    ## Now that we're instantiated, add us to any appropriate containers.
    def init(self, gameMap):
        gameMap.addSubscriber(self, container.TERRAIN)
        if self.stats.getStatValue('OBSTRUCT'):
            gameMap.addSubscriber(self, container.BLOCKERS)
        if self.stats.getStatValue('INTERESTING'):
            gameMap.addSubscriber(self, container.INTERESTING)
        if self.stats.getStatValue('OPAQUE'):
            gameMap.addSubscriber(self, container.OPAQUES)
        for action, group in [('open', container.OPENABLES),
                ('close', container.CLOSABLES),
                ('descend', container.DESCENDABLES),
                ('ascend', container.ASCENDABLES),
                ('tunnel', container.TUNNELABLES)]:
            if action in self.interactions:
                gameMap.addSubscriber(self, group)


    ## React to trying to move through us.
    def canMoveThrough(self, target):
        return (self.stats.getStatValue('OBSTRUCT') == 0)


    ## Interact with the Terrain instance.
    # \param action String describing the action to do; we use this to look
    #        up any associated procs we have.
    # \param actor Thing performing the action.
    # \param pos Position of the Terrain being interacted with -- in the event
    #        that our own pos field is invalid (because we're being aliased to
    #        multiple locations simultaneously).
    def interact(self, action, actor, gameMap, pos):
        for proc in self.interactions[action]:
            if not proc.trigger(terrain = self, actor = actor, 
                    gameMap = gameMap, pos = pos):
                # The proc blocked further procs from proceeding
                break


    ## Generate a ready-to-be-serialized dict of this Terrain's information.
    # See the util.serializer module for more information.
    def getSerializationDict(self):
        return self.__dict__


    ## Convert to a string for display.
    def __unicode__(self):
        return u"<Terrain %s at %s>" % (self.name, self.pos)



## Make a "blank" Terrain instance for deserialization. 
def makeBlankTerrain(gameMap):
    return Terrain(gameMap, (-1, -1))


util.serializer.registerObjectClass(Terrain.__name__, makeBlankTerrain)
