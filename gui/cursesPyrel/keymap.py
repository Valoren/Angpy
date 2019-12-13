## Handles conversion from input keystrokes to the enumerated list of
# abstract inputs in the commands package.

# Normally I wouldn't ever use "import *", but the keystroke map below would
# get really tedious if I had to type out "commands.MOVE_1" and the like.
from commands import *

import curses
import gui.base.keymap

class CursesKeymap(gui.base.keymap.Keymap):
    def __init__(self):
        super(CursesKeymap, self).__init__()
        ## curses keycode values for keypad movement
        self.keystrokeToCommandMap.update({
            curses.KEY_C1: MOVE_1,
            curses.KEY_DOWN: MOVE_2,
            curses.KEY_C3: MOVE_3,
            curses.KEY_LEFT: MOVE_4,
            curses.KEY_B2: REST,
            curses.KEY_RIGHT: MOVE_6,
            curses.KEY_A1: MOVE_7,
            curses.KEY_UP: MOVE_8,
            curses.KEY_A3: MOVE_9,
            })

        self.numericKeyRanges.append([
            curses.KEY_IC, curses.KEY_C1, curses.KEY_DOWN, curses.KEY_C3,
            curses.KEY_LEFT, curses.KEY_B2, curses.KEY_RIGHT,
            curses.KEY_A1, curses.KEY_UP, curses.KEY_A3])


    ## return the keycode from the input
    # For curses, this is a direct mapping
    def getKey(self, input):
        return input


    def isReturnKey(self, input):
        return input in [curses.KEY_ENTER, 10, 13]


    ## return True if the key is a "delete" key, i.e. Del or BS
    # Also return the direction in which we should delete
    def isDeleteKey(self, input):
        isDelete = input in [curses.KEY_BACKSPACE, curses.KEY_UNDO]
        direction = gui.base.keymap.BEFORE
        if input == curses.KEY_UNDO:
            direction = gui.base.keymap.AFTER
        return (isDelete, direction)
