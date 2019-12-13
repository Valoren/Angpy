import collections

import procs.procLoader
import util.boostedDie
import util.id
import util.serializer



## This class handles statistics for a given Thing. "Statistics" are basically
# any numerical property of a Thing, from how many hitpoints it has to 
# how hard it is to find. Each statistic is composed of a series of tiers of
# StatMods which are applied in order. 
class Stats:
    ## Create the Stats. This function accepts arbitrary arguments as the 
    # deserialization process (in util.serializer) may supply extra arguments.
    # But we don't need them; they're just ignored.
    def __init__(self, **kwargs):
        ## Maps stat names to lists of StatMods for that stat.
        self.stats = {}
        ## Maps StatMod names to their instances.
        self.modNameToMod = {}
        ## Set of other Stats instances that we should take into account when
        # calculating values.
        self.children = set()
        ## Global unique ID.
        self.id = util.id.getId()


    ## Generate a copy of ourselves, which includes copying all of our
    # StatMods.
    def copy(self):
        newStats = Stats()
        for statName, mods in self.stats.iteritems():
            newStats.stats[statName] = [m.copy() for m in mods]
            for mod in mods:
                newStats.modNameToMod[mod.name] = mod
        newStats.children = set(self.children)
        return newStats


    ## Add a new modifier for the named stat.
    def addMod(self, statName, modifier):
        if statName not in self.stats:
            self.stats[statName] = []
        self.stats[statName].append(modifier)
        self.stats[statName].sort(key = lambda a: a.tier)
        self.modNameToMod[modifier.name] = modifier


    ## Remove the specific StatMod instance for the named stat.
    def removeMod(self, statName, modifier):
        if statName not in self.stats:
            raise RuntimeError("Tried to remove nonexistent stat [%s]" % statName)
        self.stats[statName].remove(modifier)
        # modifier.name won't be in self.modNameToMod if we had two StatMods
        # with the same ID added to the Stats instance.
        if modifier.name in self.modNameToMod:
            del self.modNameToMod[modifier.name]


    ## Add a Stats instance to self.children.
    def addStats(self, childStats):
        self.children.add(childStats)


    ## Remove a Stats instance from self.children.
    def removeStats(self, childStats):
        if childStats not in self.children:
            raise RuntimeError("Tried to remove nonexistent child stat")
        self.children.remove(childStats)


    ## Return true if we have mods for this stat.
    def hasMod(self, statName):
        return statName in self.stats


    ## Get the value for the named stat, taking into account all extra 
    # Stats instances that have been merged into us.
    # \param statName - Name of the stat we're trying to get a value for.
    # \param maxTier - Highest tier of stats that can be considered for this
    #        calculation. Default to allowing all tiers to contribute.
    # \param condition - A predicate function that can filter on whether
    #        to include a specific StatMod in the calculations of a stat.
    #        Examples:
    #         - an effect that doubles all racial mods would only want to
    #           get the total of racial mod values.
    #         - a dungeon area that enhances or nullifies all temporary effects
    #           etc.
    # \param busyMods - List of StatMods whose values are currently being 
    #                  calculated, to prevent infinite recursion when there's a
    #                  dependency loop.  Value is maintained across function
    #                  calls.
    def getStatValue(self, statName, maxTier = None, condition = None, 
            busyMods = []):
        result = 0
        accumulator = 0
        curTier = None
        # getAllStatModsFor() returns a list of mods sorted by tier,
        # so we can be assured that mod tiers progress from lowest to highest
        for mod in self.getAllStatModsFor(statName):
            # initialize curTier to the first mod's tier, rather than making
            # any assumptions about where it starts
            if curTier is None:
                curTier = mod.tier
            # make sure not to go past the maxTier, if specified
            if maxTier is not None and mod.tier > maxTier:
                break
            # If the tier in the mods list changes, update the
            # total and reset the accumulator.
            # Higher tiers can only reference the totals generated
            # by lower tiers, not tiers of equal or higher level.
            if mod.tier != curTier:
                result += accumulator
                accumulator = 0
                curTier = mod.tier
            # block against recursion; if a mod is already in the process
            # of getting its value, we can't call on it again til it's done.
            if mod not in busyMods:
                busyMods.append(mod)
                # allow for conditional filters to specify what type of
                # mods to process.
                if condition is None or condition(mod):
                    accumulator += mod.getModifier(self, result)
                del busyMods[-1]
        result += accumulator
        return result


    ## Get a sorted list of the StatMods for the named stat, including from
    # all of our children.
    def getAllStatModsFor(self, statName):
        result = []
        if statName in self.stats:
            result.extend(self.stats[statName])
        for child in self.children:
            result.extend(child.getAllStatModsFor(statName))
        result.sort(key = lambda a: a.tier)
        return result


    ## Generate a dict that maps stat names to stat values for all of our
    # stats.
    def getAllStats(self):
        return dict([(name, self.getStatValue(name)) for name in self.stats.keys()])


    ## Retrieve a StatMod with a specific name.
    def getModWithName(self, name):
        if name in self.modNameToMod:
            # We have it.
            return self.modNameToMod[name]
        # Try our children.
        for child in self.children:
            result = child.getModWithName(name)
            if result is not None:
                return result
        # Couldn't find it.
        return None


    ## Return a list of all stat names we have, including in our children.
    def getStatNames(self):
        result = set(self.stats.keys())
        for child in self.children:
            result.update(child.getStatNames())
        return result


    ## Yield a list of (stat name, value) pairs for all our stats.
    def listMods(self):
        keys = sorted(self.getStatNames())
        for key in keys:
            yield (key, self.getStatValue(key))


    ## Merge the provided Stats instance with ourselves.
    def mergeStats(self, alt):
        for statName, mods in alt.stats.iteritems():
            for mod in mods:
                copy = mod.copy()
                self.addMod(statName, copy)
                self.modNameToMod[copy.name] = copy


    ## Consolidate StatMod instances of the provided tier together, and give
    # them a new name based on the provided format string.
    def consolidateTier(self, tier, idFormat):
        for statName, mods in self.stats.iteritems():
            newMod = StatMod(tier)
            modsToRemove = []
            for mod in mods:
                if mod.tier == tier:
                    modsToRemove.append(mod)
                    newMod.addend += mod.addend
                    newMod.multiplier += mod.multiplier
                    newMod.procs.extend(mod.procs)
            if modsToRemove:
                # We should replace the given mods with the consolidated one.
                newMod.name = idFormat % statName
                self.addMod(statName, newMod)
                for oldMod in modsToRemove:
                    self.removeMod(statName, oldMod)


    ## Find StatMods that have modifiers in BoostedDie format and roll them
    # to get their actual values.
    def roll(self, level):
        for statName, mods in self.stats.iteritems():
            for mod in mods:
                mod.roll(level)


    ## Generate a ready-for-serialization dict. See the util.serializer
    # module for more information.
    def getSerializationDict(self):
        return self.__dict__


    ## Generate a string representation of the stats.
    def __unicode__(self):
        result = "<Stats with %d entries:" % len(self.stats.keys())
        for statName, values in self.stats.iteritems():
            result += "\n%s: %s" % (statName, self.getStatValue(statName))
        result += ">"
        return result



