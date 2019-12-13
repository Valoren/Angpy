## This module provides overrides for prompts in gui/base/prompt.py
## additionally, it implements TargetPrompt class, as well as the
## receivePrompt method to pass prompts to the appropriate ui handler
import mainApp
import gui.base.prompt

import wx

## This Prompt lets the user select a tile or creature on the map, and stick
# it into the TARGETED container in the game map.
class TargetPrompt(gui.base.prompt.TargetPrompt):
    def doesKeySelectTarget(self, input):
        return input in [wx.WXK_NUMPAD_ENTER, wx.WXK_RETURN]


    ## Draw a box around our current tile, and print a description of its
    # contents.
    def draw(self, dc, artist, gameMap):
        super(TargetPrompt, self).draw(dc, artist, gameMap)

        x, y, dx, dy = artist.getTileBox(self.targetTile)
        points = [(x, y), (x + dx, y), (x + dx, y + dy), (x, y + dy), (x, y)]
        curPen = dc.GetPen()
        dc.SetPen(wx.Pen(wx.YELLOW, 1))
        dc.DrawLines(points)
        dc.SetPen(curPen)


