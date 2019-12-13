## Various utility functions for doing random actions.

import random

## Return true if we roll below the provided value on a floating-point d100.
# This allows for non-integer percentages, which can be useful.
def passPercentage(percent):
    return random.random() * 100 < percent


## Return the result of rolling dice.
def rollDice(numDice, dieSize):
    if not (numDice and dieSize):
        return 0
    return sum([random.randint(1, dieSize) for i in xrange(numDice)])


## Return true if an event with odds of 1 in N occurs.
def oneIn(ceiling):
    return random.randint(0, int(ceiling)) == 0
