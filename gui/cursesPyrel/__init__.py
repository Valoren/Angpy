import mainApp
import prompt
import messageFrame
import animation
import keymap
import gui
def init(gameMap):
    gui.prompt.setModule(prompt)
    gui.messenger.setModule(messageFrame)
    gui.animation.setModule(animation)
    gui.keymap = keymap.CursesKeymap()
    mainApp.Run(gameMap)


