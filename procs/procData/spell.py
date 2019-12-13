import gui
import procs.procLoader
import util.record

import collections
import os



## Spell data describes a single spell that can be cast. Definitions are 
# loaded from spell.txt. They are functionally Proc records with some 
# extra required fields.
class Spell:
    def __init__(self, record):
        ## Keep a copy around in case we need to make a new Spell based on us.
        self.record = record
        ## Name of the Spell.
        self.name = record['name']
        ## Message to display when the Spell is cast.
        self.message = record.get('message', None)
        ## Proc code to invoke for the spell.
        self.proc = procs.procLoader.generateProcFromRecord(record)
        ## Targeting for the spell.
        self.target = record.get('target', 'self')


    ## Passthrough to our Proc.
    def trigger(self, *args, **kwargs):
        self.proc.trigger(*args, **kwargs)



## Maps element names to Element instances.
NAME_TO_SPELL = collections.OrderedDict()

def loadFiles():
    for spell in util.record.loadRecords(
            os.path.join('data', 'spell.txt'), Spell):
        NAME_TO_SPELL[spell.name] = spell


## Generate a Spell instance. The "record" parameter may just be a string,
# in which case we look up one of our pre-loaded spells; otherwise we generate
# a new one (potentially using a pre-loaded spell as a template).
def getSpell(record):
    if isinstance(record, str) or isinstance(record, unicode):
        if record not in NAME_TO_SPELL:
            raise NameError("Tried to retrieve nonexistent spell %s" % record)
        return NAME_TO_SPELL[record]
    # We need to create a new spell.
    if 'name' in record:
        baseSpell = getSpell(record['name'])
        newRecord = dict(baseSpell.record)
        newRecord.update(record)
        return Spell(newRecord)


## Return True if a Spell generated with the given data would require an
# external target.
def getNeedsTarget(spellData):
    spell = getSpell(spellData)
    return spell.target != 'self'


## Cast a spell with a given name. Determine the target to use, and optionally
# teach the player that the caster can cast this spell. 
# \param altTarget Target for the spell, if the spell's targeting is not "self".
# \param shouldUpdateRecall If True and the player can see the caster, then 
#        update the player's monster memory.
def castSpell(spellData, caster, level, gameMap, altTarget = None, 
        shouldUpdateRecall = True):
    # Use try/catch logic here as many spells aren't implemented yet.
    try:
        spell = getSpell(spellData)
        spellName = spell.name
        # Default spells to target "externally" (i.e. not self), unless they 
        # should target the caster instead. 
        target = altTarget
        if spell.target == 'self':
            target = caster
        if spell.message is not None:
            # Display a message indicating the creature's action. 
            message = util.grammar.getConjugatedPhrase(
                    '{creature} ' + spell.message[0],
                    gameMap, caster, spell.message[1], target)
            gui.messenger.message(message)
        # Perform the spell action.
        spell.trigger(source = caster, target = target,
                level = level, gameMap = gameMap)
        if shouldUpdateRecall:
            player = gameMap.getPlayer()
            # Record that the player knows about the spell.
            # This canSee call is technically redundant, but eventually we may
            # allow creatures to can spells when the player cannot see them.
            if player.canSee(caster.pos):
                player.setKnowledge(('creature', caster.name, 'magic',
                        'spells', spellName), True)
                player.setKnowledge(('creature', caster.name, 'magic',
                        'frequency'), True)
    except NameError, e:
        print "Failed to cast spell [%s]: %s" % (spellName, e)

