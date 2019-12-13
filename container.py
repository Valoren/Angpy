import util.id
import util.serializer


## IDs for "fundamental" containers that will recur elsewhere in the code.
# Note that these all have negative values, to ensure they won't conflict
# with the automatically-generated IDs in util.id.
SPECIAL_CONTAINERS = (
## Must implement ascend(self, actor, gameMap)
ASCENDABLES,
## Must implement receiveAttack(self, alt)
ATTACKERS,
## Potentially obstructs movement. Must implement canMoveThrough(self, alt)
BLOCKERS,
## Must implement pickupItem(self, item), removeItem(self, item)
CARRIERS,
## Must implement close(self, actor, gameMap)
CLOSABLES,
## No required functions.
CREATURES,
## Must implement descend(self, actor, gameMap)
DESCENDABLES,
## No reqiured functions. Marks entities that the view should jump to when
# looking around.
INTERESTING,
## Must implement pickup(self), drop(self), getShortDescription(self)
ITEMS,
## Obstructs vision. No required functions.
OPAQUES,
## Must implement open(self, actor, gameMap)
OPENABLES,
## Marks the Thing as persisting across dungeon levels. Must implement
# resubscribe(self, gameMap).
PERSISTENT,
## We just like to keep track of this guy.
PLAYERS,
## No required functions.
TERRAIN,
## Must implement tunnel(self, actor, gameMap)
TUNNELABLES,
## Must implement update(self). Must have getStat('speed'), as well as
# "energy" and "name" fields. Recommend using the things.mixins.updater mixin.
UPDATERS,
## Must implement invoke(self).
USABLES,
## No required functions, but must have an equipSlot field.
WIELDABLES,
) = range(-18, 0)


## This class is basically a wrapper around the builtin set class, though it's
# very slightly smarter (you can set a callback to get notified when it empties,
# and we may add more later). 
# As a general rule, you should create new Containers by calling 
# GameMap.makeContainer() instead of by making them directly. That way the 
# GameMap can track the container for you. Only create Containers yourself if
# they are transient (won't last beyond the current function call). 
class Container:
    ## \param id Identifier for the Container. Uses a unique
    #         (auto-incrementing) numeric id by default. We only allow 
    #         specifying an ID for negative values here, indicating the 
    #         container is one of the special IDs listed in SPECIAL_CONTAINERS.
    # \param sortFunc Function to use for sorting our items when iterating over
    #        them.
    # \param members Things that start out in the container.
    # \param notifyOnEmpty Function to call if we're ever empty. Accepts our 
    #        ID as a parameter.
    def __init__(self, id = None, members = None, sortFunc = None,
            notifyOnEmpty = None, **kwargs):
        if id is not None and id > 0:
            raise RuntimeError("Trying to create a Container with a specific, non-reserved ID: %s." % str(id))
        self.id = util.id.getId(id)
        self.members = members
        if self.members is None:
            self.members = set()
        self.sortFunc = sortFunc
        self.notifyOnEmpty = notifyOnEmpty


    ## Receive a new member.
    def subscribe(self, member):
        self.members.add(member)


    ## Remove a member.
    def unsubscribe(self, member):
        self.members.remove(member)
        if not self.members and self.notifyOnEmpty is not None:
            self.notifyOnEmpty(self.id)


    ## Get members that intersect the given Container.
    def getIntersection(self, alt):
        return Container(members = self.members.intersection(alt.members),
                sortFunc = self.sortFunc)


    ## Get members that are disjoint to the given Container
    def getDifference(self, alt):
        return Container(members = self.members.difference(alt.members),
                sortFunc = self.sortFunc)


    ## Add alt's Things to our set.
    def unionAdd(self, alt):
        self.members.update(alt.members)


    ## Empty ourselves out entirely.
    def setEmpty(self):
        self.members.clear()


    ## Generate a ready-to-be-serialized dict of our contents. See the 
    # util.serializer module for more information.
    def getSerializationDict(self):
        return self.__dict__


    ## Iterate over our contents.
    def __iter__(self):
        iterable = self.members
        if self.sortFunc is not None:
            iterable = sorted(list(self.members), self.sortFunc)
        for item in iterable:
            yield item


    ## Get the number of items we have.
    def __len__(self):
        return len(self.members)


    ## Retrieve the indicated item from our set. This only works reliably
    # if we have a sorting function since sets are otherwise inherently
    # unordered.
    def __getitem__(self, index):
        iterable = list(self.members)
        if self.sortFunc is not None:
            iterable.sort(self.sortFunc)
        return iterable[index]


    ## Return true if we contain the specified item.
    def __contains__(self, item):
        return item in self.members


    ## Cast to a boolean -- return True if we have any subscribers.
    def __nonzero__(self):
        return bool(self.members)


    ## For debugging use, represent as a string.
    def __unicode__(self):
        return u"<Container %s with contents: %s>" % (self.id, self.members)



