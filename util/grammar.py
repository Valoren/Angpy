# coding=utf-8
## Grammar utilities

import string

# Constants:

## Not all these letters are actually in the English language, but what with all the borrowed words...
vowels = u'aeiouàáâãäåæèéêëìíîïðòóôõöøùúûüāăąēĕėęěĩīĭįıĳōŏőœũūŭůűų'


## Generate the appropriate plural form of the given word, based on the quantity.
# Formatting for names to account for plurality:
# 
# sheep
# horse~
# knife:knives
# 
# 'sheep' doesn't get modified when plural.  Returns same value regardless of quantity.
# 'horse~' appends an 's' in place of the ~ when plural.  1 = 'horse', 2+ = 'horses'
# 'knife:knives' explicity states the plural form.  Anything before the colon for 1, anything after for 2+.
def makePlural(basename, quantity):
    if not isinstance(basename, basestring):
        raise RuntimeError("Provided basename is not a string.")
    if not isinstance(quantity, int):
        raise RuntimeError("Provided quantity is not a number.")
    if quantity < 0:
        raise RuntimeError("Invalid quantity: %d" % quantity)

    if u'~' in basename:
        if quantity == 1:
            return basename.replace(u'~', u'')
        return basename.replace(u'~', u's')
    elif u':' in basename:
        parts = basename.split(u':')
        if quantity == 1 or len(parts) == 1:
            return parts[0]
        return parts[1]
    else:
        return basename


## Get the article to use with the provided word phrase, based on quantity and
#  whether we're using the definite article or not.
# \param phrase - the word phrase the article is being applied to
# \param quantity - the quantity of the word in question
# \param shouldUseDefiniteArticle - indicate whether to use a definite rather than
#       indefinite article
def getArticle(phrase, quantity = 1, shouldUseDefiniteArticle = False):
    if not isinstance(phrase, basestring):
        raise RuntimeError("Provided phrase is not a string.")
    if not isinstance(quantity, int):
        raise RuntimeError("Provided quantity is not a number.")
    if quantity < 0:
        raise RuntimeError("Invalid quantity: %d" % quantity)

    # In the case of quantity 0, the 'article' to be used depends on
    # the message context.  We therefore don't specify anything here.
    if quantity == 0:
        return u''
    elif quantity > 1:
        return unicode(quantity);

    if shouldUseDefiniteArticle:
        return u'the'

    # \todo - This won't always return the proper form for a word starting
    # with a vowel (eg: uranium).
    if phrase[0].lower() in vowels:
        return u'an'
    else:
        return u'a'


## Maps second-person conjugations of verbs to third-person conjugations.
VERB_CONJUGATION_MAP = {
        'are': 'is',
        'cannot': 'cannot',
        'have': 'has',
}


## Generate a conjugated sentence based on the provided input sentence and
# objects. Example:
# getConjugatedPhrase("{creature} {verb} {creature}.", source, "attack", target)
# -> 
# "You attack the yellow mold".
# or
# "The filthy street urchin attacks you".
# Words in curly braces are replaced by the following arguments in sequence
# (so the first argument replaces the first curly-braced word, etc.), but
# modified so that the sentence makes grammatical sense. 
# Supported control words: {creature}, {verb}, {item}.
# We assume that the most recent creature to appear in a sentence is the 
# subject performing any verbs. 
# Verbs that have unusual conjugations (i.e. third-person is not just "add an
# 's' at the end) are looked up in a conjugation dictionary; the verb passed
# in as an argument should be in its second-person form (e.g. "have" instead of
# "has"). Only second- and third-person singular conjugations are supported.
def getConjugatedPhrase(phrase, gameMap, *args):
    # List of (string, shouldConjugate) pairs.
    tokens = []
    curOffset = 0
    # Divide up the phrase into sections we need to modify and sections that
    # can go straight into the result.
    while phrase.find('{', curOffset) != -1:
        nextCurly = phrase.find('{', curOffset)
        # Get the unmodifiable text to this point.
        tokens.append((phrase[curOffset:nextCurly], False))
        # Find the close-curly.
        closeCurly = phrase.find('}', nextCurly)
        if closeCurly == -1:
            raise RuntimeError("'{' without corresponding '}' in phrase [%s]" % phrase)
        tokens.append((phrase[nextCurly + 1 : closeCurly], True))
        curOffset = closeCurly + 1
    tokens.append((phrase[curOffset:], False))

    # Generate the result phrase, performing conjugations as we go.
    result = []
    argOffset = 0
    lastCreature = None
    player = gameMap.getPlayer()
    for i, (token, shouldConjugate) in enumerate(tokens):
        if not shouldConjugate:
            result.append(token)
            continue
        if token == 'creature':
            # Insert the creature's name, as well as an article if necessary.
            if player is args[argOffset]:
                result.append('you')
            else:
                # Decide between a definite article or no article, depending 
                # on if the target is unique.
                creature = args[argOffset]
                if not creature.categories.has('unique'):
                    result.append('the %s' % creature.name)
                else:
                    result.append(creature.name)
            lastCreature = args[argOffset]
        elif token == 'verb':
            # Insert the verb. Verbs are provided in second-person by default;
            # if the actor is not the player, then we need to switch to third
            # person, either by looking up the appropriate form in our dict,
            # or by just tacking an 's' on the end.
            verb = args[argOffset]
            if player is lastCreature:
                result.append(verb)
            else:
                # Check for existing conjugation.
                if verb in VERB_CONJUGATION_MAP:
                    verb = VERB_CONJUGATION_MAP[verb]
                else:
                    verb = verb + 's'
                result.append(verb)
        elif token == 'item':
            # Insert the item's name.
            result.append(args[argOffset].getShortDescription())
        argOffset += 1
    return ''.join(result).capitalize()


