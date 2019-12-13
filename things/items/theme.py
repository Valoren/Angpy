## Class that stores and applies theme data. Themes are objects which confer
# multiple properties on items, by applying several affixes.
# They are defined in data/object/theme.txt. See
# http://bitbucket.org/derakon/pyrel/wiki/data_files for more information.

import allocatorRules
import itemLoader
import util.record

import random

## Order we want to print out components of the theme record when we serialize.
# None denotes a newline.
# \todo add template fields if implementing affix templates
THEME_FIELD_ORDER = ['index', 'name', 'position', None,
        'display', None,
        'affixes', None,
        'allocatorRules', None,
        'description', None,
]


class Theme:
    ## \param record A dictionary containing our instantiation data.
    def __init__(self, record):
        ## We need to hold onto this
        self.record = record
        ## Names of templates that specify some of our information.
        # \todo Consider theme templates to slim down theme.txt
        self.templates = []
        # Explicit listing of our possible fields, since not all of them
        # are in the record.
        ## Unique identifying integer.
        self.index = None
        ## Position of affix (either 'prefix' or 'suffix' will affect the
        # item name, anything else will not)
        self.position = None
        ## Name of the affix
        self.name = None
        ## List of dicts of affixes which lead to or are applied by the theme
        self.affixes = []
        ## Information on how we allocate ourselves.
        self.allocatorRules = []
        ## Prose description
        self.description = ''

        # Inherit values from our templates first, so they can be overridden
        # by our own attributes as needed.
        completeRecord = {}
#        if 'templates' in self.record:
#            for template in map(itemLoader.getThemeTemplate, self.record['templates']):
#                util.record.applyValues(template.record, completeRecord)
        util.record.applyValues(self.record, completeRecord)

        # Copy values from completeRecord to ourselves.
        for key, value in completeRecord.iteritems():
            setattr(self, key, value)

        # Generate ThemeAllocatorRules from our allocatorRules field.
        if 'allocatorRules' in completeRecord:
            self.allocatorRules = [allocatorRules.ThemeAllocatorRule(a) for a in completeRecord['allocatorRules']]

        
    ## Functions for applying a theme to an item
    # We assume all validity checks have been passed before this
    def applyTheme(self, itemLevel, item):
        # Take each of the theme's affixes in turn
        for affixDict in self.affixes:
            # Count how many times it is already on the item
            currentCount = 0
            for itemAffix in item.affixes:
                if itemAffix['name'] == affixDict['name']:
                    currentCount += 1
            # Work out how many times it gets applied in this theme
            if type(affixDict['chance']) is not list:
                affixDict['chance'] = [affixDict['chance']]
            numTimes = len(affixDict['chance'])
            # If we already have all needed applications of this affix, go on
            if numTimes <= currentCount:
                continue
            # Otherwise, try to apply it the remaining number of times            
            affix = itemLoader.getAffix(affixDict['name'])
            for i in xrange(numTimes - currentCount):
                if random.randint(0, 100) < affixDict['chance'][currentCount + i]:
                    affix.applyAffix(itemLevel, item, isThemed = True)

        # Record the theme name and position on the item.
        item.theme = dict({'name': self.name,
                           'position': self.position})
            

    ## Serialize us. We use the JSON format, but we output keys in a specific
    # order and try to compact things as much as possible without sacrificing
    # legibility.
    def getSerialization(self):
        return util.record.serializeRecord(self.record, THEME_FIELD_ORDER)


    ## Compare us against another theme, for sorting.
    def __cmp__(self, alt):
        return cmp(self.name, alt.name)
        
