import gui.colors
import procs.procLoader
import util.record

import collections
import os


## Element data describes the effects that different damage types can have. It
# is loaded from element.txt.
class Element:
    def __init__(self, record):
        self.name = record['name']
        ## Abbreviated name for compressed display.
        self.shortName = record.get('shortName', self.name)
        ## Max damage this element can ordinarily deal.
        self.damageCap = record.get('damageCap', None)
        ## Display info.
        self.display = record['display']
        ## Textual description of the element.
        self.info = record['info']
        ## Verb for damaging things.
        self.verb = record.get('verb', 'damages')
        procRecords = record.get('procs', [])
        ## List of procs that trigger when we damage something.
        self.procs = []
        for procRecord in procRecords:
            self.procs.append(procs.procLoader.generateProcFromRecord(procRecord))


    ## Return the damage multiplier for this element applied to the given
    # target, taking resistance/immunity into account.
    def getDamageFactor(self, target):
        if target.getStat('immune to %s' % self.name):
            return 0
        if target.getStat('resist %s' % self.name):
            return 1 / 3.0
        if target.getStat('vulnerable to %s' % self.name):
            return 2
        return 1


    ## Given a target Thing and a damage total, apply our Procs to it. Return
    # a modified damage amount. 
    def applyProcs(self, target, damage, gameMap):
        for proc in self.procs:
            result = proc.trigger(element = self, 
                    target = target, damage = damage, gameMap = gameMap)
            if result is not None:
                # Assume it's a new damage value.
                damage = result
        return damage



## Maps element names to Element instances.
NAME_TO_ELEMENT = collections.OrderedDict()

def loadFiles():
    for element in util.record.loadRecords(
            os.path.join('data', 'element.txt'), Element):
        NAME_TO_ELEMENT[element.name] = element


## Retrieve the Element instance with the corresponding name.
def getElement(name):
    if name not in NAME_TO_ELEMENT:
        raise RuntimeError("Attempted to access invalid element name %s" % name)
    return NAME_TO_ELEMENT[name]


## Return all elements.
def getAllElements():
    return NAME_TO_ELEMENT.values()
