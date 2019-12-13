import allocatorRules
import itemLoader

import collections
import random

## ItemAllocators are used to generate items of a desired level, with potential
# filters applied as well.
class ItemAllocator:
    def __init__(self, itemLevel, lootRules = None):
        # a dictionary of rules for item generation
        if lootRules is None:
            self.lootRules = None
            self.itemLevel = itemLevel
        else:
            self.lootRules = lootRules
            # If itemLevel is set in the loot template, we override the
            # passed-in itemLevel
            if self.lootRules.itemLevel:
                itemLevel = self.lootRules.itemLevel
            # Apply the random elements of the template
            self.lootRules.applyItemRuleBoosts(itemLevel)
            # Now set the final item level
            self.itemLevel = self.lootRules.itemLevel

        ## List of (commonness, ItemFactory) tuples, where "commonness" is a
        # number indicating how common the item is (larger = more common).
        self.allocationTable = []
        ## This is the sum of all commonness values for all valid items.
        self.maxRoll = 0

        
    ## \param owner A Container that holds the newly-created Item.
    def allocate(self, gameMap, owner):
        # Check for artifact creation specified in lootRules
        artifactChance = 1
        if self.lootRules:
            if self.lootRules.artifactName:
                artifact = itemLoader.getFactory(self.lootRules.artifactName)
                result = artifact.makeItem(self.itemLevel, gameMap)
                gameMap.addSubscriber(result, owner.id)
                return result
            artifactChance = self.lootRules.artifactChance

        # So we're not generating a specific artifact - now we choose an item
        if not self.allocationTable:
            # Generate the allocation table now. Iterate over all possible
            # items, including artifacts, decide if they're valid using the
            # filters, and insert them into the list.
            for factory in itemLoader.ITEM_FACTORY_MAP.values():
                if self.lootRules and not self.lootRules.isValidItem(factory.categories):
                    # Item is not valid; skip it.
                    continue
                # Check whether this factory is for creating an artifact
                isArtifact = False
                if factory.categories.has('artifact'):
                    if factory.artifactCreated:
                        # We've already created this artifact, so skip it
                        continue
                    isArtifact = True
                # Find the most applicable allocatorRule entry.
                bestRule = None
                for rule in factory.allocatorRules:
                    if rule.isValidAtItemLevel(self.itemLevel):
                        if bestRule is None or bestRule.commonness < rule.commonness:
                            bestRule = rule
                if bestRule is not None:
                    finalCommonness = bestRule.commonness
                    if isArtifact:
                        # Multiply commonness by artifactChance
                        finalCommonness = bestRule.commonness * artifactChance
                    self.allocationTable.append((finalCommonness, factory))
                    self.maxRoll += finalCommonness
            # Sort the table so the most common items are first, to make
            # repeated allocations faster.
            self.allocationTable.sort(lambda a, b: cmp(a[0], b[0]))
        
        roll = random.random() * self.maxRoll
        for commonness, factory in self.allocationTable:
            roll -= commonness
            if roll <= 0:
                result = factory.makeItem(self.itemLevel, gameMap,
                        lootRules = self.lootRules)
                gameMap.addSubscriber(result, owner.id)
                return result
            
        raise RuntimeError("Got an invalid roll %d for our item allocation table (nominal max %d)." % (roll, self.maxRoll))



