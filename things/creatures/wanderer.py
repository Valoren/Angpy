## Debug monster: wanders at random.

import container
import creature

import random

class Wanderer(creature.Creature):
    ## Pick a random adjacent free tile and move to it.
    def update(self):
        spaces = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], 
                [1, -1], [1, 0], [1, 1]]
        random.shuffle(spaces)
        for dx, dy in spaces:
            target = (self.pos[0] + dx, self.pos[1] + dy)
            if not self.gameMap.moveMe(self, self.pos, target):
                break

        