# Make Stats be [de]serializable.
util.serializer.registerObjectClass(Stats.__name__, Stats)


## Given a record (from a data file, not from a savefile), generate a Stats
# instance.
def deserializeStats(record):
    result = Stats()
    for statName, mods in record.iteritems():
        if type(mods) is not list:
            # Just one entry.
            result.stats[statName] = [deserializeStatMod(mods)]
        else:
            # Multiple entries.
            result.stats[statName] = [deserializeStatMod(m) for m in mods]
    return result



## This class represents a single modifier for a stat. By default these are 
# just additive values, but they can also be multipliers or invoke arbitrary
# functions as desired.
class StatMod:
    ## Note on the below: addend and multiplier can be strings in the 
    # BoostedDie format, in which case we're expected to roll them before
    # they ever get used. 
    # \param tier Integer indicating the tier of the stat, which in turn
    #         determines when it is applied and which stats it can use in
    #         calculating itself. A StatMod can only use other StatMods
    #         of strictly lower tier; this prevents circular dependencies.
    # \param addend Amount to add to the stat.
    # \param multiplier Amount to multiply the stat-thus-far by.
    # \param procs List of Proc instances to invoke to get an addend. Note
    #        that if the proc(s) want to take into account other stats, then
    #        they should limit themselves to stats up to (but not through)
    #        self.tier, to avoid potential infinite loops where two stats have
    #        a circular dependency.
    # \param name Unique name for the StatMod. If none is provided then an
    #        auto-incrementing ID will be used (same as the 'id' field).
    #        This can be used to find a specific StatMod later.
    def __init__(self, tier, addend = 0, multiplier = 0, procs = [], 
            name = '', category = None):
        self.tier = tier
        self.category = category
        self.addend = addend
        self.multiplier = multiplier
        self.procs = procs
        self.id = util.id.getId()
        self.name = self.id
        if name:
            self.name = name


    ## Get the additional modifier for the stat that we provide, taking into
    # account the provided Stats instance and the total calculated for the
    # stat thus far.
    def getModifier(self, stats, curVal):
        result = 0
        for proc in self.procs:
            result += proc.trigger(stats = stats, curVal = curVal,
                    tier = self.tier)
        result += self.addend + self.multiplier * curVal
        return result


    ## Calculate our addend and multiplier per the provided level. This is 
    # only relevant if the values are BoostedDie formats -- if they're 
    # numbers then we just leave them be.
    def roll(self, level):
        if type(self.addend) in [str, unicode]:
            self.addend = util.boostedDie.roll(self.addend, level)
        if type(self.multiplier) in [str, unicode]:
            self.multiplier = util.boostedDie.roll(self.multiplier, level)


    ## Generate a copy of ourselves.
    def copy(self):
        return StatMod(self.tier, self.addend, self.multiplier, self.procs)


    ## Generate a ready-for-serialization dict. See the util.serializer
    # module for more information.
    def getSerializationDict(self):
        return self.__dict__


    ## Pretty-printer.
    def __unicode__(self):
        entries = ["name %s" % self.name, "tier %d" % self.tier]
        if self.category:
            entries.append("category %s" % self.category)
        if self.addend:
            entries.append("+%.2f" % self.addend)
        if self.multiplier:
            entries.append("*%.2f" % self.multiplier)
        if self.procs:
            entries.append('special procs ["%s"]' % [p.id for p in self.procs])
        return "<%s>" % entries



## Create a "blank" StatMod.
def makeBlankStatMod(gameMap):
    return StatMod(0)


# Make StatMods be [de]serializable.
util.serializer.registerObjectClass(StatMod.__name__, makeBlankStatMod)


## Given a record (a dict or number), generate a StatMod from it. This is for
# loading from datafiles, not from a savefile, so it has a lot of logic to 
# make writing said datafiles easier.
# For numbers, we just take the number and apply it as an addend at the 
# level-0 tier. Otherwise, we extract the 'addend', 'multiplier', and 'proc'
# fields from the record, using defaults when they aren't available.
def deserializeStatMod(record):
    if type(record) in [int, float, str, unicode]:
        if type(record) in [str, unicode] and record[-1] == '%':
            # Use a percentage stat modifier.
            return StatMod(0, 0, 1.0 + int(record[:-1]) / 100)
        else:
            return StatMod(0, record)
    modProcs = record.get('procs', [])
    if modProcs:
        modProcs = [procs.procLoader.generateProcFromRecord(r) for r in modProcs]

    return StatMod(record.get('tier', 0),
            record.get('addend', 0), record.get('multiplier', 0),
            modProcs)

