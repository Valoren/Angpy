## Displays the message history.

from PyQt4.QtCore import *
from PyQt4.QtGui import * 

## Singleton message window.
window = None
class MessageFrame(QTextEdit):
    update = pyqtSignal(unicode)
    
    def __init__(self, parent):
        super(MessageFrame, self).__init__(parent)
        self.setWindowTitle("Message history")
        self.setMinimumWidth(300)
        self.setReadOnly(True)
        self.update.connect(self.handleMessage)

    def handleMessage(self, message):
        self.append(message)


def makeWindow(parent, size):
    global window
    window = MessageFrame(parent)
    #window.text.resize(size[0], size[1])
    window.show()

def message(*args):
    message = " ".join(map(unicode, args))
    # Only modify the UI when in the main thread.
    if (window):
        window.update.emit(message)


