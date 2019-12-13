import creatureLoader

import random

## CreatureAllocators are used to select creatures to place into the game map,
# as appropriate to the given level. They behave similarly to ItemAllocators
# but are simpler.
class CreatureAllocator:
    def __init__(self, creatureLevel, filterFuncs = []):
        ## Level at which we generate creatures.
        self.creatureLevel = creatureLevel
        # filterFuncs A list of functions that accept a CreatureFactory and
        # returns True if it is desirable, False otherwise. If not supplied, we
        # assume all creatures are valid.
        self.filterFuncs = filterFuncs

        ## List of (commonness, CreatureFactory) tuples, where "commonness" is a
        # number indicating how common the creature is (larger = more common).
        self.allocationTable = []
        ## This is the sum of all commonness values for all valid creatures.
        self.maxRoll = 0

        
    ## \param pos Location at which the creature is placed.
    def allocate(self, gameMap, pos):
        if not self.allocationTable:
            # Generate the allocation table now. Iterate over all possible
            # creatures, decide if they're valid using the filter func(s), and
            # insert them into the list.
            for factory in creatureLoader.CREATURE_MAP.values():
                if (not factory.rarity or 
                        sum([not f(factory) for f in self.filterFuncs])):
                    # Creature is not valid; skip it.
                    continue
                elif "allocation table creation" in factory.staticProcs:
                    # Check if the factory will allow the creature to be 
                    # allocated.
                    canAllocate = True
                    for effect in factory.staticProcs["allocation table creation"]:
                        if not effect.trigger(factory = factory, 
                                gameMap = gameMap):
                            canAllocate = False
                            break
                    if not canAllocate:
                        continue

                try:
                    # The number of entries a creature gets depends on its
                    # native depth relative to the desired depth. Entries fall
                    # off exponentially if the monster is too deep, and linearly
                    # if it is too shallow.
                    numEntries = factory.rarity
                    if factory.nativeDepth > self.creatureLevel:
                        numEntries /= float(2 ** (factory.nativeDepth - self.creatureLevel))
                    else:
                        numEntries -= (self.creatureLevel - factory.nativeDepth)
                    if numEntries > 0:
                        numEntries = int(numEntries)
                        self.maxRoll += numEntries
                        self.allocationTable.append((numEntries, factory))
                except Exception, e:
                    print "Factory for creature %s could not be allocated: %s." % (factory.name, e)

            # Sort the table so the most common creatures are first, to make
            # repeated allocations faster.
            # \todo This may be wasted effort if we're only going to do a few
            # allocations.
            self.allocationTable.sort(lambda a, b: cmp(a[0], b[0]))

        numTries = 0
        # \todo Make this a constant somewhere. We should only need retries
        # if the factory rejects allocation of the creature knowing the current
        # game state, which ideally shouldn't happen often.
        while numTries < 1000:
            numTries += 1
            roll = random.randint(0, self.maxRoll)
            for commonness, factory in self.allocationTable:
                roll -= commonness
                if roll <= 0:
                    if "allocation table selection" in factory.staticProcs:
                        canAllocate = True
                        for effect in factory.staticProcs["allocation table selection"]:
                            if not effect.trigger(factory = factory,
                                    gameMap = gameMap):
                                canAllocate = False
                                break
                        if not canAllocate:
                            break

                    result = factory.makeCreature(gameMap, pos)
                    return result
            
        raise RuntimeError("Couldn't manage to pass our allocation filters after %d attempts." % numTries)



