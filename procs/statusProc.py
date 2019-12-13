import gui
import proc
import procUtil
import util

import random

# StatusProcs are just Procs, really; they're in this file to maintain some
# semblance of organization. Procs in this file should deal with the
# consequences of status ailments.
# Please keep Procs in this file alphabetized.



## Prevent an item from being used, optionally printing a message in the 
# process.
class PreventItemUseProc(proc.Proc):
    ## \param itemUseParams A UseItemParameters instance describing the 
    #         parameters of trying to use the item; see commands/user.py for 
    #         more information.
    def trigger(self, target, gameMap, item, itemUseParams, *args, **kwargs):
        if 'message' in self.params:
            procUtil.showCreatureMessage(self.params['message'], gameMap, 
                    target)
        itemUseParams.canUse = False
        itemUseParams.shouldChargeTime = False



## Randomizes the movement direction, with separate odds for moving in the 
# normal desired direction, to an adjacent direction, or to a randomly-selected
# direction (possibly including where they want to go or even standing still).
class RandomizeMovementProc(proc.Proc):
    ## \param motionParams A MotionParameters instance describing how the 
    #         target wants to move; see commands/user.py for more information.
    def trigger(self, target, gameMap, motionParams, *args, **kwargs):
        # Check for a message to print.
        if 'message' in self.params:
            procUtil.showCreatureMessage(self.params['message'], gameMap, 
                    target)
            
        if util.randomizer.passPercentage(self.params['successPercentage']):
            # target gets to move the way they wanted to.
            return
        elif util.randomizer.passPercentage(self.params['adjacentPercentage']):
            # target moves in an adjacent direction to what they wanted. 
            motionParams.direction = random.choice(
                    util.geometry.getAdjacentDirections(motionParams.direction)
            )
        else:
            # target moves in a wholly random direction, possibly including
            # staying fixed in place.
            motionParams.direction = (random.randint(-1, 1), random.randint(-1, 1))

