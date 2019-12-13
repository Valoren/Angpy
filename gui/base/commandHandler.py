import threading
import types

import commands
import container
import events
import gui



## Encapsulates the common data structures and routines used in the main
# frame across UI implementations to handle communications between user
# command execution and their respective prompts
class CommandHandler(object):
    def __init__(self):
        super(CommandHandler, self).__init__()
        ## Current active prompt.
        self.curPrompt = None
        events.subscribe('resolve prompt', self.onResolvePrompt)
        events.subscribe('execute command', self.executeCommandId)
        events.subscribe('command execution complete', self.update)


    ##Implemented by subclass to communicate prompt cancellation
    def doesKeyCancelPrompt(self, keyEvent):
        raise NotImplementedError('%s is missing doesKeyCancelPrompt method required by super class' % self)


    def receiveKeyInput(self, keyEvent):
        if self.curPrompt is not None:
            # Interpret the input based on the prompt, instead of sending
            # a command to the game.
            if self.doesKeyCancelPrompt(keyEvent):
                # Run exit routines if any
                self.curPrompt.onCancel()
                # Cancel the current prompt.
                self.curPrompt = None
                events.publish('prompt complete', None)
            else:
                nextPrompt, promptResult = self.curPrompt.receiveKeyInput(
                        keyEvent, self.gameMap)
                if nextPrompt is None:
                    # End of prompting; publish the result and update our game
                    # state.
                    self.curPrompt = None
                    events.publish('prompt complete', promptResult)
                elif nextPrompt is not self.curPrompt:
                    # Resolve a new prompt.
                    gui.prompt.resolvePrompt(nextPrompt)
        else:
            # Create a new Command in a new thread to handle the input.
            threading.Thread(target = self.executeCommandId,
                    args = [gui.keymap.convertKeyToCommand(keyEvent)]).start()


    ## Given an input command ID, construct a Command and execute it.
    def executeCommandId(self, commandId, **kwargs):
        if commandId is None:
            # Not a valid input.
            return
        if commandId not in commands.inputToCommandClassMap:
            raise ValueError("Input with code %d does not map to any commands." % commandId)
        # \todo At this point, we're assuming that the player is the only
        # one performing Commands.
        player = self.gameMap.getContainer(container.PLAYERS)[0]
        newCommand = commands.inputToCommandClassMap[commandId](
                player, commandId, self.gameMap, **kwargs)
        newCommand.contextualizeAndExecute()


    ## Update our game state.
    def update(self):
        self.gameMap.update()


    ## Some other part of the code wants a prompt to be resolved; handle it.
    def onResolvePrompt(self, newPrompt):
        self.curPrompt = newPrompt
