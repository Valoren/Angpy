## This module creates the app and gets us up and running.

import gui

import argparse
import random
import sys
import time

# Simple utility function: print text, without a trailing newline, then force
def printFlush(text):
    print text,
    sys.stdout.flush()

parser = argparse.ArgumentParser()
parser.add_argument('--seed', dest = 'seed', default = int(time.time()))
parser.add_argument('--ui', dest='uimode', default = 'WX', choices = ['WX', 'CURSES', 'QT'])
args = parser.parse_args()

start = time.time()
seed = args.seed
print "Using random seed",seed
random.seed(seed)

# Compile Cython modules.
printFlush("Compiling Cython modules:")
import pyximport
pyximport.install()
printFlush("util.heatMap...")
import util.heatMap
printFlush("mapgen.gameMap...")
import mapgen.gameMap
printFlush("mapgen.cell...")
import mapgen.cell
print "done."

# Load data files.
print "Loading data:",
printFlush("procs...")
import procs.procLoader
procs.procLoader.loadFiles()
printFlush("proc data...")
import procs.procData
procs.procData.loadFiles()
printFlush("items...")
import things.items.itemLoader
things.items.itemLoader.loadFiles()
printFlush("creatures...")
import things.creatures.creatureLoader
things.creatures.creatureLoader.loadFiles()
printFlush("terrain...")
import things.terrain.terrainLoader
things.terrain.terrainLoader.loadFiles()
print "done."

# For now, create the player and game map here. This is clearly the wrong place,
# but we need to do it at some point, and for now we don't have the right
# point to do it, so we do it here.
print "Generating map."
import mapgen.gameMap
newMap = mapgen.gameMap.GameMap(120, 120)
import things.creatures.player
things.creatures.player.debugMakePlayer(newMap)
newMap.makeLevel(0)

gui.setUIMode(gui.__dict__[args.uimode])
print "Setup took %.2fs" % (time.time() - start)
print "Initializing GUI."
gui.init(newMap)
