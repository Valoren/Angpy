## Main game window and canvas.

import artists.ascii
import events
import keymap
import lookFrame
import messageFrame
import util.threads
import gui.base

import Queue
import threading
import time
import wx


## This is the primary window for the game. It "owns" all secondary windows,
# and when it closes, the program exits.
class MainFrame(wx.Frame):
    def __init__(self, parent, gameMap):
        wx.Frame.__init__(self, parent, title = "Pyrel")
        self.panel = MainPanel(self, gameMap)
        width, height = self.panel.artist.getCharSize()
        # Make us big enough for an 80x24 view, by default.
        self.SetClientSize((width * 80, height * 24))
        self.SetPosition((50, 50))
        messageFrame.makeWindow(self, (50, 50 + self.GetRect()[3]))
        self.lookFrame = lookFrame.makeWindow(self, (50 + self.GetRect()[2], 50))
        self.Bind(wx.EVT_MOUSE_EVENTS, self.onMouse)
        self.Bind(wx.EVT_CLOSE, self.onClose)

    ## Handle mouse events; display whatever is underneath the mouse in our
    # lookFrame.
    def onMouse(self, event):
        x, y = event.GetPosition()
        info = self.panel.artist.getInfoAt(x, y)
        self.lookFrame.setText(info)


    def onClose(self,event):
        if not self.panel.amQuitting:
            self.panel.amQuitting = True
            event.Veto(True)
        self.Destroy()



## This class is our main view into the game. It also performs all input
# handling.
class MainPanel(wx.Panel, gui.base.CommandHandler):
    def __init__(self, parent, gameMap):
        # Without this style, key events won't necessarily be propagated
        # to the Panel, preventing input handling from working properly.
        #super(MainPanel, self).__init__(parent, style = wx.WANTS_CHARS)
        wx.Panel.__init__(self, parent, style = wx.WANTS_CHARS)
        gui.base.CommandHandler.__init__(self)

        ## Lock on processing input, so we don't process input until we're
        # done with executing the previous step.
        self.inputLock = threading.Lock()
        ## Queue of input keys.
        self.keyQueue = Queue.Queue()

        self.gameMap = gameMap
        ## Artist to use for drawing the game.
        self.artist = artists.ascii.WxAsciiArtist(self.gameMap)
        ## Current animation we're rendering.
        self.curAnimation = None
        ## Amount of time to wait between frames of animation, in seconds.
        # .016 = 16ms ~= 60FPS, minus however much time we spend on doing
        # the actual drawing.
        self.delayFactor = .016
        ## Whether or not we should force-clear the entire view the next
        # time we draw.
        self.shouldForceClear = True

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_CHAR, self.onKeyDown)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        events.subscribe('new level generation', self.forceRefresh)
        events.subscribe('new game map', self.onNewGameMap)
        events.subscribe('user quit', self.onQuit)
        self.amQuitting = False
        self.processInputThread()
        self.parent = parent


    ## A new GameMap was created; switch over to using it.
    def onNewGameMap(self, newMap):
        self.gameMap = newMap
        self.forceRefresh()


    def doesKeyCancelPrompt(self, code):
        return code == wx.WXK_ESCAPE


    ## Process input. We simply append the input to our queue.
    def onKeyDown(self, event):
        self.keyQueue.put(event.GetKeyCode())


    ## This function runs in a new thread and watches for input, then processes
    # it. We have this system so we can buffer incoming key events while
    # other things are happening (e.g. redrawing the screen), without every
    # input creating a new thread that tries to block on self.inputLock. All
    # of the blocking happens here instead.
    @util.threads.callInNewThread
    def processInputThread(self):
        while not self.amQuitting:
            if not self.keyQueue.empty():
                with self.inputLock:
                    keyCode = self.keyQueue.get()
                    self.receiveKeyInput(keyCode)
                    # Force a redraw, since input may have changed what is
                    # displayed.
                    self.Refresh()
            time.sleep(.01)
        self.parent.Close()


    def onQuit(self):
        self.amQuitting = True


    ## Handle a request for a new Prompt.
    def receivePrompt(self, prompt):
        super(MainPanel, self).receivePrompt(prompt)
        # Draw the new prompt. We use wx.CallAfter because this function
        # is not necessarily called in the main thread.
        wx.CallAfter(self.Refresh)


    ## Handle drawing an animation. Must be called in a new thread so that
    # updates to the display are shown.
    @util.threads.callInNewThread
    def receiveAnimation(self, generator):
        # No input while we process animations.
        with self.inputLock:
            for frame in generator:
                self.artist.setOverlay(frame)
                events.executeAndWaitFor('draw complete',
                        wx.CallAfter, self.Refresh)
                time.sleep(self.delayFactor)
            self.artist.setOverlay(None)
            wx.CallAfter(self.Refresh)


    ## Update our game state.
    def update(self):
        self.Refresh()
        self.gameMap.update()


    ## Hand painting jobs off to our artist.
    def onPaint(self, event = None):
        dc = wx.AutoBufferedPaintDC(self)
        if self.shouldForceClear:
            dc.SetBackground(wx.Brush((0, 0, 0), wx.SOLID))
            dc.Clear()
        pixelWidth, pixelHeight = self.GetClientSizeTuple()
        self.artist.draw(dc, pixelWidth, pixelHeight, self.curPrompt,
                self.shouldForceClear)
        self.shouldForceClear = False


    ## Something requires a full screen refresh.
    def forceRefresh(self, *args):
        self.shouldForceClear = True
        self.Refresh()
