## Artist that imitates an ASCII-mode drawing style.

from PyQt4.QtCore import Qt
from PyQt4.QtGui import * 

import gui.base.artists.ascii
import container
import gui.colors
import gui.flavors
import util.threads

## Ordered list of what we want to draw -- the first thing to match gets 
# displayed.
DRAW_ORDER = [container.UPDATERS, container.ITEMS, container.TERRAIN]



class QtAsciiArtist(gui.base.artists.ascii.AsciiArtist):
    def __init__(self, gameMap):
        ## Bitmap for drawing the map. It'll be recreated as needed, typically
        # when the window is resized.
        self.mapBitmap = None
        ## Bitmap for drawing the player; ditto.
        self.playerBitmap = None
        ## Bitmap for drawing temporary overlays.
        self.overlayBitmap = None
        ## List of [(position, symbol, color)] tuples to draw on top of 
        # everything else.
        self.overlayData = None
        ## Point size to use for drawing.
        self.pointSize = 12
        ## Font for drawing characters
        self.font = QFont("Courier", self.pointSize)
        self.font.setStyleHint(QFont.Monospace)
        self.fontMetrics = QFontMetrics(self.font)
        
        gui.base.artists.ascii.AsciiArtist.__init__(self, gameMap)


    # Get the size of all ASCII characters, so we know how big a single
    # tile in the view is.
    def getBiggestCharacterDimensions(self):
        fontMetrics = QFontMetrics(self.font)
        biggestChar = [0, 0]
        # Unicode characters can be 
        # unusually large; we'll assume we don't use those. 
        # \todo Find a better way to enumerate all draw-able (i.e. non-control-
        # character) ASCII chars.
        # \todo There's probably a better way to accomplish this in general,
        # actually -- do we really need to iterate over all the characters?
        # What about accented capital characters?
        for char in xrange(32, 127):
            char = unichr(char)
            extent = fontMetrics.boundingRect(char)
            width = extent.width() - 1
            height = extent.height() - 1
            if width > biggestChar[0]:
                biggestChar[0] = width
            if height > biggestChar[1]:
                biggestChar[1] = height
        return biggestChar
   

    ## Draw the game view ASCII-style (i.e. one character per tile).
    # We do this by generating an array of characters to display.
    @util.threads.classLocked
    def draw(self,qp, pixelWidth, pixelHeight, curPrompt, shouldRedrawAll): 
        # Have enough rows/columns to completely fill the window.
        numColumns = int(float(pixelWidth) / self.charWidth) + 1
        numRows = int(float(pixelHeight) / self.charHeight) + 1
        if (self.mapBitmap is None or numColumns != self.numColumns or 
                numRows != self.numRows):
            # Size of the display has changed, so a) we have to redraw 
            # everything, and b) we need new bitmaps to draw to.
            shouldRedrawAll = True
            # Note we use a multiple of the char width/height here instead 
            # of the actual size of the window. 
            size = (numColumns * self.charWidth, numRows * self.charHeight)
            self.mapBitmap = QPixmap(*size)
            self.playerBitmap = QPixmap(*size)
            self.numColumns = numColumns
            self.numRows = numRows

        mapPainter = QPainter(self.mapBitmap)
        blackBrush = QBrush(Qt.black)
        mapPainter.setBackground(blackBrush)
        mapPainter.setBrush(blackBrush)
        mapPainter.setFont(self.font)
        self.drawMap(mapPainter, shouldRedrawAll)
        qp.setBackground(blackBrush)
        qp.drawPixmap(0, 0, self.mapBitmap)

        playerPainter = QPainter(self.playerBitmap)
        playerPainter.setBackground(blackBrush)
        playerPainter.eraseRect(0, 0, self.numPlayerColumns * self.charWidth, 
                self.numRows * self.charHeight)
        playerPainter.setBrush(blackBrush)
        playerPainter.setFont(self.font)
        self.drawPlayerStatus(playerPainter)
        qp.setBackground(blackBrush)
        qp.drawPixmap(0, 0, self.playerBitmap)
        
        if curPrompt:
            curPrompt.draw(qp, self, self.gameMap)
        self.drawOverlay(qp)


    ## Draw overlay data if there is any
    def drawOverlay(self, qp):
        if self.overlayData is None:
            return    

        for tile, symbol, color in self.overlayData:
            x, y = tile
            self.drawChar(qp, symbol, color, x + self.numPlayerColumns, y)


    ## Draw a character of the specified color at the specified position.
    def drawChar(self, qp, char, color, x, y, info = None):
        if type(color) in [str, unicode]:
            # Color is a color-string; convert it.
            color = gui.colors.getColor(color)
        qp.setPen(QColor(*color))
        x = x * self.charWidth
        y = y * self.charHeight
        qp.eraseRect(x, y, self.charWidth, self.charHeight)
        # y position needs to be the baseline of the font, so add ascent
        y += self.fontMetrics.ascent()
        qp.drawText(x, y, char)


    ## Draw a rectangle of the specified color over the given cell range.
    # \todo For now, just erasing the rect instead.
    def drawRectangle(self, qp, color, x, y, width, height):
        if width == -1:
            width = self.numColumns
        if height == -1:
            height = self.numRows
        qp.eraseRect(x * self.charWidth, y * self.charHeight, 
                width * self.charWidth, height * self.charHeight)



    ## Override this function so that we aren't limited to grid-locked
    # strings.
    def writeString(self, qp, colorName, xPos, yPos, string, info = None):
        colorTuple = gui.colors.getColor(colorName)
        color = QColor(*colorTuple)
        qp.setPen(color)
        x = xPos * self.charWidth
        y = yPos * self.charHeight
        qp.eraseRect(x, y, self.charWidth * len(string), self.charHeight)
        qp.drawText(x, y + self.fontMetrics.ascent(), string)


    ## Copy the map bitmap over by the specified offset.
    def copyMapTo(self, qp, xOffset, yOffset):
        copy = self.mapBitmap.copy()
        qp.drawPixmap(xOffset * self.charWidth, yOffset * self.charHeight, copy)

