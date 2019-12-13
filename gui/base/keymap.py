## Handles conversion from input keystrokes to the enumerated list of
# abstract inputs in the commands package.

# Normally I wouldn't ever use "import *", but the keystroke map below would
# get really tedious if I had to type out "commands.MOVE_1" and the like.
from commands import *

(BEFORE, AFTER) = range(2)

def ctrl(key):
    return ord(key) - ord('a') + 1

class Keymap(object):
    def __init__(self):
        ## Default mapping of standard keystroke IDs to command enums.
        self.keystrokeToCommandMap = {
            ord('1'): MOVE_1,
            ord('2'): MOVE_2,
            ord('3'): MOVE_3,
            ord('4'): MOVE_4,
            ord('5'): REST,
            ord('6'): MOVE_6,
            ord('7'): MOVE_7,
            ord('8'): MOVE_8,
            ord('9'): MOVE_9,
        
            ord('>'): DESCEND,
            ord('<'): ASCEND,
            ord('/'): RECALL_CREATURE,
            ord('!'): LOAD,
        
            ord('C'): DISPLAY_CHARACTER,
            ord('c'): CLOSE,
            ord('d'): DROP_ITEM,
            ord('e'): LIST_EQUIPMENT,
            ord('g'): GET_ITEM,
            ord('I'): INSPECT_ITEM,
            ord('i'): LIST_INVENTORY,
            ord('l'): LOOK,
            ord('L'): SCAN,
            ord('O'): OPEN_ITEM,
            ord('o'): OPEN,
            ord('P'): PUT_ITEM,
            ord('Q'): QUIT,
            ord('S'): SAVE,
            ord('T'): TUNNEL,
            ord('t'): REMOVE_ITEM,
            ord('u'): USE_ITEM,
            ord('v'): THROW_ITEM,
            ord('w'): WIELD_ITEM,
            ctrl('a'): WIZARD_MODE
        }

        self.keystrokeToWizardCommandMap = {
            ord('c'): CREATE_ITEM,
            ord('j'): JUMP_LEVEL,
            ord('o'): TWEAK_ITEM,
            ord('!'): TEST_COMMAND
        }

        self.numericKeyRanges = [
            range(ord('0'), ord('9')+1)
        ]

        self.commandMaps = { 'normal' : self.keystrokeToCommandMap,
                             'wizard' : self.keystrokeToWizardCommandMap}

    ## Generate a Command for the appropriate key input, or None if that input
    # doesn't correspond to anything.
    def convertKeyToCommand(self, keycode, commandSet='normal'):
        commandMap = self.commandMaps[commandSet]
        if keycode in commandMap:
            return commandMap[keycode]
        return None


    ## Convert a Command to the first Key input we find that maps to that Command.
    def convertCommandToKey(self, command, commandSet='normal'):
        commandMap = self.commandMaps[commandSet]
        for key, altCommand in commandMap.iteritems():
            if command == altCommand:
                return key
        print "Couldn't find a key for command",command


    ## Convert a key to its digit
    def convertKeyToNumber(self, keycode):
        for range in self.numericKeyRanges:
            if keycode in range:
                return range.index(keycode)
        return None


    ## return the key from the input that came from the UI
    def getKey(self, input):
        raise RuntimeError("%s didn't implement its getKey function" % self)


    ## return True if the key is a "return" key
    def isReturnKey(self, keycode):
        raise RuntimeError("%s didn't implement its isReturnKey function" % self)


    ## return True if the key is a "delete" key i.e. Del or BS
    def isDeleteKey(self, keycode):
        raise RuntimeError("%s didn't implement its isDeleteKey function" % self)
