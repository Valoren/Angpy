## Class that stores and applies affix data. Affixes are objects which confer
# or adjust properties on items: changing damage, weight, stat boosts,
# resists etc. They are defined in data/object/affix.txt. Affixes have a type
# and a level, both of which are defined in data/affix_meta.txt. See
# http://bitbucket.org/derakon/pyrel/wiki/data_files for more information.

import allocatorRules
import util.boostedDie
import itemLoader
from .. import stats
import util.record

import collections
import random

## Order we want to print out components of the affix record when we serialize.
# None denotes a newline.
# \todo add template fields if implementing affix templates
AFFIX_FIELD_ORDER = ['index', 'affixType', 'position', None,
        'name', 'genus', None,
        'display', None,
        'stats', None,
        'minima', None,
        'mods', None,
        'flags', None,
        'randoms', None,
        'procs', None,
        'conflicts', None,
        'allocatorRules', None,
        'description', None,
]


class Affix:
    ## \param record A dictionary containing our instantiation data.
    def __init__(self, record):
        ## We need to hold onto this
        self.record = record
        ## Names of templates that specify some of our information.
        # \todo Consider affix templates to slim down affix.txt
        self.templates = []
        # Explicit listing of our possible fields, since not all of them
        # are in the record.
        ## Unique identifying integer.
        self.index = None
        ## Broad typing for the affix (e.g. make, material, quality)
        self.affixType = None
        ## Position of affix:
        # modPrefix - goes before the modifierNoun
        # basePrefix - goes before the baseNoun, after the modifierNoun
        # suffix - goes after the baseNoun
        # Anything else has no effect
        self.position = None
        ## The distance from the noun being modified.
        # 1 = immediately adjacent (before, if it's a prefix, else after)
        # 2 = next most adjacent
        # etc.
        # Defaults to 100 for affixes that neither specify a distance, nor
        # have an affixType to get a default value from.
        self.positionDistance = 100
        ## Name of the affix
        self.name = None
        ## Genus of the affix (generic name for use with multiple affixes)
        self.genus = None
        ## Stats instance containing all stats for the affix
        self.stats = stats.Stats()
        ## Minimum stats (these are not mods so we don't use a Stats instance)
        self.minima = dict()
        ## List of bonuses.
        self.mods = []
        ## List of flags
        self.flags = []
        ## List of random flag possibilities
        self.randoms = []
        ## ProcFactories that generate the effects the affix is capable of 
        # triggering.
        self.procs = []
        ## List of affixes with which we conflict
        self.conflicts = []
        ## Information on how we allocate ourselves.
        self.allocatorRules = []
        ## The quality level of the affix (determined upon application, since
        # it depends on the item type and itemLevel)
        self.affixLevel = None
        ## Prose description
        self.description = ''

        # Build a full record based on the current object and all ancestor templates.
        # NOTE: There are no affix templates, so don't pass any template loader.
        completeRecord = util.record.buildRecord(self, None)
        # Apply that record to ourselves, setting appropriate attributes in place.
        util.record.applyRecord(self, completeRecord)

        # Generate AffixAllocatorRules from our allocatorRules field.
        if 'allocatorRules' in completeRecord:
            self.allocatorRules = [allocatorRules.AffixAllocatorRule(a) for a in completeRecord['allocatorRules']]

        # Fill in our stats.
        self.stats = stats.deserializeStats(completeRecord.get('stats', {}))
        # Apply flags as -1/+1 modifiers, depending on if they begin with a 
        # '-'
        for flag in self.flags:
            if flag.startswith('-'):
                self.stats.addMod(flag, stats.StatMod(0, -1))
            else:
                self.stats.addMod(flag, stats.StatMod(0, 1))

        # Get any procs
        self.procRecords = completeRecord.get('procs', [])

        # Update the position values from the affixType metadata if none
        # are explicitly provided in the record definition.
        if not self.position or not self.positionDistance:
            if self.affixType:
                # affixType must provide a default position and distance
                affixType = itemLoader.getAffixType(self.affixType)
                if not self.position:
                    self.position = affixType['position']
                if self.positionDistance == 100:
                    self.positionDistance = affixType['positionDistance']


    ## Functions for applying random properties to items
    # We assume all validity checks have been passed before this
    # \param itemLevel
    # \param item - The item to attach the affix to
    # \param isThemed - True if this affix was generated from a theme
    def applyAffix(self, itemLevel, item, isThemed = False):
        # Apply random flags
        for randomFlag in self.randoms:
            flags = []
            # Build a list of available flags from given flag types
            if 'flag types' in randomFlag:
                for flagType in randomFlag['flag types']:
                    for flag in itemLoader.OBJECT_FLAGS:
                        if flag['flagType'] == flagType:
                            flags.append(flag['label'])
            # Add a specific list of flags to the list we're building
            if 'flags' in randomFlag:
                flags.extend(randomFlag['flags'])
            # Now choose from the finished list
            for i in range(randomFlag['number']):
                item.stats.addMod(random.choice(flags), stats.StatMod(0, 1))

        # Apply all other affix stats to item
        item.stats.mergeStats(self.stats)

        # Apply mods to stats
        for mod in self.mods:
            bonus = util.boostedDie.BoostedDie(mod['bonus']).roll()
            statMod = stats.StatMod(0, bonus)
            for flag in mod['flags']:
                item.stats.addMod(flag, statMod)
        # Calculate any modifiers that were in BoostedDie format.
        item.stats.roll(itemLevel)

        # Apply minima
        for stat in self.minima.keys():
            value = item.getStat(stat)
            minimum = int(self.minima[stat])
            if value < minimum:
                item.stats.addMod(stat, stats.StatMod(0, minimum - value))

        # Record affix information on item for later reference
        item.affixes.append({'name': self.name,
                             'genus': self.genus,
                             'position': self.position,
                             'positionDistance': self.positionDistance,
                             # are the following two used by anything?
                             'affixType': self.affixType,
                             'affixLevel': self.affixLevel,
                             'isThemed': isThemed})

    ## Serialize us. We use the JSON format, but we output keys in a specific
    # order and try to compact things as much as possible without sacrificing
    # legibility.
    def getSerialization(self):
        return util.record.serializeRecord(self.record, AFFIX_FIELD_ORDER)


    ## Compare us against another Affix, for sorting.
    def __cmp__(self, alt):
        return cmp(self.affixType, alt.affixType) or cmp(self.genus, alt.genus)
