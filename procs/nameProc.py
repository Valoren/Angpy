import proc
import util.grammar
import util.extend
import things.items.item

# Procs triggered when constructing item names

# pass itemRecord.nameInfo in params

## Default namer class for most items
class DefaultItemNamer(proc.Proc):
    def trigger(self, item, quantity, alterNameCallbacks = None, **kwargs):
        return getItemName(item, quantity, alterNameCallbacks, **self.params)



## Default namer class for unique items
class UniqueItemNamer(DefaultItemNamer):
    def trigger(self, item, quantity, alterNameCallbacks = None, **kwargs):
        return getItemName(item, quantity, alterNameCallbacks, isUnique = True, **self.params)



## Generates names for spell objects.
class SpellItemNamer(proc.Proc):
    def trigger(self, item, quantity, alterNameCallbacks = None, **kwargs):
        # \todo Include cost, failure rate, spell info.
        return item.nameInfo.get('variantName', 'No name specified')


## Function to handle actually creating an item's name, called via
#  one of the above procs.
#
# \param item - The item we're getting the name for.
# \param quantity - The quantity to display.
# \param alterNameCallbacks - List of callback functions
#       that can change anything about the item's description.
#       Called after all other construction calculations are done,
#       so it can tweak just specific aspects of the final description.
#       Descriptors indicating a change in state should be inserted at
#       the front of the modAdjectives list.
# -- Vars for the parts of the item's name:
# "set of gloves" >> "set of" (modifier) "gloves" (base)
# \param baseNoun - required
# \param modifierNoun
# \param variantName - Any specified differentiating type for the item.
# \param properName - The special name/origin of the item.
# \param flavorPosition - The position that any flavor text should be placed in.
# \param isUnique - Whether this is a unique item.
# \param otherParams - Any other params provided by the original params
#        object that we don't care about.
def getItemName(item, quantity, alterNameCallbacks = None,
                baseNoun = None,
                modifierNoun = None,
                variantName = None,
                properName = None,
                flavorPosition = 'basePrefix',
                isUnique = False,
                **otherParams):

    # Trying to create a name proc for an item without a base
    # noun will generate an error.  Any other field is optional.
    if not baseNoun:
        raise RuntimeError("Item has no base noun.")

    baseAdjectives = []
    modAdjectives = []
    suffixList = []

    # Cache the results of the calculations

    if item.cachedDescription:
        modAdjectives = item.cachedDescription['modAdjectives']
        baseAdjectives = item.cachedDescription['baseAdjectives']
        suffixList = item.cachedDescription['suffixList']
    else:
        # uncached, create from scratch

        # Affixes:
        # Each affix is defined with a position and a position distance.
        # The default for these values is drawn from its respective
        # affixType, but can be overridden as needed.
        #
        # Positions:
        # modPrefix - goes before the modifier noun
        # -- state, quality
        # basePrefix - goes after the modifier noun, but before the base noun
        # -- most flavors, material, make
        # suffix - goes after the base noun.
        # -- alt make, combat, physical, mental, elemental, arcane, holy, 
        #    any affix without an affix type, and postfix flavors
        #
        # Position Distance:
        # Numerical value indicating the relative distance from the noun
        # being modified that this affix is intended to be placed.
        # Generally a value of 1 means 'immediately adjacent', while
        # each number higher than that gets further away.
        # Any affix without a specified distance or affix type is given
        # a distance of 100.

        # If given a proper name, that's the only thing we'll use for constructing
        # the final output.  Otherwise, work through all the details.
        if properName:
            suffixList.append(properName)
        else:
            # Themes get defined and placed according to the theme type and contents.
            # If item has a theme, pull out theme information.
            # The theme supplants anything else that might get put in its
            # respective position.
            if item.theme:
                if item.theme['position'] == 'prefix':
                    # Get all prefix-based affixes that the theme generates, and use
                    # that to determine the overall position the theme name should hold.
                    themePrefixes = [a for a in item.affixes if a['isThemed'] == True]
                    themeBasePrefixes = [a for a in themePrefixes if a['position'] == 'basePrefix']
                    themeModPrefixes = [a for a in themePrefixes if a['position'] == 'modPrefix']
                    if len(themeBasePrefixes) > len(themeModPrefixes):
                        baseAdjectives = [theme['name']]
                    else:
                        modAdjectives = [theme['name']]
                elif item.theme['position'] == 'suffix':
                    suffixList = [theme['name']]

            # If no theme was inserted into the various adjective lists, fill them
            # out based on the affixes' position and positionDistance.

            nonThemeAffixes = [a for a in item.affixes if a['isThemed'] == False]

            # Loop through all the different position lists and fill them in
            for adjTuple in [(modAdjectives, 'modPrefix', True),
                             (baseAdjectives, 'basePrefix', True),
                             (suffixList, 'suffix', False)]:

                adjs = adjTuple[0]

                # Skip loop if we already added a theme to this adjective list
                if adjs:
                    continue

                position = adjTuple[1]
                reverse = adjTuple[2]

                # Get the affixes that are available for this position
                affixes = [a for a in nonThemeAffixes if a['position'] == position]

                # Add the flavor value, if appropriate.  Set at max distance.
                if item.flavor and flavorPosition == position:
                    affixes.append({'name': item.flavor, 'positionDistance': 101, 'genus': ''})

                # Add the variant as the first suffix value, if present
                if adjs is suffixList and variantName:
                    affixes.append({'name': variantName, 'positionDistance': 0, 'genus': ''})

                # If we have any affixes at this point, proceed
                if affixes:
                    # Group affixes by distance
                    affixesByDistance = util.extend.groupBySortedByKey(
                            affixes, key=lambda a: a['positionDistance'], shouldReverseOrder = reverse)

                    # For each distance grouping, either add the affix name to the output list,
                    # or get the most popular genus from the available affixes.
                    for distanceGroup in affixesByDistance:
                        # If there's only one affix at a given distance, use its name.
                        if len(distanceGroup) == 1:
                            adjs.append(distanceGroup[0]['name'])
                        # Otherwise, get the most common genus within the group
                        else:
                            genusGroups = util.extend.groupBySortedByCount(distanceGroup, key=lambda a: a['genus'])
                            # The most common group is at the end of the list
                            mostCommon = genusGroups[-1]
                            # Get the value from the first item in the list
                            genus = mostCommon[0]['genus']
                            if genus:
                                adjs.append(genus)
                            else:
                                # Fallback if the most common is no genus
                                adjs.append(mostCommon[0]['name'])

            # \todo - Uncomment this when confident of stability of the code.
            # Store construction results in item cache
            #item.cachedDescription.update({'modAdjectives': modAdjectives,
            #                               'baseAdjectives': baseAdjectives,
            #                               'suffixList': suffixList})

    # Allow specification of a modifyCallback function that may modify
    # any aspect of the item's description.  This occurs regardless of
    # what was determined above.
    # \todo: Function call also needs to restrict based on player knowledge.
    if alterNameCallbacks:
        for alterCallback in alterNameCallbacks:
            if callable(alterCallback):
                # Store current values
                descriptors = dict({'modAdjectives': modAdjectives,
                                    'modifierNoun': modifierNoun,
                                    'baseAdjectives': baseAdjectives,
                                    'baseNoun': baseNoun,
                                    'properName': properName,
                                    'variantName': variantName,
                                    'suffixList': suffixList})

                alterCallback(item, descriptors)

                # Retrieve any changes.
                modAdjectives = descriptors['modAdjectives']
                modifierNoun = descriptors['modifierNoun']
                baseAdjectives = descriptors['baseAdjectives']
                baseNoun = descriptors['baseNoun']
                properName = descriptors['properName']
                variantName = descriptors['variantName']
                suffixList = descriptors['suffixList']

    # All done figuring out the pieces of the item name.
    # Let grammar put it together, and return the value.
    return util.grammar.getFullItemName(baseNoun = baseNoun,
                                        baseAdjectives = baseAdjectives,
                                        modifierNoun = modifierNoun,
                                        modAdjectives = modAdjectives,
                                        suffixList = suffixList,
                                        quantity = quantity,
                                        isUnique = isUnique)


