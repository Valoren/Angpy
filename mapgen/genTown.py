## This module will handle town generation.  For now it just makes
# a debug level that is entirely hardcoded for use in debugging.

import container
import gameMap
import generationMap
import genUtility
import things.terrain.terrainLoader
import things.creatures.player
import things.creatures.creatureLoader
import things.creatures.creatureAllocator
import things.items.itemLoader
import things.items.itemAllocator
import things.stats

def makeTownLevel(curMap, width, height):
    # make a generation map (which we won't use for now)
    genMap = generationMap.GenerationMap(width, height)
    
    # Make the surrounding ring of permanent walls
    genUtility.makeRectangleHollow(curMap, genMap, 0, 0, width - 1 , height - 1, 
            'permanent wall', priority = 10)

    # Clear everything else (maybe not necessary?)
    genUtility.makeRectangleFilled(curMap, genMap, 1, 1, width - 3, height - 3,
            None)

    things.terrain.terrainLoader.makeTerrain('down staircase', curMap, 
            (1, 1), 0)
    things.terrain.terrainLoader.makeTerrain('decorative floor tile', curMap, 
            (10, 10), 0)
    things.terrain.terrainLoader.makeTerrain('door', curMap, (9, 10), 0)
    things.terrain.terrainLoader.makeTerrain('door', curMap, (8, 10), 0)

    things.creatures.creatureLoader.makeCreature("Filthy street urchin", curMap, (8, 8))
    things.creatures.creatureLoader.makeCreature("Red mold", curMap, (7, 8))
    things.creatures.creatureLoader.makeCreature("Farmer Maggot", curMap, (6, 8))
    things.items.itemLoader.makeItem(('helm', 'full helm'), 0, curMap, (1, 2))
    dagger = things.items.itemLoader.makeItem(('sword', 'dagger'), 0, curMap, (4, 4))
    dagger.stats.addMod('slay townsfolk', things.stats.StatMod(0, 2))
    dagger = things.items.itemLoader.makeItem(('sword', 'dagger'), 0, curMap, (3, 6))
    dagger.stats.addMod('fire brand', things.stats.StatMod(0, 2))
    things.items.itemLoader.makeItem(('magic book', '[Magic for Beginners]'), 
            0, curMap, (2, 4))
    things.items.itemLoader.makeItem(('ring', 'Prowess'), 80, curMap, (2, 5))
    things.items.itemLoader.makeItem(('ring', 'Finesse'), 80, curMap, (1, 5))
    things.items.itemLoader.makeItem(('ring', 'Slaying'), 80, curMap, (3, 5))
    things.items.itemLoader.makeItem(('spike', 'iron spike'), 0, curMap, (3, 3))
    things.items.itemLoader.makeItem(('potion', 'Cure Light Wounds'), 0, curMap, (3, 2))
    things.items.itemLoader.makeItem(('potion', 'Speed'), 0, curMap, (3, 2))
    things.items.itemLoader.makeItem(('food', 'ration of food'), 0, curMap, (3, 6))

    things.items.itemLoader.makeItem(('scroll', 'Light'), 80, curMap, (4, 5))
    things.items.itemLoader.makeItem(u'Galadriel', 80, curMap, (8, 8))
    things.items.itemLoader.makeItem(u'Thr\u00e1in', 80, curMap, (9, 8))

    things.items.itemLoader.makeItem(('container', 'small wooden chest'), 0, 
            curMap, (5, 4))
    quiver = things.items.itemLoader.makeItem(('container', 'quiver'), 0, curMap, (5, 5))
    arrows = things.items.itemLoader.makeItem(('arrow',), 0, curMap, (5, 6))
    quiver.addItemToInventory(arrows)
    curMap.removeSubscriber(arrows, (5, 6))

    r = things.items.itemLoader.makeItem(('ring', 'Slaying'), 80, curMap, (8, 5))
    affix = things.items.itemLoader.getAffix("Strength")
    affix.applyAffix(10, r)
    affix = things.items.itemLoader.getAffix("Resist Fire")
    affix.applyAffix(10, r)
    affix = things.items.itemLoader.getAffix("Resist Cold")
    affix.applyAffix(10, r)


    player = curMap.getContainer(container.PLAYERS)[0]
    player.pos = (4, 4)
    curMap.addSubscriber(player, (4, 4))
    

    # A test pattern to explore.
    for x in xrange(20, width - 20, 4):
        for y in xrange(20, height - 20, 4):
            wall = things.terrain.terrainLoader.makeTerrain('granite wall', curMap, (x, y), 0)
            wall.display = {'ascii': {'color': (255, 0, 0), 'symbol': '#'}}
            wall = things.terrain.terrainLoader.makeTerrain('granite wall', curMap, (x + 1, y), 0)
            wall.display = {'ascii': {'color': (0, 255, 0), 'symbol': '#'}}
            wall = things.terrain.terrainLoader.makeTerrain('granite wall', curMap, (x, y + 1), 0)
            wall.display = {'ascii': {'color': (0, 0, 255), 'symbol': '#'}}
            wall = things.terrain.terrainLoader.makeTerrain('granite wall', curMap, (x + 1, y + 1), 0)
            wall.display = {'ascii': {'color': (255, 255, 0), 'symbol': '#'}}
