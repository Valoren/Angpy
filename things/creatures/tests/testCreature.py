import unittest
import mapgen.gameMap
import mapgen.generator
import things.creatures.player
import container

import gui
def setupTestGUI():
    class TestGUI(object):
        def message(self, *args):
            print ' '.join(args)
    gui.messenger = TestGUI()

class TestCreature(unittest.TestCase):
    def setUp(self):
        setupTestGUI()
        newMap = mapgen.gameMap.GameMap(20,20)
        things.creatures.player.debugMakePlayer(newMap)
        mapgen.generator.makeDebugLevel(newMap, newMap.width, newMap.height)
        self.newMap = newMap

    def test_creature_die(self):
        players = self.newMap.getContainer(container.CREATURES, container.PLAYERS)
        creature = self.newMap.getContainer(container.CREATURES).getDifference(players)[0]
        creature.die(players[0])
        self.assertNotIn(creature,self.newMap.getContainer(container.CREATURES))

    def test_creature_move(self):
        players = self.newMap.getContainer(container.CREATURES, container.PLAYERS)
        creature = self.newMap.getContainer(container.CREATURES).getDifference(players)[0]
        memberships = set()
        memberships.update(self.newMap.getMembershipsFor(creature))
        x, y = creature.pos
        self.newMap.moveMe(creature,creature.pos,(x+1, y+1))
#        self.newMap.moveThing(creature,creature.pos,(x+1, y+1))
        memberships.remove((x,y))
        memberships.add((x+1,y+1))
        self.assertEquals(memberships,self.newMap.getMembershipsFor(creature))

    def test_creature_move_then_die(self):
        players = self.newMap.getContainer(container.CREATURES, container.PLAYERS)
        creature = self.newMap.getContainer(container.CREATURES).getDifference(players)[0]
        print self.newMap.thingToMemberships[creature]
        x, y = creature.pos
        self.newMap.moveMe(creature,creature.pos,(x+1, y+1))
        print self.newMap.thingToMemberships[creature]
        creature.die(players[0])
        self.assertNotIn(creature,self.newMap.getContainer(container.CREATURES))

