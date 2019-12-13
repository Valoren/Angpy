import gui
import procs.procLoader
import procs.procUtil
import util.grammar
import util.record

import collections
import os


## Status data describes temporary status effects. Data is loaded from 
# data/status.txt.
class Status:
    def __init__(self, record):
        self.name = record['name']
        ## Stat to modify when we are applied.
        self.statName = record.get('statName', self.name)
        ## Additive modifier to the stat that we apply, unless otherwise
        # overriden.
        self.modAmount = record.get('modAmount', 1)
        ## Multiplicative modifier to the stat we apply (0 = nothing, 
        # 1 = double, -1 = cancel, etc.), unless otherwise overridden.
        self.modFactor = record.get('modFactor', 0)
        ## Mapping of trigger conditions to Procs to invoke when those 
        # conditions are met. 
        self.triggerToProc = {}
        for trigger, proc in record.get('procs', {}).iteritems():
            self.triggerToProc[trigger] = procs.procLoader.generateProcFromRecord(proc)
        ## Phrase to use to describe applying the status to something.
        self.initialDescription = record['initialDescription']
        ## Phrase to use when we apply the status but the thing receiving it
        # already has that status.
        self.stackDescription = record.get('stackDescription', 
                self.initialDescription)


    ## Generate the string describing applying us to the target.
    def getApplicationString(self, target, gameMap, isRepeatApplication = False):
        text = [self.initialDescription, self.stackDescription][int(isRepeatApplication)]
        return util.grammar.getConjugatedPhrase(
                "{creature} %s" % text[0], 
                gameMap, target, text[1])


    ## Apply ourselves to the given target. Add a timered stat modifier, and
    # attach our Procs to the target. 
    def apply(self, target, gameMap, duration, modAmount = None, 
            modFactor = None, stackMode = 'reset'):
        if modAmount is None:
            modAmount = self.modAmount
        if modFactor is None:
            modFactor = self.modFactor
        statStatus = procs.procUtil.addTimeredStat(target, gameMap, 
                self.statName, duration, modAmount, modFactor, stackMode)
        if statStatus.didStart:
            # Attach our procs to the target.
            # \todo Assuming that the target is a Creature with a procs map.
            for trigger, proc in self.triggerToProc.iteritems():
                target.addProc(trigger, proc)
            statStatus.timer.doAlso(self.remove, (target,))
            gui.messenger.message(self.getApplicationString(target, gameMap, False))
        if statStatus.didStack:
            gui.messenger.message(self.getApplicationString(target, gameMap, True))


    ## Remove our procs from the target.
    def remove(self, target):
        for trigger, proc in self.triggerToProc.iteritems():
            target.removeProc(trigger, proc)



## Maps status names to Status instances.
NAME_TO_STATUS = collections.OrderedDict()

def loadFiles():
    for status in util.record.loadRecords(
            os.path.join('data', 'status.txt'), Status):
        NAME_TO_STATUS[status.name] = status


## Retrieve the Status instance with the corresponding name.
def getStatus(name):
    if name not in NAME_TO_STATUS:
        raise NameError("Attempted to access invalid status name %s" % name)
    return NAME_TO_STATUS[name]


## Return all statuses.
def getAllStatuses():
    return NAME_TO_STATUS.values()


## Apply a status to the target.
def applyStatus(name, target, gameMap, duration, modAmount = None, 
            modFactor = None, stackMode = 'reset'):
    if name not in NAME_TO_STATUS:
        raise NameError("Attempted to access invalid status name %s" % name)
    NAME_TO_STATUS[name].apply(target, gameMap, duration, modAmount, modFactor,
            stackMode)
