# Wizard-mode commands
#
# These commands are specifically used for "wizard-mode" debugging, and
# are those which do not duplicate normal game functionality

import commands
import container
import gui
import mapgen.gameMap
import things.items.itemAllocator
import things.items.itemLoader

import random

## This Command creates an item.
#
# It starts by displaying a selection of the type of generation, allowing
# random or specific selection, then displays further prompts for more
# information if necessary.
class CreateItemCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)
        ## Set if a specific item is to be created, rather than a random one
        # Choosing a specific base item sets self.specificItem to a (type,
        # subtype) tuple. Choosing a specific artifact sets it to the artifact
        # name.
        self.specificItem = None
        ## If a random item is being created, this gets set to the lootTemplate
        # used to generate it. If left as None, then a normal random item
        # (appropriate to the level will be generated.
        self.lootTemplate = None


    ## Collect the information we need, first allowing a choice of specific
    # items, lootTemplates or artifacts, or random items or artifacts
    # then any further information each of those options needs
    def contextualizeAndExecute(self):
        category = yield gui.prompt.resolvePrompt(
                gui.prompt.StringSelectionPrompt(message='What type of item?',
                container=['Specific artifact',
                           'Random artifact',
                           'Item from LootTemplate',
                           'Specific item',
                           'Random item']))

        if category == 'Specific artifact':
            self.specificItem = yield gui.prompt.resolvePrompt(
                    gui.prompt.StringSelectionPrompt(message='Which artifact?',
                    container=things.items.itemLoader.getArtifacts()))

        elif category == 'Random artifact':
            self.specificItem = random.choice(things.items.itemLoader.getArtifacts())

        elif category == 'Item from LootTemplate':
            selection = yield gui.prompt.resolvePrompt(
                    gui.prompt.StringSelectionPrompt(message='Which template?',
                    container=things.items.itemLoader.LOOT_TEMPLATE_MAP.keys()))
            self.lootTemplate = things.items.itemLoader.getLootTemplate(selection)

        elif category == 'Specific item':
            itemType = yield gui.prompt.resolvePrompt(
                    gui.prompt.StringSelectionPrompt(
                    message='Which type of item?',
                    container=things.items.itemLoader.getTypes()))
            itemSubType = yield gui.prompt.resolvePrompt(
                    gui.prompt.StringSelectionPrompt(
                    message='Which subtype of %s?' % itemType,
                    container=things.items.itemLoader.getSubTypes(itemType)))
            self.specificItem = (itemType, itemSubType)

        elif category == 'Random item':
            # Nothing to do, self.lootTemplate is already None
            pass

        self.execute()

    ## Now generate the item
    def execute(self):
        # Have to either create a specific item ... 
        if self.specificItem:
            item = things.items.itemLoader.makeItem(self.specificItem,
                    self.gameMap.mapLevel, self.gameMap, self.subject.pos)
        # ... or a random one, based on a lootTemplate
        else:
            if self.lootTemplate:
                self.lootTemplate.resolveValues(self.gameMap.mapLevel)
            allocator = things.items.itemAllocator.ItemAllocator(self.gameMap.mapLevel, self.lootTemplate)
            item = allocator.allocate(self.gameMap, self.gameMap.getContainer(self.subject.pos))
        # Inform the GUI of the item we've just created
        gui.messenger.message("Generated %s." % item.getShortDescription())
        item.pos = self.subject.pos



## This Command jumps straight to a particular level, prompting for which
class JumpLevelCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)


    def contextualizeAndExecute(self):
        self.newLevel = yield gui.prompt.resolvePrompt(
                gui.prompt.NumericPrompt(message='Which level? '))
        self.gameMap.makeLevel(self.newLevel)



## Test command
# This is a placeholder for testing other parts of the command and prompt
# objects. It's here so that you don't have to create a test framework and
# command structure just to test something.
#
# Feel free to change this to test anything you like
class TestCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)


    def contextualizeAndExecute(self):
        test = yield gui.prompt.resolvePrompt(
                gui.prompt.TextPrompt(message='Enter text: '))
        print 'Text entered was: %s' % test



## Central entry-point for all the debugging or "wizard-mode" commands
# Prompts for a further command key, and looks it up in a separate
# command set.
class WizardCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)


    def contextualizeAndExecute(self):
        player = self.gameMap.getContainer(container.PLAYERS)[0]
        if not player.hasUsedDebugCommands:
            isOk = yield gui.prompt.resolvePrompt(
                    gui.prompt.YesNoPrompt(message='You are about to use the dangerous and unsupported debug commands. This will permanently taint your character. Ok to continue?'))
            if not isOk:
                return
            player.hasUsedDebugCommands = True
        debugInput = yield gui.prompt.resolvePrompt(
                gui.prompt.CommandPrompt(message="Debug Command:", commandSet='wizard'))
        debugCommand = commands.inputToCommandClassMap[debugInput](
                player, debugInput, self.gameMap )
        yield debugCommand