##Get a fully constructed item name based on the provided parts of speech.
# \param baseNoun - The fundamental noun of the item
# \param baseAdjectives - List of adjectives to apply to the baseNoun
# \param modifierNoun - A noun that can modify the base noun (and should
#        be placed before the baseAdjectives)
# \param modAdjectives - List of adjectives to apply to the modifierNoun
#        (or just extend the number being applied to the base noun)
# \param itemName - The proper 'name' of the item. Placed after the base noun
# \param suffixList - List of suffixes to add after the base noun, if
#        the item doesn't have a proper name.
# \param quantity - The quantity of the item, which determines the article
# \param unique - Whether the item should be considered unique
def getFullItemName(baseNoun, baseAdjectives = [],
                    modifierNoun = None, modAdjectives = [],
                    suffixList = [], quantity = 1, isUnique = False):
    phrase = u""

    for adj in modAdjectives:
        phrase += u"%s " % string.capwords(adj)

    if modifierNoun:
        pluralModNoun = makePlural(modifierNoun, quantity).capitalize()
    else:
        pluralModNoun = None

    if pluralModNoun:
        phrase += u"%s " % pluralModNoun

    for adj in baseAdjectives:
        phrase += u"%s " % string.capwords(adj)

    phrase += u"%s" % string.capwords(makePlural(baseNoun, quantity))

    # Special consideration:
    # If the last item in the suffix list starts with an ampersand (&),
    # move the 'and' addition to the next-to-last entry, and append
    # the last item without additional modifiers (after removing the &).
    # This is for dealing with things like 'a scroll of Light titled "xyz"'.
    if suffixList:
        if suffixList[-1][0] == u"&":
            mainList = suffixList[0:-1]
            finalItem = suffixList[-1][1:]
        else:
            mainList = suffixList
            finalItem = None

        if mainList:
            if mainList[0][0].isalpha():
                phrase += u" of"
            phrase += u" %s" % mainList[0]
            for suffix in mainList[1:-1]:
                phrase += u", %s" % suffix
            if len(mainList) > 1:
                phrase += u" and %s" % mainList[-1]

        if finalItem:
            phrase += u" %s" % finalItem

    article = getArticle(phrase, quantity, isUnique)

    phrase = u"%s %s" % (article, phrase)

    return phrase


## Given a block of text, split it at word boundaries such that no sub-block
# is longer than the specified number of characters.
def splitIntoLines(text, maxLen, delimiter = ' '):
    offset = 0 # Index of the last line break.
    lastDelimiter = 0 # Index of the last delimiter we found.
    result = []
    for i, char in enumerate(text):
        if text[i:i + len(delimiter)] == delimiter:
            if (i - offset) >= maxLen:
                # Can't use this space as a breaker, as it shows up too late; 
                # use the last one we found instead.
                result.append(text[offset:lastDelimiter])
                offset = lastDelimiter + len(delimiter)
            lastDelimiter = i
    result.append(text[offset:])
    return result
