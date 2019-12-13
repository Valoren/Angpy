import gui.base.artists.ascii
import container
import gui.colors
import util.threads


## Artist that imitates an ASCII-mode drawing style.
# Provides a common UI drawing abstractions for prompts
# to display their interfaces
class AsciiArtist(gui.base.artists.ascii.AsciiArtist):
    def __init__(self, gameMap):
        super(AsciiArtist, self).__init__(gameMap)
        # position last rendered to the upper corner of the map display
        # used to determine if full screen redraw is required when map
        # display shifts
        self.lastUpperLeftCorner = (None, None)


    ## A single text character is the highest resolution
    # of text-based display
    def getBiggestCharacterDimensions(self):
        return (1,1)


    ## Draw the game view ASCII-style (i.e. one character per tile).
    # Draw changes to game map, and then overlay animations and
    # the current prompt, if any
    # \param dc drawingcontext for lower level graphics drawing
    # \param width width of map display view
    # \param height height of map display view
    # \param curPrompt current prompt to overlay on map, if any
    # \param shouldRedrawAll flag to refresh the whole screen or only dirty data
    @util.threads.classLocked
    def draw(self, dc, width, height, curPrompt, shouldRedrawAll):
        if height != self.numRows or width != self.numColumns:
            shouldRedrawAll = True
            self.numRows = height
            self.numColumns = width
        self.drawMap(dc, shouldRedrawAll)
        self.drawPlayerStatus(dc)
        self.drawOverlay(dc)
        if curPrompt:
            curPrompt.draw(dc, self, self.gameMap)


    ## Draws the animation overlay
    # \param dc drawingcontext for lower level graphics drawing
    def drawOverlay(self, dc):
        if self.overlayData and self.boundingBox:
            xMin, xMax, yMin, yMax = self.boundingBox
            for tile, symbol, color in self.overlayData:
                x, y = tile
                if xMin <= x <= xMax and yMin <= y <= yMax:
                    self.drawChar(dc, symbol, color, x-xMin, y-yMin)


    ## Draw a character of the specified color at the specified position.
    # \param dc drawingcontext for lower level graphics drawing
    # \param color either rgb tuple or name of color in gui.colors map
    def drawChar(self, dc, char, color, x, y):
        dc.DrawText(char, x, y, color)


    ## Draw a rectangle of the specified color over the given cell range.
    def drawRectangle(self, dc, color, x, y, width, height):
        # \todo actually clear the region in question.
        dc.window.erase()

    ## Display a one-line string at the provided position.
    # The color is a color name, and not a UI-native color
    # \param dc drawingcontext for lower level graphics drawing
    # \info ignore tooltips for now
    def writeString(self, dc, colorName, xPos, yPos, string, info=None):
        dc.DrawText( string, xPos, yPos, colorName )


    ## Copy the map bitmap over by the specified offset.
    def copyMapTo(self, dc, xOffset, yOffset):
        dc.window.overwrite(dc.window,
                            min(xOffset,0),
                            min(yOffset,0),
                            max(xOffset,0),
                            max(yOffset,0),
                            self.numRows - max(0,xOffset),
                            self.numColumns - max(0,yOffset))
