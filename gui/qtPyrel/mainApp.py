import argparse
import random
import time
from PyQt4 import QtGui

import mapgen.gameMap
import mainFrame

## Singleton instance of the PyrelQTApp.
app = None

## This creates the necessary windows to run the program.
class PyrelQTApp(QtGui.QApplication):
    def __init__(self, gameMap, *args):
        super(PyrelQTApp, self).__init__(*args)
        self.frame = mainFrame.MainFrame(None, gameMap)
        self.frame.show()
        self.frame.raise_()



def makeApp(*args):
    global app
    app = PyrelQTApp(*args)
    app.exec_()


## Access the Panel that does all of the heavy lifting for UI work.
def getPanel():
    return app.frame.panel