## Register Containers as a [de]serializable object class.
util.serializer.registerObjectClass(Container.__name__, 
        lambda **kwargs: Container())



## As Container is a smart wrapper around the builtin set, ContainerMap is a
# smart wrapper around the builtin dict. Sometimes we need a mapping
# relationship that can still be conveniently indexed into.
# As a general rule, you should create new ContainerMaps by calling 
# GameMap.makeContainerMap() instead of by making them directly. That way the 
# GameMap can track the container for you. Only create Containers yourself if
# they are transient (won't last beyond the current function call). 
class ContainerMap(dict):
    ## \param id Identifier for the Container. Uses a unique
    #         (auto-incrementing) numeric id by default. We only allow 
    #         specifying an ID for negative values here, indicating the 
    #         container is one of the special IDs listed in SPECIAL_CONTAINERS.
    # \param sortFunc Function to use for sorting our items when iterating over
    #        them or indexing into them.
    # \param members Initial dict of stuff starting out in the container.
    # \param notifyOnEmpty Function to call if we're ever empty. Accepts our 
    #        ID as a parameter.
    def __init__(self, id = None, members = None, sortFunc = None,
            notifyOnEmpty = None):
        if id is not None and id > 0:
            raise RuntimeError("Trying to create a ContainerMap with a specific, non-reserved ID: %s." % str(id))
        dict.__init__(self)
        self.id = util.id.getId(id)
        if members is not None:
            self.update(members)
        self.sortFunc = sortFunc
        self.notifyOnEmpty = notifyOnEmpty


    ## Receive a new key-value mapping.
    def subscribe(self, key, member):
        self[key] = member


    ## Remove whatever is under the given key.
    def unsubscribe(self, key):
        member = self[key]
        del self[key]
        if not self and self.notifyOnEmpty is not None:
            self.notifyOnEmpty(self.id)


    ## Iterate over our contents, using our sort function if relevant.
    def __iter__(self):
        iterable = self.keys()
        if self.sortFunc is not None:
            iterable.sort(self.sortFunc)
        for item in iterable:
            yield item


    ## Override so we operate in sorted order.
    def items(self):
        return [i for i in self.iteritems()]


    ## Override so we operate in sorted order.
    def iteritems(self):
        for key in self:
            yield (key, self[key])


    ## Override so we operate in sorted order.
    def values(self):
        return [self[key] for key in self]


    ## Retrieve the indicated item from our dict. This only works reliably
    # if we have a sorting function since sets are otherwise inherently
    # unordered.
    def getByIndex(self, index):
        iterable = self.keys()
        if self.sortFunc is not None:
            iterable.sort(self.sortFunc)
        return self[iterable[index]]


    ## Generate a ready-to-be-serialized dict of our contents. See the 
    # util.serializer module for more information.
    def getSerializationDict(self):
        return self.__dict__


    ## Access an item in our dict via its key. We put a hack in here to
    # try self.getByIndex() if the key is an int and isn't already in the
    # dict.
    def __getitem__(self, key):
        if key in self:
            return dict.__getitem__(self, key)
        if type(key) is int and key < len(self):
            return self.getByIndex(key)


    ## Hashing function; we do lookup by our unique ID.
    def __hash__(self):
        return hash(self.id)


    ## For debugging use, represent as a string.
    def __unicode__(self):
        return u"<ContainerMap %s with %d items>" % (self.id, len(self))



## Register ContainerMaps as a [de]serializable object class.
util.serializer.registerObjectClass(ContainerMap.__name__, 
        lambda **kwargs: ContainerMap())
