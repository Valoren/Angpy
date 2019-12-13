## This file defines the LootTemplate class. Loot templates hold rules for
# item generation, such as which item types are allowed, how many affixes
# they're allowed to have, and which kinds. Please see
# http://bitbucket.org/derakon/pyrel/wiki/data_files for full documentation.

import itemLoader
import things.mixins.filter
import util.boostedDie
import util.evaluator

import random



## Class that sets rules and filters for item generation
class LootTemplate(things.mixins.filter.ItemFilter,
                   things.mixins.filter.AffixFilter,
                   things.mixins.filter.ThemeFilter):
    ## \param record A dictionary containing our instantiation data
    def __init__(self, record):
        # Construct the filter mixins
        things.mixins.filter.ItemFilter.__init__(self)
        things.mixins.filter.AffixFilter.__init__(self)
        things.mixins.filter.ThemeFilter.__init__(self)
        # The raw data record loaded from data/loot_template.txt
        self.record = record
        # The name of this template
        self.templateName = None
        # Dict of chance/amount pairs for random boosts to values
        self.itemRuleBoosts = {}
        # Overall number and chance of drops
        self.numDrops = 1
        self.dropChance = 100
        # The two levels for the item (itemLevel for generation,
        # magicLevel for properties)
        self.itemLevel = 0
        self.magicLevel = 0
        # Affix details - number, min/max quality, min/max limits, allowed
        # types, and any automatic affixes
        self.numAffixes = 0
        self.minAffixLevel = None
        self.maxAffixLevel = None
        self.affixLimits = {}
        self.affixType = {}
        self.affixes = []
        # Theme details - normal chance, allowed themes and
        # and specified theme
        self.themeChance = 1
        self.themes = []
        self.themeName = None
        # Artifact details - normal chance and any specified name
        self.artifactChance = 1
        self.artifactName = None

        # Build a full record based on the current object and all ancestor templates.
        completeRecord = util.record.buildRecord(self, itemLoader.getLootTemplate)
        # Apply that record to ourselves, setting appropriate attributes in place.
        util.record.applyRecord(self, completeRecord)


    ## Resolve boostedDie values in the template, so they can be used.
    def resolveValues(self, itemLevel):
        # \todo Construct a tester for boostedDie that returns whether a
        # string is a valid boostedDie formula. Use this to iterate over all
        # members of self and avoid overwriting other strings.
        self.itemLevel = util.boostedDie.roll(self.itemLevel)
        self.magicLevel = util.boostedDie.roll(self.magicLevel)
        self.numAffixes = util.boostedDie.roll(self.numAffixes)


    ## Apply the 'itemRuleBoosts' in the template to the relevant rules. This
    # allows for some variety within a given template, e.g. so that some
    # 'good' items are better than others.
    def applyItemRuleBoosts(self, mapLevel):
        if not self.itemRuleBoosts:
            # No boosts to apply - set defaults
            self.itemLevel = mapLevel
            self.magicLevel = mapLevel
            return
        # Set up the dictionary of variables used when evaluating expressions
        variables = {'mapLevel': mapLevel}
        # Check for an itemLevel boost first, as this will be used by others
        if 'itemLevel' in self.itemRuleBoosts:
            for pair in self.itemRuleBoosts['itemLevel']:
                chance, amount = pair.split(';')
                if random.random() * 100 < util.evaluator.run(chance, variables):
                    mapLevel += util.boostedDie.BoostedDie(amount).roll()
        # If magicLevel is not specified, assign its default value prior to
        # boosting
        if not self.magicLevel:
            self.magicLevel = mapLevel
        # Iterate over all itemRuleBoosts
        for key, value in self.itemRuleBoosts.iteritems():
            for pair in value:
                chance, amount = pair.split(';')
                if random.random() * 100 < util.evaluator.run(chance, variables):
                    result = util.boostedDie.BoostedDie(amount).roll()
                    if key == 'minAffixLevel' or key == 'maxAffixLevel':
                        self.adjustAffixLevels(key, result)
                    if key == 'magicLevel':
                        self.magicLevel += result
                    if key == 'numAffixes':
                        self.numAffixes += result
                    if key == 'themeChance':
                        self.themeChance += result
                    if key == 'artifactChance':
                        self.artifactChance += result
                    if key == 'numDrops':
                        self.numDrops += result
                    if key == 'dropChance':
                        self.dropChance += result
        # Assign the correct itemLevel (to avoid doubling any boost)
        self.itemLevel = mapLevel


    ## Deal with affix level adjustments, converting to and from text. We
    # assume that the lowest affix level has rank 0, but we want to avoid
    # hard-coding a highest level. 
    def adjustAffixLevels(self, which, amount):
        if which == 'minAffixLevel':
            current = itemLoader.AFFIX_LEVELS[self.minAffixLevel]['rank']
        elif which == 'maxAffixLevel':
            current = itemLoader.AFFIX_LEVELS[self.maxAffixLevel]['rank']
        else:
            raise RuntimeError("invalid argument passed to adjustAffixLevels")
        current += amount
        if current < 0:
            current = 0
        # Check whether new value is valid
        valid = False
        while not valid:
            for level, details in itemLoader.AFFIX_LEVELS.iteritems():
                if details['rank'] == current:
                    setattr(self, which, level)
                    valid = True
                    break
            if valid:
                break
            # It's not, so we try again
            current -= 1
            if current < 0:
                raise RuntimeError("Major problem with affix levels")
