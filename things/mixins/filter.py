import util.extend

## A filter for valid item selections, based on the categories an
# item belongs to.
# allowCategories and denyCategories can specify any category of
# any level of granularity (eg: allow 'armor', deny 'chain mail').
# An empty allowCategories is considered to be 'all'.
# An empty denyCategories is considered to be 'none'.
# 'all' is a special value for either category type.
class ItemFilter:
    def __init__(self):
        # Set of categories that we allow
        self.allowCategories = util.extend.Categories()
        # Set of categories that we don't allow
        self.denyCategories = util.extend.Categories()


    ## Return true if the item containing the provided
    #  categories passes the filters contained in this
    #  filter object (allowCategories, denyCategories).
    def isValidItem(self, itemCategories):
        # If no filters specified, allow anything.
        if not self.denyCategories and not self.allowCategories:
            return True

        # Filter on deny first, then allow
        # This allows for A except B type rules

        # Check for a global block first
        if self.denyCategories.has("all"):
            return False
        # If any of the item categories are in our deny rules, block.
        if self.denyCategories.has(itemCategories):
            return False

        # Have checked deny; check for universal allow
        # If nothing specific allowed, treat as 'all'.
        if not self.allowCategories or self.allowCategories.has("all"):
            return True
        # If any of the item categories are in our allow rules, pass.
        if self.allowCategories.has(itemCategories):
            return True

        # Block anything else
        return False



## A filter for valid affix selections.
# As above, allow or deny an affix based on rules present.
# For affixes, however, there are subcategories per affix type.
# Because of this, the use of the categories class isn't viable.
# These types may be specified for a known type, or for any 'unknown' type.
# The contents of each subcategory may either be a list, or, for simplicity,
# a single string value (eg: "all").
class AffixFilter:
    def __init__(self):
        # Ensure that the affix rule dicts exist.
        self.allowAffixes = {}
        self.denyAffixes = {}


    ## Return True if we are allowing this affix.
    def isValidAffix(self, affixType, affixName):
        # No affix type specified, so anything goes.
        if not self.affixType:
            return True
            
        # Pull out the per-type rules to apply
        if affixType in denyAffixes:
            denyOfType = denyAffixes[affixType]
        elif 'unknown' in denyAffixes:
            denyOfType = denyAffixes['unknown']
        
        if affixType in allowAffixes:
            allowOfType = allowAffixes[affixType]
        elif 'unknown' in allowAffixes:
            allowOfType = allowAffixes['unknown']
            
        # If no rules for the type are specified, allow anything.
        if not allowOfType and not denyOfType:
            return True
            
        # First check deny and block anything in that list.
        # If 'all' is listed, block everything.
        # If no deny list is present, skip to allow check.
        if denyOfType:
            if denyOfType == "all" or "all" in denyOfType:
                return False
            elif denyOfType == affixName or affixName in denyOfType:
                return False
                
        # Then check allow and pass anything in that list.
        # If 'all' is listed, allow anything past.
        # If no allow list present, allow anything past.
        if allowOfType:
            if allowOfType == "all" or "all" in allowOfType:
                return True
            elif allowOfType == affixName or affixName in allowOfType:
                return True
        else:
            return True
            
        # If it failed to pass the allow list, deny.
        return False



## A filter for valid theme selections, based on specified
# categories allowThemes and denyThemes.
# An empty allowThemes is considered to be 'all'.
# An empty denyThemes is considered to be 'none'.
# 'all' is a special value for either category type.
class ThemeFilter:
    def __init__(self):
        # Ensure that a list of themes exists, even if empty
        self.allowThemes = util.extend.Categories()
        self.denyThemes = util.extend.Categories()


    ## Return True if we are allowing this theme.
    def isValidTheme(self, themeName):
        # If no filters specified, allow anything.
        if not self.denyThemes and not self.allowThemes:
            return True

        # Filter on deny first, then allow
        # This allows for A except B type rules

        # Check for a global block first
        if self.denyThemes.has("all"):
            return False
        # If any of the item categories are in our deny rules, block.
        if self.denyThemes.has(themeName):
            return False

        # Have checked deny; check for universal allow
        # If nothing specific allowed, treat as 'all'.
        if not self.allowThemes() or self.allowThemes.has("all"):
            return True
        # If any of the item categories are in our allow rules, pass.
        if self.allowThemes.has(themeName):
            return True

        # Block anything else
        return False

