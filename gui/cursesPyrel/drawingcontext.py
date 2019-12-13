import curses

import gui.colors


## Finds the magnitude of distance (squared) between two rgb vectors
# \param rgb1 - (red, green, blue) tuple
# \param rgb2 - (red, green, blue) tuple
def color_distance(rgb1, rgb2):
    return sum([n**2 for n in map(lambda x, y: x-y, rgb1, rgb2)])

## Color table currently supported by 8 and 16 color displays
XTERM_16_RGB_COLORS = [
    (0, 0, 0),
    (205, 0, 0),
    (0, 205, 0),
    (205, 205, 0),
    (0, 0, 238),
    (205, 0, 205),
    (0, 205, 205),
    (229, 229, 229),
    (127, 127, 127),
    (255, 0, 0),
    (0, 255, 0),
    (255, 255, 0),
    (92, 92, 255),
    (255, 0, 255),
    (0, 255, 255),
    (255, 255, 255)
]


## Specialized dictionary mapping rgb values to the indices of the
# respective rgb colors supported by xterm compatible terminal emulations
# This class implements a singleton cache shared by all DrawingContext
# instances.  It will map any rgb color tuple to its nearest xterm color
class TermColorMap(dict):
    def __init__(self):
        super(TermColorMap, self).__init__()

        if curses.COLORS >= 256:
            #  of a 256 color term.
            self.COLORS = 256
            cincr = [0] + [95+40*n for n in range(5)]
            rgbToTerm = [(i,j,k) for i in cincr for j in cincr for k in cincr]
            rgbToTerm = dict(zip(range(16, len(rgbToTerm)+16), rgbToTerm))
            rgbToTerm.update(zip(range(232,256),
                                 [(n,n,n) for n in range(8,248,10)]))
        elif curses.COLORS in [8,16]:
            self.COLORS = curses.COLORS
            rgbToTerm = dict(zip(range(self.COLORS),
                                 XTERM_16_RGB_COLORS[:self.COLORS]))
        #initialize a corresponding color_pair (foreground, background)
        #with background set to black for each of the 256 colors
        #These color pairs are used by DrawingContext drawing primitives
        for color in rgbToTerm.keys():
            if color > 0:  # term color 0 is fixed to white in curses
                assert color < curses.COLOR_PAIRS
                curses.init_pair(color, color, 0)
        self.rgbToTerm = rgbToTerm

    ## Finds the standard 256 term color index closest to the given rgb color
    # \param rgb - (red, green, blue) tuple
    def __missing__(self, rgb):
        term_color = min([(color_distance(rgb, v), k)
                         for k, v in self.rgbToTerm.iteritems()])[1]
        self[rgb] = term_color
        return term_color

## Singleton instance of TermColorMap
termColorMap = None

## Manages TermColorMap singleton and access to its map
# \param rgb color tuple
def mapTermColor(rgb):
    global termColorMap
    if termColorMap is None:
        termColorMap = TermColorMap()
    return termColorMap[rgb]

## Abstraction of lower level drawing primitives available to Artist
# classes and prompt drawing methods.  Ideally, all calls to curses drawing
# primitives should appear in this class.
# \todo support more curses drawing attributes (reverse fg/bg colors, bold, blink?)
class DrawingContext(object):
    def __init__(self, window):
        self.hasColors = curses.has_colors() and curses.COLORS >= 8
        self.window = window


    ## method to ensure position text can be passed to curses API
    def isTextInBounds(self, x, y, text):
        yMin, xMin = self.window.getbegyx()
        if x < xMin or y < yMin:
            return False
        yMax, xMax = self.window.getmaxyx()
        if x > xMax or y > yMax:
            return False
        return True


    ## clears all text from window
    def Clear(self):
        self.window.erase()


    ## draw positioned colored text to window
    def DrawText(self, text, x, y, color=None):
        if not self.isTextInBounds(x, y, text):
            return
        if self.hasColors and color is not None:
            if isinstance(color,basestring):
                color = gui.colors.getColor(color)
            term_color = mapTermColor(tuple(color))
            self.window.addstr(y, x, text.encode('utf-8'), curses.color_pair(term_color))
        else:
            self.window.addstr(y, x, text.encode('utf-8'))