## Affix allocators are used to generate tables of valid affixes for a 
# particular item with specified rules
class AffixAllocator:
    def __init__(self, itemCategories, lootRules, limits = None, itemAffixes = []):
        ## Effective generation depth (n.b. may not be actual depth)
        self.itemLevel = lootRules.magicLevel
        # The other loot rules
        self.lootRules = lootRules
        # Categories of the item for which we are selecting affixes
        self.itemCategories = itemCategories
        # Minimum and maximum affix type and level requirements
        if limits is None:
            # Instantiate an empty limits object
            self.limits = allocatorRules.AffixLimits({})
        else:
            self.limits = limits
        # Affixes already on the item, if any
        self.itemAffixes = itemAffixes
        # List of (commonness, affix) tuples
        self.allocationTable = []
        ## This is the sum of all commonness values for all valid affixes.
        self.maxRoll = 0


    ## Create the allocation table (if necessary) and choose the affix
    def allocate(self):
        if not self.allocationTable:
            # Count the types and levels of affixes already on the item, so
            # we can use these counts in the coming loops
            existingTypes = collections.Counter()
            existingLevels = collections.Counter()
            for existingAffix in self.itemAffixes:
                existingTypes[existingAffix['affixType']] += 1
                existingLevels[existingAffix['affixLevel']] += 1
            # Generate the allocation table now. Iterate over all possible
            # affixes, decide if they're valid, and insert valid ones
            # into the list.
            for affix in itemLoader.AFFIX_NAME_MAP.values():
                # Find the most applicable allocatorRule entry.
                bestRule = None
                # Check for minimum required affix types - discard affixes
                # that aren't part of any min requirements
                if (self.limits.typesMin and
                        affix.affixType not in self.limits.typesMin):
                    continue
                # Check for maximum allowed affix types - discard affixes that
                # violate them
                if (self.limits.typesMax and
                        affix.affixType in self.limits.typesMax and
                        existingTypes[affix.affixType] >=
                        self.limits.typesMax[affix.affixType]):
                    continue
                # Check for conflicts with affixes already on the item
                hasAffixConflict = False
                for existingAffix in self.itemAffixes:
                    if existingAffix['name'] in affix.conflicts:
                        hasAffixConflict = True
                        break
                if hasAffixConflict:
                    continue
                # Check against affixes specified in lootRules
                if not self.lootRules.isValidAffix(affix.affixType, affix.name):
                    continue

                # The affix itself is valid so we check its allocation rules
                for rule in affix.allocatorRules:
                    # Meet minimum requirements first - discard all rules that
                    # aren't part of any min requirements
                    if (self.limits.levelsMin and
                            rule.affixLevel not in self.limits.levelsMin):
                        continue
                    # Check against maxima - discard rules that violate them
                    if (self.limits.levelsMax and
                            rule.affixLevel in self.limits.levelsMax and
                            existingLevels[rule.affixLevel] >=
                            self.limits.levelsMax[rule.affixLevel]):
                        continue

                    # Check other constraints
                    if (rule.isValidAtItemLevel(self.itemLevel) and
                            rule.isValidAffixLevel(self.limits.minAffixLevel,
                            self.limits.maxAffixLevel) and
                            rule.isValidItem(self.itemCategories)):
                        # Finally, a valid rule! We use the best commonness
                        if bestRule is None or bestRule.commonness < rule.commonness:
                            bestRule = rule
                if bestRule is not None:
                    affix.affixLevel = bestRule.affixLevel
                    self.allocationTable.append((bestRule.commonness, affix))
                    self.maxRoll += bestRule.commonness
            # Sort the table so the most common affixes are first, to make
            # repeated allocations faster.
            self.allocationTable.sort(lambda a, b: cmp(a[0], b[0]))

        # Drop out if we have no available affixes
        if self.maxRoll == 0:
            return None

        # Select the affix from the allocation table and return it
        roll = random.random() * self.maxRoll
        for commonness, affix in self.allocationTable:
            roll -= commonness
            if roll <= 0:
                return affix
            
        raise RuntimeError("Got an invalid roll %d for our affix allocation table (nominal max %d)." % (roll, self.maxRoll))



## Theme allocators are used to generate tables of valid themes for a 
# particular item with specified rules
class ThemeAllocator:
    def __init__(self, itemCategories, lootRules, itemAffixes = []):
        ## Effective generation depth (n.b. may not be actual depth)
        self.itemLevel = lootRules.magicLevel
        # The other loot rules
        self.lootRules = lootRules
        # Categories of the item for which we are selecting a theme
        self.itemCategories = itemCategories
        # Affixes already on the item, if any
        self.itemAffixes = itemAffixes
        # List of (commonness, theme) tuples
        self.allocationTable = []
        ## This is the sum of all commonness values for all valid themes.
        self.maxRoll = 0


    ## Create the allocation table (if necessary) and choose the theme
    def allocate(self):
        if not self.allocationTable:
            # Generate the allocation table now. Iterate over all possible
            # themes, decide if they're valid, and insert valid ones
            # into the list.
            for theme in itemLoader.THEME_NAME_MAP.values():
                # Check against themes specified in lootRules
                if not self.lootRules.isValidTheme(theme.name):
                    continue

                isValid = False
                # The theme itself is valid so we check its allocation rules
                for rule in theme.allocatorRules:
                    if (rule.isValidAtItemLevel(self.itemLevel) and
                            rule.isValidItem(self.itemCategories)):
                        isValid = True
                        
                if not isValid:
                    continue
                        
                # Now we check for relevant affixes
                totalCount = 0
                totalWeight = 0
                themeWeight = 0
                # Iterate over all affixes listed in the theme 
                for themeAffix in theme.affixes:
                    count = 0
                    # Weighting is a list of likelihoods of selecting
                    # this affix, because affixes can be relevant to a
                    # theme more than once.
                    weighting = themeAffix['weighting']
                    if type(weighting) is not list:
                        weighting = [weighting]
                    themeWeight += sum(weighting)
                    # If it's on the item, add the correct weighting
                    for itemAffix in self.itemAffixes:
                        if itemAffix['name'] == themeAffix['name']:
                            count += 1
                            if count and count <= len(weighting):
                                totalWeight += weighting[count - 1]
                    if count:
                        totalCount += 1

                # If we have two or more relevant affixes, add us to the table                                
                if totalCount > 1:
                    # This is the formula used to determine chance of a theme
                    commonness = float(8 * totalWeight ** 2) / themeWeight
                    self.allocationTable.append((commonness, theme))
                    self.maxRoll += commonness
            # Sort the table so the most common themes are first, to make
            # repeated allocations faster.
            self.allocationTable.sort()

        # Drop out if we have no available themes:
        if self.maxRoll == 0:
            return None

        # Select the theme from the allocation table and return it
        # But use a standard maxRoll of 200 so if the table is small
        # we may still get no theme. The 200 is modifiable by lootRules,
        # whose themeChance defaults to 100.
        roll = random.random() * max(self.maxRoll, 20000 /
                                     self.lootRules.themeChance)
        for commonness, theme in self.allocationTable:
            roll -= commonness
            if roll <= 0:
                return theme
        # So there were themes available, but we rolled too high and didn't
        # get one
        return None
