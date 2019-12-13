## Main game window and canvas.

import artists.ascii
import events
import messageFrame
import util.threads
import gui.base

import threading
import time
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui


## This is the primary window for the game. It "owns" all secondary windows,
# and when it closes, the program exits.
class MainFrame(QtGui.QMainWindow):
    def __init__(self, parent, gameMap):
        super(MainFrame, self).__init__()
        self.setWindowTitle("Pyrel")
        self.setWindowIcon(QtGui.QIcon('../att-128.png'))
        self.panel = MainPanel(self, gameMap)
        width, height = self.panel.artist.getCharSize()
        # Make us big enough for an 80x24 view, by default.
        self.panel.setFixedSize(width * 80, height * 24)

        self.setCentralWidget(self.panel)
        messageFrame.makeWindow(self, (width * 40, height * 24))
        messageDock = QtGui.QDockWidget(parent=self)
        messageDock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        messageDock.setWidget(messageFrame.window)
        messageDock.setWindowTitle(messageDock.widget().windowTitle())
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, messageDock)
        self.panel.setFocusPolicy(QtCore.Qt.StrongFocus)



## This class is our main view into the game. It also performs all input
# handling.
class MainPanel(QtGui.QWidget, gui.base.CommandHandler):
    refresh = QtCore.pyqtSignal()

    def __init__(self, parent, gameMap):
        # Without this style, key events won't necessarily be propagated
        # to the Panel, preventing input handling from working properly.
        super(MainPanel, self).__init__(parent) #, style = qt.WANTS_CHARS)
        gui.base.CommandHandler.__init__(self)
        self.gameMap = gameMap
        ## Artist to use for drawing the game.
        self.artist = artists.ascii.QtAsciiArtist(self.gameMap)
        ## Lock on processing input.
        self.inputLock = threading.Lock()
        ## Current animation we're rendering.
        self.curAnimation = None
        ## Amount of time to wait between frames of animation, in seconds.
        self.delayFactor = .016
        ## Whether or not we should force-clear the entire view the next
        # time we draw.
        self.shouldForceClear = True

        self.setBackgroundRole(QtGui.QPalette.NoRole)
        self.refresh.connect(self.doRefresh)
        events.subscribe('new level generation', self.onLevelGeneration)
        events.subscribe('refresh screen', self.doRefresh)
        events.subscribe('user quit', self.onQuit)


    def doRefresh(self):
        self.repaint()


    def doesKeyCancelPrompt(self, keyEvent):
        return keyEvent[0] == QtCore.Qt.Key_Escape


    def keyPressEvent(self, event):
        keyEvent = (event.key(), event.modifiers())
        with self.inputLock:
            self.receiveKeyInput(keyEvent)
        self.doRefresh()


    ## Handle a request for a new Prompt.
    def receivePrompt(self, prompt):
        super(MainPanel, self).receivePrompt(prompt)
        # Draw the new prompt. We use a signal because this function
        # is not necessarily called in the main thread.
        self.refresh.emit()


    ## Handle drawing an animation.
    @util.threads.callInNewThread
    def receiveAnimation(self, generator):
        # No input while we process animations.
        with self.inputLock:
            for frame in generator:
                self.artist.setOverlay(frame)
                self.refresh.emit()
                time.sleep(self.delayFactor)
            self.artist.setOverlay(None)
            self.refresh.emit()


    ## Update our game state.
    def update(self):
        self.doRefresh()
        self.gameMap.update()


    ## Hand painting jobs off to our artist.
    def paintEvent(self, event = None):
        qp = QtGui.QPainter()
        qp.begin(self)
        if self.shouldForceClear:
            qp.setBackground(QtGui.QBrush(QtCore.Qt.black))
            qp.eraseRect(qp.window())
        client = qp.window()
        self.artist.draw(qp, client.width(), client.height(), self.curPrompt,
                self.shouldForceClear)
        self.shouldForceClear = False
        qp.end()


    ## A new level has been generated; we have to redraw every tile.
    def onLevelGeneration(self, *args):
        self.shouldForceClear = True
        

    def onQuit(self):
        QtCore.QCoreApplication.instance().quit()
