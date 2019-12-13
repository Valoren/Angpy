import util.boostedDie
import util.randomizer
import util.record
import itemLoader
import things.mixins.filter

import collections

## This class is a simple container class describing how an item ought to be 
# allocated.
class ItemAllocatorRule:
    ## \param record A dictionary defining allocation parameters, taken from
    # object.txt.
    def __init__(self, record):
        self.commonness = record['commonness']
        self.minDepth = record['minDepth']
        self.maxDepth = record['maxDepth']
        self.pileChance = 0
        pileSize = ''
        if 'piling' in record:
            self.pileChance = record['piling']['chance']
            pileSize = record['piling']['pileSize']
        self.pileSize = util.boostedDie.BoostedDie(pileSize)


    ## Return true if we can generate items of the given depth.
    # -1 is a special value which means "no maximum"
    def isValidAtItemLevel(self, itemLevel):
        return (self.minDepth <= itemLevel and
               (itemLevel <= self.maxDepth or self.maxDepth == -1))


    ## Get a quantity for allocation.
    def getQuantity(self, itemLevel):
        quantity = 1
        if util.randomizer.passPercentage(self.pileChance):
            quantity = self.pileSize.roll(itemLevel)
        return quantity


    ## Convert to string for storage.
    def serialize(self):
        result = collections.OrderedDict()
        result['minDepth'] = self.minDepth
        result['maxDepth'] = self.maxDepth
        result['commonness'] = self.commonness
        if self.pileChance:
            result['piling'] = {
                    'chance': self.pileChance,
                    'pileSize': self.pileSize.serialize
            }
        return result



## Class for describing how affixes are allocated
class AffixAllocatorRule(things.mixins.filter.ItemFilter):
    ## \param record A dictionary defining allocation parameters, taken from
    # affix.txt (see http://bitbucket.org/derakon/pyrel/wiki/data_files
    # for full documentation)
    def __init__(self, record):
        # Construct the filter mixin
        things.mixins.filter.ItemFilter.__init__(self)
        # Apply the record values to ourselves.
        util.record.applyRecord(self, record)


    ## Return true if we can generate affixes at the given depth.
    def isValidAtItemLevel(self, itemLevel):
        return (self.minDepth <= itemLevel and
               (itemLevel <= self.maxDepth or self.maxDepth == -1))


    ## Return true if we can generate affixes of the given quality level.
    def isValidAffixLevel(self, minAffixLevel = None, maxAffixLevel = None):
        ## Convert text affix level labels to numbers, where present.
        ourAffixLevel = itemLoader.AFFIX_LEVELS[self.affixLevel]['rank']
        if minAffixLevel:
            minimum = itemLoader.AFFIX_LEVELS[minAffixLevel]['rank']
        if maxAffixLevel:
            maximum = itemLoader.AFFIX_LEVELS[maxAffixLevel]['rank']
        # Compare levels which are present
        if minAffixLevel is None:
            if maxAffixLevel is None:
                return True
            else:
                return ourAffixLevel <= maximum
        elif maxAffixLevel is None:
            return minimum <= ourAffixLevel
        else:
            return minimum <= ourAffixLevel <= maximum


    ## Convert to string for storage.
    def serialize(self):
        result = collections.OrderedDict()
        result['minDepth'] = self.minDepth
        result['maxDepth'] = self.maxDepth
        result['commonness'] = self.commonness
        result['affixLevel'] = self.affixLevel
        result['itemType'] = self.itemType
        return result



## Simple class to store maximum and minimum allowed affix types and levels
class AffixLimits:
    ## \param record A dictionary containing maxima and minima
    def __init__(self, record):
        self.levelsMin = record.get('levelsMin', None)
        self.levelsMax = record.get('levelsMax', None)
        self.typesMin = record.get('typesMin', None)
        self.typesMax = record.get('typesMax', None)
        self.minAffixLevel = record.get('minAffixLevel', None)
        self.maxAffixLevel = record.get('maxAffixLevel', None)



## Class for describing how themes are allocated
class ThemeAllocatorRule(things.mixins.filter.ItemFilter):
    ## \param record A dictionary defining allocation parameters, taken from
    # theme.txt (see http://bitbucket.org/derakon/pyrel/wiki/data_files
    # for full documentation)
    def __init__(self, record):
        # Construct the filter mixin
        things.mixins.filter.ItemFilter.__init__(self)
        # Apply the record values to ourselves.
        util.record.applyRecord(self, record)


    ## Return true if we can generate themes at the given depth.
    def isValidAtItemLevel(self, itemLevel):
        return (self.minDepth <= itemLevel and
               (itemLevel <= self.maxDepth or self.maxDepth == -1))


    ## Convert to string for storage.
    def serialize(self):
        result = collections.OrderedDict()
        result['minDepth'] = self.minDepth
        result['maxDepth'] = self.maxDepth
        result['itemType'] = self.itemType
        return result
