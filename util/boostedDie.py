## Simple class for rolling dice, with the option to apply various mods to 
# them. 

import random

class BoostedDie:
    ## \param definition A string describing the die roll, in the format
    # "A+XdYMZ", where A, X, Y, and Z are (optionally-negative) integers.
    # Note that we can accept empty strings, in which case we always return 0.
    # We also accept a single number, for a constant result.
    def __init__(self, definition):
        self.flatBonus = self.scaledBonus = self.numDice = self.dieSize = 0
        if (type(definition) is int or 
                (definition and '+' not in definition and 
                    'd' not in definition and 'M' not in definition)):
            # Just handed us a single value.
            self.flatBonus = definition
        else:
            if '+' in definition:
                self.flatBonus, definition = definition.split('+')
            if 'M' in definition:
                definition, self.scaledBonus = definition.split('M')
            if definition:
                self.numDice, self.dieSize = definition.split('d')
                if not self.numDice:
                    # Handle "d10" as an implicit "1d10"
                    self.numDice = 1
                elif self.numDice == '-':
                    # Handle "-d10" as an implicit "-1d10"
                    self.numDice = -1
        ## Number of dice to roll. Positive integer.
        self.numDice = int(self.numDice)
        ## Size of the dice to roll. Positive integer
        self.dieSize = int(self.dieSize)
        ## Constant integer to add to the result. May be negative.
        self.flatBonus = int(self.flatBonus)
        ## Integer that scales with depth.
        self.scaledBonus = int(self.scaledBonus)


    ## Return true if we could possibly return any nonzero value.
    def getAmRelevant(self):
        return self.flatBonus or (self.numDice and self.dieSize) or self.scaledBonus


    ## Return a result from rolling our values.
    # \param shouldMaximize If True, then all die rolls are the maximum possible
    # value.
    def roll(self, level = None, shouldMaximize = False):
        if shouldMaximize:
            total = self.dieSize * self.numDice
        else:
            total = sum([random.randint(1, self.dieSize) for i in xrange(abs(self.numDice))])
        if self.numDice < 0:
            # Handle "negative dice"
            total *= -1
        total += self.flatBonus
        if level is not None:
            # Add a depth-depedent bonus.
            # \todo For now we're just making this a linearly-scaled result.
            total += int(self.scaledBonus * level / 100)
        return total


    ## Convert back to a string for storage.
    def serialize(self):
        result = ''
        if self.flatBonus:
            result += '%s' % self.flatBonus
            if self.numDice or self.dieSize or self.scaledBonus:
                result += '+'
        if self.numDice or self.dieSize:
            if self.numDice > 1:
                result += str(self.numDice)
            result += 'd%s' % self.dieSize
        if self.scaledBonus:
            result += 'M%s' % self.scaledBonus
        return result


## Create and roll a BoostedDie in a single function.
def roll(dieDesc, level = None, shouldMaximize = False):
    return BoostedDie(dieDesc).roll(level, shouldMaximize)
