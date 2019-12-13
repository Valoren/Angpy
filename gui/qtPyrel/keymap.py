## Handles conversion from input keystrokes to the enumerated list of
# abstract inputs in the commands package.

# Normally I wouldn't ever use "import *", but the keystroke map below would
# get really tedious if I had to type out "commands.MOVE_1" and the like.
from commands import *
import gui.base.keymap

from PyQt4.QtCore import Qt

class QtKeymap(gui.base.keymap.Keymap):
    def __init__(self):
        super(QtKeymap, self).__init__()

        ## Default mapping of Qt keystroke IDs to command enums.
        self.keystrokeToCommandMap.update({
            Qt.Key_End: MOVE_1,
            Qt.Key_Down: MOVE_2,
            Qt.Key_PageDown: MOVE_3,
            Qt.Key_Left: MOVE_4,
            Qt.Key_Clear: REST,
            Qt.Key_Right: MOVE_6,
            Qt.Key_Home: MOVE_7,
            Qt.Key_Up: MOVE_8,
            Qt.Key_PageUp: MOVE_9,
            })

        self.numericKeyRanges.append([
            Qt.Key_Insert, Qt.Key_End, Qt.Key_Down, Qt.Key_PageDown,
            Qt.Key_Left, Qt.Key_Clear, Qt.Key_Right, Qt.Key_Home,
            Qt.Key_Up, Qt.Key_PageUp])


    ## Generate a Command for the appropriate key input, or None if that input
    # doesn't correspond to anything.
    def convertKeyToCommand(self, keycode_mods, commandSet = 'normal'):
        commandMap = self.commandMaps[commandSet]
        keycode = self.getKey(keycode_mods)
        if keycode in commandMap:
            return commandMap[keycode]
        else: # Temporary for debugging implementation of more commands
            print "Unknown key, code", hex(keycode), "modifiers", hex(int(keycode_mods[1]))
        return None


    ## return the key from the input
    # For Qt, we have to take account of the modifiers
    def getKey(self, input):
        keycode, mods = input
        if keycode in range(ord('A'), ord('Z')+1):
            if not mods & Qt.ShiftModifier:
                keycode += ord('a') - ord('A')
            if mods & Qt.ControlModifier:
                keycode -= ord('a') - 1
        return keycode


    ## return True if the key is a "return" key
    def isReturnKey(self, input):
        return input[0] in [Qt.Key_Return, Qt.Key_Enter]


    ## return True if the key is a "delete" key, i.e. Del or BS
    # Also return the direction in which we should delete
    def isDeleteKey(self, input):
        isDelete = input[0] in [Qt.Key_Backspace, Qt.Key_Delete]
        direction = gui.base.keymap.BEFORE
        if input[0] == Qt.Key_Delete:
            direction = gui.base.keymap.AFTER
        return (isDelete, direction)
