## Template class for all artists.

class Artist(object):
    def __init__(self, gameMap):
        ## We'll need to keep track of the game state if we want to draw it!
        self.gameMap = gameMap


    ## Draw the current game state.
    # \param dc Whatever drawing context is needed for drawing the map.
    # \param pixelWidth Width in pixels of the display
    # \param pixelHeight Height in pixels of the display
    def draw(self, dc, pixelWidth, pixelHeight):
        raise RuntimeError("This artist failed to implement its draw function.")
