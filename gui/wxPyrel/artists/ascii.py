## Artist that imitates an ASCII-mode drawing style.

import events
import container
import gui.base.artists.ascii
import gui.colors
import gui.flavors
import util.threads

import wx

## Ordered list of what we want to draw -- the first thing to match gets 
# displayed.
DRAW_ORDER = [container.UPDATERS, container.ITEMS, container.TERRAIN]



class WxAsciiArtist(gui.base.artists.ascii.AsciiArtist):
    def __init__(self, gameMap):
        ## Point size to use for drawing.
        self.pointSize = 12
        ## Font for drawing characters
        self.font = wx.Font(self.pointSize, wx.FONTFAMILY_TELETYPE, 
            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        ## Bitmap for drawing the map. It'll be recreated as needed, typically
        # when the window is resized.
        self.mapBitmap = None
        ## Bitmap for drawing the player status column.
        self.playerBitmap = None
        ## Bitmap for drawing prompts.
        self.promptBitmap = None
        ## Bitmap for drawing temporary overlays.
        self.overlayBitmap = None

        gui.base.artists.ascii.AsciiArtist.__init__(self, gameMap)
  

    ## Get the size of all ASCII characters, so we know how big a single
    # tile in the view is.
    def getBiggestCharacterDimensions(self):
        renderer = wx.GraphicsRenderer.GetDefaultRenderer()
        biggestChar = [0, 0]
        measureContext = renderer.CreateMeasuringContext()
        measureContext.SetFont(self.font)
        # Unicode characters can be 
        # unusually large; we'll assume we don't use those. 
        # \todo Find a better way to enumerate all draw-able (i.e. non-control-
        # character) ASCII chars.
        # \todo There's probably a better way to accomplish this in general,
        # actually -- do we really need to iterate over all the characters?
        # What about accented capital characters?
        for char in xrange(32, 127):
            char = unichr(char)
            extent = measureContext.GetFullTextExtent(char)
            width = extent[0]
            height = extent[1] + extent[2] + extent[3]
            if width > biggestChar[0]:
                biggestChar[0] = width
            if height > biggestChar[1]:
                biggestChar[1] = height
        return biggestChar


    ## Draw the game view ASCII-style (i.e. one character per tile).
    # We do this by generating an array of characters to display.
    @util.threads.classLocked
    def draw(self, dc, pixelWidth, pixelHeight, curPrompt, shouldRedrawAll): 
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
            self.mapBitmap = wx.EmptyBitmap(*size)
            self.playerBitmap = wx.EmptyBitmap(*size)
            self.promptBitmap = wx.EmptyBitmap(*size)
            self.overlayBitmap = wx.EmptyBitmap(*size)
            self.numColumns = numColumns
            self.numRows = numRows

        mapDC = wx.MemoryDC()
        mapDC.SelectObject(self.mapBitmap)
        blackBrush = wx.Brush((0, 0, 0), wx.SOLID)
        mapDC.SetBackground(blackBrush)
        mapDC.SetBrush(blackBrush)
        mapDC.SetFont(self.font)

        self.drawMap(mapDC, shouldRedrawAll)
        dc.Blit(0, 0, self.mapBitmap.GetWidth(), self.mapBitmap.GetHeight(), 
                mapDC, 0, 0)

        playerDC = wx.MemoryDC()
        playerDC.SelectObject(self.playerBitmap)
        playerDC.SetBackground(wx.Brush((0, 0, 0, 0)))
        playerDC.Clear()
        # Draw a black rectangle over the entire status region.
        playerDC.SetBrush(blackBrush)
        playerDC.DrawRectangle(0, 0, 
                self.numPlayerColumns * self.charWidth, 
                self.numRows * self.charHeight)
        playerDC.SetBrush(blackBrush)
        playerDC.SetFont(self.font)
        self.drawPlayerStatus(playerDC)
        dc.Blit(0, 0, self.playerBitmap.GetWidth(), 
                self.playerBitmap.GetHeight(), playerDC, 0, 0)

        if curPrompt is not None:
            # Draw the current prompt to its own bitmap, then draw that bitmap
            # on top of the main view.
            promptDC = wx.MemoryDC()
            promptDC.SelectObject(self.promptBitmap)
            # For now, we refresh the entire prompt every time.
            promptDC.SetBackground(wx.Brush((0, 0, 0, 0)))
            promptDC.Clear()
            promptDC.SetBrush(blackBrush)
            promptDC.SetFont(self.font)
            curPrompt.draw(promptDC, self, self.gameMap)
            dc.Blit(0, 0, self.promptBitmap.GetWidth(), 
                    self.promptBitmap.GetHeight(), promptDC, 0, 0)

        if self.overlayData is not None:
            # Draw our overlay data on top of everything.
            overlayDC = wx.MemoryDC()
            overlayDC.SelectObject(self.overlayBitmap)
            overlayDC.SetBackground(wx.Brush((0, 0, 0, 0)))
            overlayDC.Clear()
            overlayDC.SetBrush(blackBrush)
            overlayDC.SetFont(self.font)
            xMin, yMin = self.getUpperLeftCorner()
            for tile, symbol, color in self.overlayData:
                self.drawChar(overlayDC, symbol, color, 
                        tile[0] - xMin, tile[1] - yMin)
            dc.Blit(self.numPlayerColumns * self.charWidth, 0, 
                    self.overlayBitmap.GetWidth(), 
                    self.overlayBitmap.GetHeight(), overlayDC, 0, 0)
        events.publish("draw complete")


    ## Draw a character of the specified color at the specified position.
    def drawChar(self, dc, symbol, color, x, y):
        dc.SetTextForeground(color)
        drawX = x * self.charWidth
        drawY = y * self.charHeight
        # Ensure that anything under the symbol is erased.
        dc.DrawRectangle(drawX, drawY, self.charWidth, self.charHeight)
        dc.DrawText(symbol, drawX, drawY)


    ## Draw a rectangle of the specified color over the given cell range.
    def drawRectangle(self, dc, color, x, y, width, height):
        dc.SetBrush(wx.Brush(color, wx.SOLID))
        if width == -1:
            width = self.numColumns
        if height == -1:
            height = self.numRows
        dc.DrawRectangle(x * self.charWidth, y * self.charHeight, 
                width * self.charWidth, height * self.charHeight)
        # Revert back to a black brush since that's assumed by other drawing
        # functions.
        dc.SetBrush(wx.Brush((0, 0, 0), wx.SOLID))


    ## Copy the map bitmap over by the specified offset.
    def copyMapTo(self, dc, xOffset, yOffset):
        tempDC = wx.MemoryDC()
        tempBitmap = wx.EmptyBitmap(self.numColumns * self.charWidth,
                self.numRows * self.charHeight)
        tempDC.SelectObject(tempBitmap)
        tempDC.Blit(xOffset * self.charWidth, yOffset * self.charHeight,
                self.mapBitmap.GetWidth(), self.mapBitmap.GetHeight(), 
                dc, 0, 0)
        dc.Blit(0, 0,
                self.mapBitmap.GetWidth(), self.mapBitmap.GetHeight(), 
                tempDC, 0, 0)


