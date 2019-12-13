import curses
import sys
import locale

import mapgen.gameMap
import mainFrame
import messageFrame

## Singleton instance of the PyrelWXApp.
app = None

locale.setlocale(locale.LC_ALL,"")

## This class manages UI initialization using the curses API, as well as the main
# application loop.
class PyrelCursesApp(object):
    def __init__(self, gameMap):
        self.gameMap = gameMap

    def MainLoop(self):
        ## initializes curses, stops echo of key inputs, and intializes curses
        ## support for colors for the terminal emulator, control is then passed
        ## to the helper function _mainloop
        curses.wrapper(self._mainloop)
        if self.exit_message:
            print 'Pyrel exiting...', self.exit_message

    def _mainloop(self, stdscr):
        ## Check terminal capabilities for game support
        maxy, maxx = stdscr.getmaxyx()
        if maxy < 35 or maxx < 80:
            self.exit_message = 'requires at least 80x35 window'
            return

        ## Try to hide cursor
        try:
            cursor = curses.curs_set(0)
        except:
            pass

        ## Initialize UI Frames
        self.mainFrame = mainFrame.MainFrame(self.gameMap)
        self.messageFrame = messageFrame.MessageFrame()
        curses.ungetch(' ') #KLUDGE to run main loop once
        curses.raw()
        ## Main Application Loop
        while True:
            try:
                ch = stdscr.getch()
                self.mainFrame.onKeyDown(ch)
                curses.doupdate()
            except KeyboardInterrupt:
                self.exit_message = 'as requested'
                break

        ## Return cursor to original state before exiting
        try:
            curses.curs_set(cursor)
        except:
            pass

## mainApp module interface from gui
## access app singleton instance
def getApp():
    return app

## initialize and run application UI
def Run(gameMap):
    global app
    app = PyrelCursesApp(gameMap)
    app.MainLoop()
