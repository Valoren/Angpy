# coding=utf-8

from nose.exc import SkipTest
from nose.tools import assert_equals
from nose.tools import raises
import util.grammar

## Class for testing the grammar.makePlural() function
class plural_test():
    # known value tuples: decorated form, singular, plural
    # \todo: unicode, and words with unicode characters
    knownValues = ( (u"horse~",          "horse",    "horses"),
                    (u"house~",          "house",    "houses"),
                    (u"sheep",           "sheep",    "sheep"),
                    (u"mouse:mice",      "mouse",    "mice"),
                    (u"knife:knives",    "knife",    "knives"),
                    (u"staff:staves",    "staff",    "staves"),
                    (u"vortex:vortices", "vortex",   "vortices"),
                    (u"vortex:vortices", "vortex",   "vortices"),
                    (u"man:men",         "man",      "men"),
                    (u"woman:women",     "woman",    "women"),
                    (u"witch:witches",   "witch",    "witches"),
                    (u"lady:ladies",     "lady",     "ladies"),
                    (u"dwarf:dwarves",   "dwarf",    "dwarves"),
                    (u"shield~",         "shield",   "shields"),
                    (u"zweihander~",     "zweihander", "zweihanders"),
                    (u"set~ of leather gloves", "set of leather gloves", "sets of leather gloves"),
                    (u"pair~ of hard leather boots", "pair of hard leather boots", "pairs of hard leather boots") )


    # General function to check the results of a makePlural call
    def check_result(self, form, quantity, expectation):
        result = util.grammar.makePlural(form, quantity)
        assert_equals(result, expectation)

    # Generator function for testing each known value as a singular
    def test_singular(self):
        '''Test normal singular form'''
        for form, singular, plural in self.knownValues:
            yield self.check_result, form, 1, singular

    # Generator function for testing each known value as a plural
    def test_plural_2(self):
        '''Test normal plural form (2 items)'''
        for form, singular, plural in self.knownValues:
            yield self.check_result, form, 2, plural

    # Generator function for testing each known value as a plural
    def test_plural_0(self):
        '''Test plural form for 0 items'''
        for form, singular, plural in self.knownValues:
            yield self.check_result, form, 0, plural


    # Remainder are checks for specific invalid data.

    @raises(Exception)
    def test_negative_quantity(self):
        '''Test invalid data: quantity is -1'''
        result = util.grammar.makePlural("horse~", -1)

    @raises(Exception)
    def test_no_quantity(self):
        '''Test invalid data: quantity is None'''
        result = util.grammar.makePlural("horse~", None)

    @raises(Exception)
    def test_invalid_number(self):
        '''Test invalid data: quantity is not a number'''
        result = util.grammar.makePlural("horse~", [2])

    @raises(Exception)
    def test_no_base_name(self):
        '''Test invalid data: base name is None'''
        result = util.grammar.makePlural(None, 2)

    @raises(Exception)
    def test_invalid_string(self):
        '''Test invalid data: base name is not a string'''
        result = util.grammar.makePlural(["horse~"], 2)


