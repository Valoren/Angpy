This directory is for code associated with creating the map of the game. 
Somewhat confusingly, in addition to level generation, it also holds the
gameMap.py and cell.py modules, which deal with tracking and organizing all 
game objects, including after the map has been generated.

 * accessibilityMap.py: handles pathfinding logic by creating a simplified
   version of the game map where tiles are either "open" or "blocked".
 * cell.pyx: the Cell class is the container class for the contents of a tile
   in the game map.
 * connection.py: ensures connectivity during dungeon generation.
 * gameMap.pyx: contains all game objects and contains functions for querying
   for specific objects or objects that meet certain conditions (e.g. all 
   items in a given tile, or all objects that can block LOS)
 * genCavern.py: creates organic-looking caverns.
 * genTown.py: creates Debug Town.
 * genUtility.py: utility functions relied on by other map-generation modules.
 * generationMap.py: handles intermediate representation of the map during
   map generation.
 * generator.py: top-level map-generation logic (starting from 
   makeAngbandLevel)
