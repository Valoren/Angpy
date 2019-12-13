import events

## Various constants (hereafter referred to as "abstract input") representing
# actions that can be taken. These are one of the fundamental ways that the UI
# layer communicates with the engine. The MOVE_* commands need to be first in
# this sequence, as well as in this specified order, since we rely on that in
# various places.
(MOVE_1, MOVE_2, MOVE_3, MOVE_4, REST, MOVE_6, MOVE_7, MOVE_8, MOVE_9,
        DESCEND, ASCEND, JUMP_LEVEL,
        GET_ITEM, DROP_ITEM, INSPECT_ITEM, WIELD_ITEM, REMOVE_ITEM,
        CREATE_ITEM, TWEAK_ITEM,
        LIST_INVENTORY, LIST_EQUIPMENT, DISPLAY_CHARACTER, RECALL_CREATURE,
        OPEN_ITEM, PUT_ITEM, THROW_ITEM,
        INVOKE_ITEM, AIM_ITEM, CAST_ITEM, QUAFF_ITEM, READ_ITEM, USE_ITEM, 
        ZAP_ITEM,
        TUNNEL, OPEN, CLOSE, LOOK, SCAN,
        WIZARD_MODE, TEST_COMMAND,
        QUIT, SAVE, LOAD) = range(43)


## List of commands that can be used to invoke the powers of an item.
USE_ITEM_COMMANDS = set([INVOKE_ITEM, AIM_ITEM, CAST_ITEM, QUAFF_ITEM, 
        READ_ITEM, USE_ITEM, ZAP_ITEM])


## List of positional offsets, useful for movement or looking up tiles
# adjacent to a given position. These correspond in order to the various
# MOVE_* commands (and REST), so their ordering is important.
DIRECTION_OFFSETS = [
        (-1, 1), (0, 1), (1, 1),
        (-1, 0), (0, 0), (1, 0),
        (-1, -1), (0, -1), (1, -1)]

## A Command is an action implemented upon the world, e.g. "move left" or
# "drink a Potion of Cure Light Wounds" or "cast the spell Magic Missile from
# the book Magic for Beginners at this tile". Commands typically start with
# an abstract input representing the verb that will be performed; they then
# generate Prompts that let them fill in any additional context they need
# (e.g. direct/indirect objects).
#
class Command:
    ## \param subject The Thing performing the Command.
    # \param input The abstract input code that was used to start the Command.
    def __init__(self, subject, input, gameMap):
        self.subject = subject
        self.input = input
        self.gameMap = gameMap

        ## Energy cost of performing the Command (i.e. how long it takes).
        self.energyCost = 0


    ## Acquire any additional context needed to execute the Command. This
    # typically involves making a series of Prompts for the UI to resolve.
    # Once all context is acquired, call self.execute().
    def contextualizeAndExecute(self):
        self.execute()


    ## Execute the Command, modifying the game state as needed. Then let the
    # UI layer know that the command has been completed.
    def execute(self):
        self.finalize()


    ## Subtract our energy cost, and publish an event indicating the command
    # is complete (mostly useful so that the game can update other actors).
    def finalize(self):
        self.subject.addEnergy(-self.energyCost)
        events.publish('command execution complete')



## Given an abstracted input (e.g. MOVE_4), convert the command into a
# movement offset.
def getDirectionFromInput(command):
    index = command - MOVE_1
    if index >= 0 and index <= 8:
        dx, dy = DIRECTION_OFFSETS[index]
        return (dx, dy)
    return None



import user
import wizardMode

## Maps abstracted inputs to the Command subclasses needed to execute them.
inputToCommandClassMap = {
        ASCEND: user.ClimbCommand,
        CLOSE: user.InteractNearbyCommand,
        CREATE_ITEM: wizardMode.CreateItemCommand,
        DESCEND: user.ClimbCommand,
        DISPLAY_CHARACTER: user.DisplayCharacterCommand,
        DROP_ITEM: user.InventoryCommand,
        JUMP_LEVEL: wizardMode.JumpLevelCommand,
        GET_ITEM: user.GetItemCommand,
        INSPECT_ITEM: user.InventoryCommand,
        LIST_EQUIPMENT: user.ItemListCommand,
        LIST_INVENTORY: user.ItemListCommand,
        LOAD: user.LoadCommand,
        LOOK: user.TargetCommand,
        MOVE_1: user.MovementCommand,
        MOVE_2: user.MovementCommand,
        MOVE_3: user.MovementCommand,
        MOVE_4: user.MovementCommand,
        MOVE_6: user.MovementCommand,
        MOVE_7: user.MovementCommand,
        MOVE_8: user.MovementCommand,
        MOVE_9: user.MovementCommand,
        OPEN: user.InteractNearbyCommand,
        OPEN_ITEM: user.InventoryCommand,
        PUT_ITEM: user.InventoryCommand,
        QUIT: user.QuitCommand,
        RECALL_CREATURE: user.RecallCreatureCommand,
        REMOVE_ITEM: user.EquipmentCommand,
        REST: user.RestCommand,
        SCAN: user.ScanCommand,
        SAVE: user.SaveCommand,
        TEST_COMMAND: wizardMode.TestCommand,
        THROW_ITEM: user.ThrowCommand,
        TUNNEL: user.InteractNearbyCommand,
        TWEAK_ITEM: user.InventoryCommand,
        WIELD_ITEM: user.EquipmentCommand,
        WIZARD_MODE: wizardMode.WizardCommand,
}

for command in USE_ITEM_COMMANDS:
    inputToCommandClassMap[command] = user.InventoryCommand