## Class for testing the grammar.getArticle() function.
class article_test():
    # known value tuples: phrase, article
    knownValues = ((u"ring", u"a"),
                   (u"armband", u"an"),
                   (u"amber ring", u"an"),
                   (u"ungulant armor", u"an"),
                   (u"yellow bracer", u"a"),
                   (u"set of leather gloves", u"a"),
                   (u"ring mail", u"a"))

    knownBadValues = ((u"universal headband", u"a"),
                      (u"\x00fcber", u"an") # -- how to handle unicode characters?
                      )

    # General function to check the results of a makePlural call
    def check_result(self, phrase, quantity, defArt, expectation):
        result = util.grammar.getArticle(phrase, quantity, defArt)
        assert_equals(result, expectation, "%s: %s != %s" % (phrase, result, expectation))

    # Generator function for testing singular indefinite form.
    def test_singular_indefinite(self):
        '''Test singular indefinite form'''
        for phrase, article in self.knownValues:
            yield self.check_result, phrase, 1, False, article

    # Generator function for testing singular definite form.
    # Result should always be "the"
    def test_singular_definite(self):
        '''Test singular definite form'''
        for phrase, article in self.knownValues:
            yield self.check_result, phrase, 1, True, u"the"

    # Generator function for testing plural indefinite form.
    def test_plural_indefinite(self):
        '''Test plural indefinite form'''
        for num in range(2,4):
            for phrase, article in self.knownValues:
                yield self.check_result, phrase, num, False, unicode(num)

    # Generator function for testing plural definite form.
    def test_plural_definite(self):
        '''Test plural definite form'''
        for num in range(2,4):
            for phrase, article in self.knownValues:
                yield self.check_result, phrase, num, True, unicode(num)

    # Generator function for testing zero indefinite form.
    def test_zero_indefinite(self):
        '''Test zero indefinite form'''
        for phrase, article in self.knownValues:
            yield self.check_result, phrase, 0, False, u""

    # Generator function for testing zero definite form.
    def test_zero_definite(self):
        '''Test zero definite form'''
        for phrase, article in self.knownValues:
            yield self.check_result, phrase, 0, True, u""


    # General method to skip a function test.
    def skip(self, phrase, quantity, defArt, expectation):
        raise SkipTest("Skipping '%s'" % phrase)

    # Generator function for testing known fail cases.
    def test_bad_values(self):
        '''Known failing test cases.  Skip them.'''
        for phrase, article in self.knownBadValues:
            yield self.skip, phrase, 1, False, article

    # Remainder are checks for specific invalid data.

    @raises(Exception)
    def test_negative_quantity(self):
        '''Test invalid data: quantity is -1'''
        result = util.grammar.getArticle(u"ring", -1, False)

    @raises(Exception)
    def test_no_quantity(self):
        '''Test invalid data: quantity is None'''
        result = util.grammar.getArticle(u"ring", None, False)

    @raises(Exception)
    def test_invalid_number(self):
        '''Test invalid data: quantity is not a number'''
        result = util.grammar.getArticle(u"ring", [2], False)

    @raises(Exception)
    def test_no_base_name(self):
        '''Test invalid data: phrase is None'''
        result = util.grammar.getArticle(None, 1, False)

    @raises(Exception)
    def test_invalid_string(self):
        '''Test invalid data: base name is not a string'''
        result = util.grammar.getArticle(["ring"], 1, False)


## Class for testing the grammar.getFullItemName() function.
class itemName_test():
    # knownValues: list of params for getFullItemName, and the expected result
    # param order: baseNoun, baseAdjectives, modifierNoun, modAdjectives, suffixList, quantity, unique
    knownValues = ((["amulet~", [], None, [], [], 1, False], "an Amulet"),
                   (["ring~", ["coral"], None, [], [], 1, False], "a Coral Ring"),
                   (["rod~", [], None, [], ["Recall"], 1, False], "a Rod of Recall"),
                   (["bolt~", [], None, [], ["Shocking"], 18, False], "18 Bolts of Shocking"),
                   (["amulet~", ["steel"], None, [], ["Resist Acid", "Hold Life"], 1, False], "a Steel Amulet of Resist Acid and Hold Life"),
                   (["gloves", ["leather"], "set~ of", [], ["'Icy Princess'"], 1, True], "the Set of Leather Gloves 'Icy Princess'")
                   )

    # General function to check the results of a call to getFullItemName
    def check_result(self, params, expectation):
        result = util.grammar.getFullItemName(params[0], params[1], params[2], params[3], params[4], params[5], params[6])
        assert_equals(result, expectation, "%s: %s != %s" % (params, result, expectation))

    # Generator function to run through the list of known values.
    def test_item_names(self):
        '''Test item name construction'''
        for params, output in self.knownValues:
            yield self.check_result, params, output

