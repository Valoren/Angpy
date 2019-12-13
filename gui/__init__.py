## This module serves as an interface to the various UI implementations. 
# The engine does "import gui" and then does all interactions directly through
# the gui module, instead of speaking to a specific UI layer.
# At program start, gui.setUIMode() must be called to set which UI
# implementation is used. 
#
# This module includes several "fake" submodules, which are really classes
# that the engine can speak to:
# - gui.prompt (lets the engine create Prompts)
# - gui.messenger (lets the engine send messages to the user)
import sys

## Valid UI modes. These need to match the ordering of the "choices" parameter
# in the pyrel module's commandline argument parser.
[WX, CURSES, QT] = range(3)

## This class serves as a wrapper that provides access to the classes 
# defined in a specific UI layer.
class FakeModule:
    ## Remap all of our items to point to the ones in the specified module.
    def setModule(self, module):
        for key, value in module.__dict__.iteritems():
            setattr(self, key, value)


## For creating Prompts
prompt = FakeModule()
## For sending messages
messenger = FakeModule()
## For drawing animation effects
animation = FakeModule()
## For handling keyboard inputs
keymap = None

## We'll need to track this across function calls
guiPackage = None

## Set the UI to use the specified mode. This imports that UI's specific
# modules to this namespace so that the engine can access it without
# needing to know what display mode is being used.
def setUIMode(mode):
    global guiPackage
    import base.animation
    animation.setModule(base.animation)
    import base.prompt
    prompt.setModule(base.prompt)
    if mode == WX:
        import wxPyrel as guiPackage
    elif mode == CURSES:
        import cursesPyrel as guiPackage
    elif mode == QT:
        import qtPyrel as guiPackage


## Perform any necessary UI initialization (creating windows, etc.).
# setUIMode() must have already been called.
def init(gameMap):
    global guiPackage
    guiPackage.init(gameMap)
