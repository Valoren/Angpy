## This module handles drawing animations for various effects. Each of the 
# drawFoo functions is a generator function, and is expected to yield a
# list of lists of (position, symbol, color) tuples describing what to draw on
# each frame of the animation.
import gui
import gui.colors
import util.geometry


## This decorator function causes the given function to be registered with 
# our display layer.
def register(func):
    def wrappedFunc(*args, **kwargs):
        generator = func(*args, **kwargs)
        gui.animation.receiveAnimation(generator)
    return wrappedFunc


## Maps direction offsets to the symbol used to display them.
PROJECTILE_SYMBOL_MAP = {
(0, 0): '*',
(1, 0): '-',
(-1, 0): '-',
(0, 1): '|',
(0, -1): '|',
(1, 1): '\\',
(-1, -1): '\\',
(-1, 1): '/',
(1, -1): '/',
}


## Send a projectile from the start position to the end position.
@register
def drawProjectile(start, end, displayData):
    color = gui.colors.getColor(displayData['ascii']['color'])
    tiles = util.geometry.getLineBetween(start, end)
    prevTile = start
    for tile in tiles:
        dx = tile[0] - prevTile[0]
        if dx:
            # Convert to +- 1
            dx = dx / abs(dx)
        dy = tile[1] - prevTile[1]
        if dy:
            # Convert to +- 1
            dy = dy / abs(dy)
        yield [(tile, PROJECTILE_SYMBOL_MAP[(dx, dy)], color)]


## Generate a "beam" from the start position to the end position. Like
# drawProjectile except that more characters are drawn, and we always use the 
# '*' symbol.
@register
def drawBeam(start, end, displayData):
    color = gui.colors.getColor(displayData['ascii']['color'])
    tiles = util.geometry.getLineBetween(start, end)
    accumulator = []
    for tile in tiles:
        accumulator.append((tile, '*', color))
        yield accumulator


## Draw an explosion at the specified center affecting the specified tiles.
@register
def drawExplosion(center, affectedTiles, displayData):
    color = gui.colors.getColor(displayData['ascii']['color'])
    yield [(tile, '*', color) for tile in affectedTiles]


## Draw a projectile from the start to the end, followed by an explosion at
# the end.
def drawExplosiveProjectile(start, end, affectedTiles, displayData):
    drawProjectile(start, end, displayData)
    drawExplosion(end, affectedTiles, displayData)

