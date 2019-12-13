""" This is the Qt graphics module for Pyrel
"""
import gui
import prompt
import messageFrame
import animation
import keymap
import mainApp
def init(gameMap):
    gui.prompt.setModule(prompt)
    gui.messenger.setModule(messageFrame)
    gui.animation.setModule(animation)
    gui.keymap = keymap.QtKeymap()
    mainApp.makeApp(gameMap, [])

