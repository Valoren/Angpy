# coding=latin-1
## This module handles mapping flavor names to the colors for those names.

import string
import json
import os
import random

colorRecords = json.load(open(os.path.join('data', 'flavor_colors.txt'), 'r'))
typeRecords = json.load(open(os.path.join('data', 'flavor_types.txt'), 'r'))

## Maps flavor names to colors for those flavors.
FLAVOR_COLOR_MAP = {}
## Maps flavor categories to lists of flavor names.
FLAVOR_CATEGORY_MAP = {}
## Maps item base types to lists of flavor names.
FLAVOR_TYPE_MAP = {}

for record in colorRecords:
    FLAVOR_CATEGORY_MAP[record['type']] = record['flavors'].keys()
    for key, value in record['flavors'].iteritems():
        FLAVOR_COLOR_MAP[key] = value
for key, value in typeRecords.iteritems():
    FLAVOR_TYPE_MAP[key] = value


def getColorNameForFlavor(flavor):
    if flavor not in FLAVOR_COLOR_MAP:
        raise RuntimeError("Unrecognized flavor name [%s]" % flavor)
    return FLAVOR_COLOR_MAP[flavor]


def getFlavorsForCategory(category):
    if category not in FLAVOR_CATEGORY_MAP:
        raise RuntimeError("Unrecognized flavor category [%s]" % category)
    return FLAVOR_CATEGORY_MAP[category]


## Select a random flavor for an item of the given type.
# \todo This is probably the wrong place to do this, since we need to always
# choose the same flavor for a given item type in a given game. 
def chooseFlavorForItemType(type):
    if type not in FLAVOR_TYPE_MAP:
        raise RuntimeError("No known flavors for items of type [%s]" % type)
    categories = FLAVOR_TYPE_MAP[type]
    allFlavors = []
    for category in categories:
        allFlavors.extend(getFlavorsForCategory(category))
    return random.choice(allFlavors)


## Select a random flavor for an item of the given type.
# \todo This is probably the wrong place to do this, since we need to always
# choose the same flavor for a given item type in a given game. 
def chooseFlavorFromCategory(categories):
    allFlavors = []
    # First check for procedurally generated category types.
    for category in categories:
        if category not in FLAVOR_CATEGORY_MAP:
            raise RuntimeError("Unrecognized flavor category [%s]" % category)
        if "procedure" in FLAVOR_CATEGORY_MAP[category]:
            return procedurals[category]()
        else:
            allFlavors.extend(getFlavorsForCategory(category))

    return random.choice(allFlavors)


consonants = u"bcdfghjklmnpqrstvwxz"
# Repeat basic vowels to give them more weight in random selection
vowels = u"aeiouaeiouaeiouaeiouaeiouaeiouyyyàáâãäåæèéêëìíîïðòóôõöøùúûü"
consonantList = list(consonants)
vowelList = list(vowels)

## Generate a random or pseudo-random bit of text to use for flavor.
def generateTitle():
    # 1 to 3 words, of 2 to 7 characters, but no more than 14
    # chars across all words
    numWords = random.randint(1, 3)
    charsPerWord = []
    totalChars = 0
    for i in range(0, numWords):
        charsPerWord.append(random.randint(2, 7))

    totalChars = sum(charsPerWord)
    if totalChars > 14:
        charsPerWord[-1] -= totalChars - 14
        if charsPerWord[-1] < 1:
            charsPerWord.pop()

    words = []
    for wordChars in charsPerWord:
        word = u''
        for i in range(0, wordChars):
            shouldChooseVowel = random.randint(0, 1)
            if shouldChooseVowel:
                char = random.choice(vowelList)
            else:
                char = random.choice(consonantList)
            word += char
        words.append(word)

    # Put all the words together into a single string.
    title = u" ".join(map(unicode, words))

    result = u'&titled "%s"' % title
    return result

# Mapping of categories to procedural functions that generate that flavor type.
# Keep at the bottom of the file so that any referenced functions are defined
# before we get here.
procedurals = {"Titles": generateTitle}


