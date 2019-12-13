## Load terrain records from terrain.txt, and create Terrains for them.

import terrain
import util.record

import json
import os

## Maps terrain names to TerrainFactory instances.
TERRAIN_NAME_MAP = dict()
def getTerrainFactory(name):
    if name not in TERRAIN_NAME_MAP:
        raise RuntimeError("Invalid terrain name: [%s]" % name)
    return TERRAIN_NAME_MAP[name]


## Make a Terrain instance straight up, without requiring a Factory to be 
# made first.
def makeTerrain(name, gameMap, pos, mapLevel):
    factory = getTerrainFactory(name)
    return factory.makeTerrain(gameMap, pos, mapLevel)


## Load our data files.
def loadFiles():
    terrainFactories = util.record.loadRecords(
            os.path.join('data', 'terrain.txt'),
            terrain.TerrainFactory)
    for terrainFactory in terrainFactories:
        TERRAIN_NAME_MAP[terrainFactory.name] = terrainFactory


