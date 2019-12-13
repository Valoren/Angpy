## Artist that imitates an ASCII-mode drawing style.

import artist
import events
import container
import gui.colors
import gui.flavors
import procs.procData.element
import util.fieldOfView
import util.threads

import numpy

## Ordered list of what we want to draw -- the first thing to match gets 
# displayed.
DRAW_ORDER = [container.UPDATERS, container.ITEMS, container.TERRAIN]



class AsciiArtist(artist.Artist):
    def __init__(self, gameMap):
        artist.Artist.__init__(self, gameMap)
        ## List of [(position, symbol, color)] tuples to draw on top of 
        # everything else.
        self.overlayData = None
        # Get the size of all ASCII characters, so we know how big a single
        # tile in the view is.
        biggestChar = self.getBiggestCharacterDimensions()
        # Tile location to center display at
        self.centerTile = None
        ## Number of horizontal pixels to dedicate to each character we draw.
        # \todo Is casting to int here appropriate? We could be losing up to 
        # a pixel in each dimension...
        self.charWidth = int(biggestChar[0])
        ## Number of vertical pixels to dedicate to each character we draw.
        self.charHeight = int(biggestChar[1])
        ## Number of columns of characters to draw. Recalculated each time
        # self.draw is called.
        self.numColumns = None
        ## Number of rows, ditto.
        self.numRows = None
        ## Number of columns to dedicate to drawing the player status (thus,
        # not available for drawing the map).
        self.numPlayerColumns = 12
        ## Number of columns to dedicate to drawing the map. Recalculated in
        # self.drawMap.
        self.numMapColumns = None
        ## Precalculated bounding box (xMin, xMax, yMin, yMax); we adjust
        # this if necessary when self.draw is called. Measured in characters.
        self.boundingBox = None
        ## We need to access the player's knowledge of the game map so often,
        # it's simplest to keep a copy of the player handy.
        self.player = gameMap.getContainer(container.PLAYERS)[0]
        ## Set of dirty cells -- cells that have been modified since the last
        # time we drew them.
        self.dirtyCells = set()
        ## Maps cells to textual descriptions of what's displayed in them.
        self.cellToInfo = dict()
        ## Numpy array of booleans indicating if the given cell is visible
        # to the player or not. Will be initialized in drawMap().
        self.fovMap = None
        self.gameMap.addUpdateCellFunc(self.setCellDisplay)
   
        events.subscribe("center point for display", self.updateCenterTile)
        events.subscribe('new game map', self.onNewGameMap)


    ## A new GameMap was created; switch over to using it.
    def onNewGameMap(self, newMap):
        self.gameMap = newMap
        self.gameMap.addUpdateCellFunc(self.setCellDisplay)
        self.player = newMap.getPlayer()
        self.fovMap = None


    ## Mark a cell as being dirtied.
    @util.threads.classLocked
    def setCellDisplay(self, cell, item, wasItemAdded):
        # Only cells that the player can see can be dirtied.
        if not self.player.canSee(cell.pos):
            return
        if self.boundingBox is None:
            # Haven't drawn anything yet, so this is irrelevant.
            return
        x, y = cell.pos
        xMin, xMax, yMin, yMax = self.boundingBox
        if x < xMin or x > xMax or y < yMin or y > yMax:
            # Tile isn't actually visible, so we don't care.
            return
        self.dirtyCells.add(cell.pos)


    ## Return a (symbol, color) tuple indicating what to draw at the specified
    # map location.
    def getDisplayData(self, cellPos):
        # Find the highest-priority item in the cell and set that as the 
        # thing to be drawn.
        allThings = self.player.coordsToCell[cellPos]
        if not allThings:
            # Nothing there; draw a . instead for visible cells, and nothing
            # for non-visible ones.
            if self.player.canSee(cellPos):
                return ('.', 'WHITE')
            return (' ', 'BLACK')
        bestThing = None
        bestLayerIndex = None
        layers = set(DRAW_ORDER)
        for thing in allThings:
            memberships = self.gameMap.getMembershipsFor(thing)
            for layer in layers.intersection(memberships):
                layerIndex = DRAW_ORDER.index(layer)
                if (bestThing is None or
                        (layerIndex < bestLayerIndex and layer in memberships)):
                    bestThing = thing
                    bestLayerIndex = layerIndex
            if bestLayerIndex == 0:
                # Not going to get better than this.
                break

        if bestThing is None:
            return None
        
        symbol = bestThing.display['ascii']['symbol']
        color = bestThing.display['ascii']['color']
        if color == 'flavor':
            # Get the color based on the flavor of the item.
            color = gui.flavors.getColorNameForFlavor(bestThing.flavor)
            color = gui.colors.getColor(color)
        # \todo Is there a better way to do this check?
        elif type(color) in [str, unicode]:
            # Map from a color name to the color tuple.
            color = gui.colors.getColor(color)

        # Darken the color if the cell is not in the player's field of view.
        if not self.fovMap[cellPos]:
            color = [c / 2 for c in color]
        return (symbol, color)


    ## Draw the game view ASCII-style (i.e. one character per tile).
    # Child classes that implement this function should be sure to include
    # the decorator, which ensures that while it is running nothing will
    # try to change the data it draws.
    # \param dc Whatever drawing context is needed to draw the game view.
    # \param pixelWidth Width in pixels of the display.
    # \param pixelHeight Height in pixels of the display.
    # \param curPrompt A Prompt instance to draw on top of the game view (or
    #        None if there is no Prompt).
    # \param shouldRedrawAll True if we need to force a full-display refresh.
    @util.threads.classLocked
    def draw(self, dc, pixelWidth, pixelHeight, curPrompt, shouldRedrawAll):
        raise RuntimeError("ASCII Artist [%s] didn't implement its draw function" % str(type(self)))


    ## Draw a single character of the given color at the specified 
    # character coordinates (not pixel coordinates).
    def drawChar(self, dc, symbol, color, x, y):
        raise RuntimeError("ASCII Artist [%s] didn't implement its drawChar function" % str(type(self)))


    ## Draw the main game view -- a character for each tile in the map.
    def drawMap(self, dc, shouldRedrawAll):
        self.numMapColumns = self.numColumns - self.numPlayerColumns
        if self.centerTile is None:
            xMin, yMin = self.getUpperLeftCorner()
        else:
            xMin = max(0, self.centerTile[0] - self.numMapColumns / 2)
            yMin = max(0, self.centerTile[1] - self.numRows / 2)
 
        xMax = min(self.gameMap.width, xMin + self.numMapColumns)
        yMax = min(self.gameMap.height, yMin + self.numRows)
        
        #avoid overflowing
        if (xMin + self.numMapColumns > self.gameMap.width):
            xMin = self.gameMap.width - self.numMapColumns
        if (yMin + self.numRows > self.gameMap.height):
            yMin = self.gameMap.height - self.numRows

        if self.boundingBox != (xMin, xMax, yMin, yMax) and not shouldRedrawAll:
            # The bounding box has changed, either because the window resized
            # or because the screen has scrolled. Odds are that the screen
            # has scrolled, so we can save some effort by just redrawing
            # the current screen, shifted over a bit. 
            xOffset = xMin - self.boundingBox[0]
            yOffset = yMin - self.boundingBox[2]
            self.copyMapTo(dc, -xOffset, -yOffset)
            # Find tiles that weren't covered by this action, and mark them
            # as dirty. If we're below / to the right of where we used to be
            # (x/y offsets > 0) then the newly-exposed tiles are on the 
            # bottom and right borders, and vice versa.
            xVals = range(xMax - xOffset, xMax)
            yVals = range(yMax - yOffset, yMax)
            if xOffset < 0:
                xVals = range(xMin, xMin - xOffset)
            if yOffset < 0:
                yVals = range(yMin, yMin - yOffset)
            for x in xVals:
                self.dirtyCells.update([(x, y) for y in xrange(yMin, yMax)])
            for y in yVals:
                self.dirtyCells.update([(x, y) for x in xrange(xMin, xMax)])

        # Augment self.dirtyCells with all cells that entered / left the 
        # player's field of view.
        # First, initialize our array, if necessary.
        if self.fovMap is None:
            self.fovMap = numpy.zeros((self.gameMap.getDimensions()), 
                    dtype = numpy.bool)
        # Compare the player's map to our own map.
        player = self.gameMap.getContainer(container.PLAYERS)[0]
        xVals, yVals = numpy.where(self.fovMap != player.fovMap)
        # Update self.dirtyCells with the cells whose visibility status has
        # changed.
        self.dirtyCells.update(zip(xVals, yVals))
        # Copy the player's visibility map so we're ready for next time.
        self.fovMap[:] = player.fovMap

        # Make a copy since other threads may be modifying self.dirtyCells
        # while we're busy drawing.
        cellsToDraw = list(self.dirtyCells)
        if shouldRedrawAll:
            cellsToDraw = [(x, y)
                    for x in xrange(xMin, xMax)
                    for y in xrange(yMin, yMax)]

        for x, y in cellsToDraw:
            if x < xMin or x > xMax or y < yMin or y > yMax:
                continue
            symbol, color = self.getDisplayData((x, y))
            self.drawChar(dc, symbol, color, 
                    x - xMin + self.numPlayerColumns, y - yMin)
        self.boundingBox = (xMin, xMax, yMin, yMax)
        self.dirtyCells.clear()


    ## Draw the player status information, a fairly narrow but long column.
    def drawPlayerStatus(self, dc):
        player = self.gameMap.getContainer(container.PLAYERS)[0]
        # Start with HP and SP, color-coded by how full their respective pools
        # are. Cyan = full, red = empty.
        curRow = 0
        for label, current, maximum in [
                ('HP', player.curHitpoints, player.getStat('maxHitpoints')),
                ('SP', player.getStat('curSpellpoints'), player.getStat('maxSpellpoints'))]:

            percentage = 1
            if maximum:
                percentage = current / float(maximum)
            percentage = min(1, max(percentage, 0))
            hue = 360 - percentage * 120
            saturation = 1 - percentage / 2.0
            color = numpy.array(gui.colors.hsvToRgb(hue, saturation, 1)) * 255
            # Ramp up intensity as needed.
            magnitude = numpy.sqrt(sum(color * color))
            if magnitude < 255:
                color *= magnitude / 255.0
            self.writeString(dc, color, 0, curRow, '%s:' % label)
            currentLabel = "% 4d" % current
            self.writeString(dc, color, 3, curRow, currentLabel)
            self.writeString(dc, (255, 255, 255), 3 + len(currentLabel), 
                    curRow, '/')
            maxColor = numpy.array(gui.colors.hsvToRgb(240, .5, 1)) * 255
            self.writeString(dc, maxColor, 4 + len(currentLabel), curRow, 
                    '% 4d' % maximum)
            curRow += 1

        # Draw current stat values
        # \todo Recognize drained stats (how?)
        for statName in ['STR', 'INT', 'WIS', 'DEX', 'CON', 'CHA']:
            curVal = player.getStat(statName)
            self.writeString(dc, (255, 255, 255), 0, curRow, 
                    "%s:" % statName)
            self.writeString(dc, (127, 127, 255), 5, curRow, "% 3d" % curVal)
            curRow += 1

        # Draw current resistances.
        curRow = 10
        for i, element in enumerate(procs.procData.element.getAllElements()):
            # The color of the text is the element's color if the player has
            # resistance, or dark if not.
            color = gui.colors.getColor(element.display['ascii']['color'])
            if player.getStat('resist %s' % element.name) <= 0:
                color = gui.colors.getColor('L_DARK')
            self.writeString(dc, color, (i % 5) * 2, curRow, 
                    element.shortName, info = element.info)
            if i % 5 == 4:
                # Start a new row.
                curRow += 1


    ## Display a one-line string at the provided position.
    # The color is a color name, and not a UI-native color
    # \param info Optional string describing the contents being drawn.
    def writeString(self, dc, colorName, xPos, yPos, string, info = None):
        color = gui.colors.getColor(colorName)
        for i, char in enumerate(string):
            self.drawChar(dc, char, color, xPos + i, yPos)
            if info is not None:
                self.cellToInfo[(xPos + i, yPos)] = info


    ## Display a sequence of string pairs, where the first item in each pair
    # is left-aligned and the second item is right-aligned, with blank space
    # in between them. 
    def drawStrings(self, dc, strings, yOffset, minFirstLength = 20):
        if not strings:
            return
        longestFirst = max(minFirstLength, max([len(s[0]) for s in strings]))
        longestSecond = max([len(s[1]) for s in strings])

        # Need at least one space between the items.
        maxLen = longestFirst + longestSecond + 1
        for i, (first, second) in enumerate(strings):
            # First entry and spacer.
            spacer = ' ' * (maxLen - len(first) - len(second))
            self.writeString(dc, 'WHITE', self.numColumns - maxLen - 1,
                    i + 1, "%s%s" % (first, spacer))
            # Second entry.
            self.writeString(dc, 'WHITE', self.numColumns - len(second) - 1, 
                    i + 1, second)


    ## Draw a rectangle of the specified color over the given cell range.
    # If width or height is -1, it should be interpreted as "the full width"
    # or "the full height".
    def drawRectangle(self, dc, color, x, y, width, height):
        raise NotImplementedError("Artist of type %s didn't implement drawRectangle" % (str(self)))


    ## Update the location of the display
    @util.threads.classLocked
    def updateCenterTile(self, location):
        self.centerTile = location
    
    
    ## Return the tile position that's in the upper-left corner of the
    # drawable portion of the map.
    def getUpperLeftCorner(self):
        # Center the display on the player, but don't go off the end of the 
        # map.
        playerPos = list(self.gameMap.getContainer(container.PLAYERS)[0].pos)
        xOffset = max(playerPos[0] - (self.numMapColumns) / 2, 0)
        yOffset = max(playerPos[1] - self.numRows / 2, 0)
        return (xOffset, yOffset)


    ## Return a bounding box (x, y, width, height) describing the screen
    # position of the given tile.
    def getTileBox(self, pos):
        xOffset, yOffset = self.getUpperLeftCorner()
        dx = pos[0] - xOffset + self.numPlayerColumns
        dy = pos[1] - yOffset
        return (dx * self.charWidth, dy * self.charHeight, 
                self.charWidth, self.charHeight)


    ## Retrieve our character dimensions.
    def getCharSize(self):
        return (self.charWidth, self.charHeight)


    ## Receive a new list of [(position, symbol, color)] overlay data to draw.
    # Or receive None to disable overlay drawing.
    @util.threads.classLocked
    def setOverlay(self, newData):
        self.overlayData = newData


    ## Return the cell at the specified pixel coordinates.
    def getCellAt(self, x, y):
        xOffset, yOffset = self.getUpperLeftCorner()
        return (xOffset + x / self.charWidth, yOffset + y / self.charHeight)


    ## Get a description of whatever is shown at the specified pixel
    # coordinates -- potentially useful for mouse interactions.
    # Returns a list of strings.
    def getInfoAt(self, x, y):
        xOffset, yOffset = self.getUpperLeftCorner()
        cellX = xOffset + x / self.charWidth
        cellY = yOffset + y / self.charHeight
        if (cellX, cellY) in self.cellToInfo:
            return [self.cellToInfo[(cellX, cellY)]]
        elif cellX > self.numPlayerColumns:
            # Return a description of the contents of the map cell there.
            cellX += self.numPlayerColumns
            things = self.gameMap.getContainer((cellX, cellY))
            return [unicode(t) for t in things]
        # Nothing there to show.
        return []


    ## Return the view dimensions -- the number of visible rows and columns.
    def getViewDimensions(self):
        return (self.numColumns, self.numRows)

