import util.id
import util.serializer

# File containing extensions to native classes to provide a bit of
# extra functionality when using existing types.

# SQL-like GROUPBY class that also encapsulates the logic in a Unix-like "sort | uniq"
# Source: http://code.activestate.com/recipes/259173-groupby/
# Example usage:
# >>> letters = 'abracadabra'
# >>> [g for k, g in groupby(letters)]
# [['a', 'a', 'a', 'a', 'a'], ['r', 'r'], ['b', 'b'], ['c'], ['d']]
class GroupGyOrig(dict):
    def __init__(self, seq, key=lambda x:x):
        for value in seq:
            k = key(value)
            self.setdefault(k, []).append(value)
    __iter__ = dict.iteritems


# Redone groupby using a function rather than a class.
# \param seq - The sequence of items to group
# \param key - The function to use to determine what key
#              to use to define each group.
# Returns a dict's iteritems().
def groupBy(seq, key=lambda x:x):
    groups = dict()
    for value in seq:
        k = key(value)
        groups.setdefault(k, []).append(value)
    return groups.iteritems()


# A means of sorting grouped items into lists.
# --
# Passed to the groupby function:
# \param seq - The sequence of items to group
# \param key - The function to use to determine what key
#              to use to define each group.
# --
# \param shouldReverseOrder - Whether to reverse the list after sorting.
# Returns a list of lists sorted by list length.
def groupBySortedByCount(seq, key = lambda x:x, shouldReverseOrder = False):
    myList = [v for k, v in groupBy(seq, key)]
    myList.sort(key = lambda x: len(x))
    if shouldReverseOrder:
        myList.reverse()
    return myList


# A means of sorting grouped items into lists.
# --
# Passed to the groupby function:
# \param seq - The sequence of items to group
# \param key - The function to use to determine what key
#              to use to define each group.
#              Also used as the sorting method for the lists.
# --
# \param reverse - Whether to reverse the list after sorting.
# Returns a list of lists sorted by the grouping key.
def groupBySortedByKey(seq, key = lambda x:x, shouldReverseOrder = False):
    myList = [v for k, v in groupBy(seq, key)]
    myList.sort(key = lambda x: key(x[0]))
    if shouldReverseOrder:
        myList.reverse()
    return myList




## Custom version of a set that has a general membership function.
class Categories(set):
    def __init__(self):
        set.__init__(self)
        self.id = util.id.getId()


    ## Because we've overridden the __init__ method on set(), we need to 
    # implement this method or else deepcopy() breaks. I'm unclear why. 
    def __deepcopy__(self, memo):
        result = Categories()
        result.id = self.id
        result.update(self)
        return result

        
    ## Return True if the specified category is contained in the set.
    # \param category - Category value (of any type) to check for.
    #  If given a set or a list, it will return the intersection.
    #  If given a simple value, it will return True or False.
    #  If given a dict, it will return False, since behavior is
    #  undefined.
    def has(self, category):
        if isinstance(category, set) or isinstance(category, list):
            return self.intersection(category)
        elif isinstance(category, dict):
            return False
        else:
            return category in self


    ## Generate a ready-to-be-serialized dict of our attributes. See the 
    # util.serializer module for more information.
    def getSerializationDict(self):
        return {
            'contents': set(self)
        }


    ## Generate a hash key for this object so it can be inserted into a 
    # dictionary. We just use the object's Python ID (=~ its location in
    # memory), since anything else might be mutable, and mutable object
    # keys are bad.
    def __hash__(self):
        return id(self)


        
## Given a "blank" Categories instance, fill in its data. 
def fillCategoriesData(categories, data, gameMap):
    categories.update(data['contents'])


# Ensure that Categories instances can be [de]serialized.
util.serializer.registerObjectClass(Categories.__name__, 
        lambda **kwargs: Categories(), fillCategoriesData)
