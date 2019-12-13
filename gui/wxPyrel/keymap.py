## Handles conversion from input keystrokes to the enumerated list of
# abstract inputs in the commands package.

# Normally I wouldn't ever use "import *", but the keystroke map below would
# get really tedious if I had to type out "commands.MOVE_1" and the like.
from commands import *
import gui.base.keymap
import wx

class WxKeymap(gui.base.keymap.Keymap):
    def __init__(self):
        super(WxKeymap, self).__init__()
        self.keystrokeToCommandMap.update({
            wx.WXK_NUMPAD1: MOVE_1,
            wx.WXK_NUMPAD2: MOVE_2,
            wx.WXK_NUMPAD3: MOVE_3,
            wx.WXK_NUMPAD4: MOVE_4,
            wx.WXK_NUMPAD5: REST,
            wx.WXK_NUMPAD6: MOVE_6,
            wx.WXK_NUMPAD7: MOVE_7,
            wx.WXK_NUMPAD8: MOVE_8,
            wx.WXK_NUMPAD9: MOVE_9,
            wx.WXK_UP: MOVE_8,
            wx.WXK_DOWN: MOVE_2,
            wx.WXK_LEFT: MOVE_4,
            wx.WXK_RIGHT: MOVE_6
            })

        self.numericKeyRanges.append([
            wx.WXK_NUMPAD0, wx.WXK_NUMPAD1, wx.WXK_NUMPAD2, wx.WXK_NUMPAD3,
            wx.WXK_NUMPAD4, wx.WXK_NUMPAD5, wx.WXK_NUMPAD6, wx.WXK_NUMPAD7,
            wx.WXK_NUMPAD8, wx.WXK_NUMPAD9])


    ## Return the keypress from the input
    # In the case of WXWidgets, it is a direct mapping
    def getKey(self, input):
        return input


    def isReturnKey(self, input):
        return input in [wx.WXK_NUMPAD_ENTER, wx.WXK_RETURN]


    def isDeleteKey(self, input):
        isDelete = input in [wx.WXK_DELETE, wx.WXK_BACK]
        direction = [-1, 1][input == wx.WXK_DELETE]
        return (isDelete, direction)

