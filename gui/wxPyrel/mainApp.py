import argparse
import random
import time
import wx

import mapgen.gameMap
import mainFrame

## Singleton instance of the PyrelWXApp.
app = None

## This creates the necessary windows to run the program.
class PyrelWXApp(wx.App):
    def OnInit(self):
        return True



def makeApp(gameMap):
    global app
    app = PyrelWXApp(redirect = False)
    app.frame = mainFrame.MainFrame(None, gameMap)
    app.frame.Show()
    app.MainLoop()


## Access the Panel that does all of the heavy lifting for UI work.
def getPanel():
    return app.frame.panel
