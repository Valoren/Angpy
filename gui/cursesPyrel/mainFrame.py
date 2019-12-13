## Main game window and canvas.
import curses
import time

import artists.ascii
import drawingcontext
import events
import gui.base
import frame


## This encapsulates window for the game map. It also handles
# input processing and command execution.
# \todo separate CommandHandler input processing and command execution
#       from what should be a display management class
class MainFrame(frame.Frame,gui.base.CommandHandler):
    def __init__(self, gameMap):
        frame.Frame.__init__(self, 0, 0, 80, 24)
        gui.base.CommandHandler.__init__(self)
        self.gameMap = gameMap
        ## Artist to use for drawing the game.
        self.artist = artists.ascii.AsciiArtist(self.gameMap)
        ## Amount of time to wait between frames of animation, in seconds.
        self.delayFactor = .01
        ## Whether or not we should force-clear the entire view the next
        # time we draw.
        self.shouldForceClear = True
        events.subscribe('user quit', self.onQuit)

    # draw map to window and flush buffer to screen
    def Refresh(self, shouldRedrawAll=False):
        dc = drawingcontext.DrawingContext(self.window)
        if self.shouldForceClear:
            dc.Clear()
        self.artist.draw(dc, self.width, self.height, self.curPrompt,
                         shouldRedrawAll or self.shouldForceClear)
        self.shouldForceClear = False
        self.windowRefresh()
        curses.doupdate()

    ## Handle drawing an animation sequence.
    def receiveAnimation(self, generator):
        for frame in generator:
            self.artist.setOverlay(frame)
            self.Refresh()
            time.sleep(self.delayFactor)
        self.artist.setOverlay(None)
        self.Refresh(True)

    # \todo The following methods don't have anything to due with the
    # primary display of game map and should be refactored out at some point

    # main loop calls this method on keypress, and passes it to the CommandHandler
    # receiveKeyInput method
    def onKeyDown(self, code):
        self.receiveKeyInput(code)
        self.Refresh()

    # used by CommandHandler to determine if prompt cancel key was pressed
    # maybe this method call something either in keymap.py or prompt.py
    def doesKeyCancelPrompt(self, code):
        return code == 27 #ESC

    ## Handle a request for a new Prompt.
    def receivePrompt(self, prompt):
        super(MainFrame, self).receivePrompt(prompt)
        self.Refresh(True)

    ## Update our game state.
    def update(self):
        self.gameMap.update()
        self.Refresh(True)

    ## Exit cleanly
    def onQuit(self):
        raise KeyboardInterrupt
