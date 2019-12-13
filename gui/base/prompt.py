# Please keep the classes in this file alphabetized, after the initial Prompt
# class.
import commands
import container
import events
import gui
import things.mixins.carrier
import util.geometry



## Prompts are requests to the user to provide some information (e.g. an item
# to interact with, a tile to target, a simple yes/no question, etc.). There
# can be one Prompt active at a time, though they may chain into each other;
# most of the Command classes simply create a sequence of Prompts and then
# perform some action with the resulting information. 
class Prompt(object):
    ## \param message Text message to display for the prompt.
    # \param container Container we're displaying the prompt for, if
    #        applicable.
    # \param callback Function to call with the user's answer, if applicable.
    def __init__(self, message = '', container = None):
        self.message = message
        self.container = container


    ## Draw the Prompt. By default we just draw our message.
    def draw(self, dc, artist, gameMap):
        artist.writeString(dc, 'WHITE', 0, 0, self.message)


    ## Receive keyboard input, and return a result tuple 
    # (nextPrompt, promptResult). nextPrompt is a new Prompt to display, if 
    # applicable (or self, if we aren't done yet); promptResult is the final
    # information provided by this Prompt. 
    def receiveKeyInput(self, input, gameMap):
        raise RuntimeError("%s didn't implement its receiveKeyInput function" % self)


    def __unicode__(self):
        return '<Prompt "%s">' % self.message


    def onCancel(self):
        pass



## This prompt displays a message, then waits for a further command
# passing the input back as the result of the prompt
class CommandPrompt(Prompt):
    def __init__(self, commandSet='normal', *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        self.commandSet = commandSet


    def receiveKeyInput(self, input, gameMap):
        command = gui.keymap.convertKeyToCommand(input, self.commandSet)
        if command:
            return (None, command)
        return (self, None)



## This Prompt simply displays detailed information about an item -- there's
# no question being asked, the user just has to clear the prompt when they're
# done.
class DetailedItemPrompt(Prompt):
    def draw(self, dc, artist, gameMap):
        artist.writeString(dc, 'WHITE', 0, 0, self.message)
        item = self.container[0]
        artist.writeString(dc, 'WHITE', 0, 1,
                "This is %s" % item.getShortDescription())
        artist.writeString(dc, 'WHITE', 0, 2,
                "Its typing is (%s, %s)" % (item.type, item.subtype))
        artist.writeString(dc, 'WHITE', 0, 3, item.description)
        offset = 4
        if item.procs:
            artist.writeString(dc, 'WHITE', 0, offset, "Item procs:")
            for i, proc in enumerate(item.procs):
                artist.writeString(dc, 'WHITE', 0, 5 + i, str(proc))
            offset += i + 3
        artist.writeString(dc, 'WHITE', 0, offset, "Item modifiers:")
        for i, (key, value) in enumerate(item.stats.listMods()):
            artist.writeString(dc, 'WHITE', 0, offset + i + 1,
                    "%s: %s" % (key, value))
        # Dump raw stats for debugging item generation
        offset += i + 3
#        artist.writeString(dc, 'GREEN', 0, offset, "Raw stats: %s" % item.stats)
        # Dump affix data
        artist.writeString(dc, 'WHITE', 0, offset, "Item affixes:")
        for i, affix in enumerate(item.affixes):
            artist.writeString(dc, 'WHITE', 0, offset + i + 1,
                    "%s: %s %s" % (affix['name'], affix['affixType'], affix['affixLevel']))
#        offset += i + 3
#        if item.lootTemplate is not None:
#            artist.writeString(dc, 'RED', 0, offset, "Loot template: %s" % item.lootTemplate.templateName)


    ## keep displaying self until prompt is cancelled
    def receiveKeyInput(self, input, gameMap):
        return (self, None)



## This Prompt requests the user to input a direction. Call our callback with
# the direction, as a 2D tuple.
class DirectionPrompt(Prompt):
    ## Ignore any input that is not a direction.
    def receiveKeyInput(self, input, gameMap):
        command = gui.keymap.convertKeyToCommand(input)
        direction = commands.getDirectionFromInput(command)
        if direction is None:
            return (None, None)
        else:
            return (self, direction)



## Display the stats on the provided creature.
class DisplayCreaturePrompt(Prompt):
    def __init__(self, creature):
        Prompt.__init__(self)
        self.creature = creature


    ## Any input causes us to return to normal gameplay.
    def receiveKeyInput(self, input, gameMap):
        return (self, None)


    ## For now, just draw a list of stats.
    def draw(self, dc, artist, gameMap):
        strings = []
        for statName, mod in self.creature.stats.listMods():
            strings.append((statName, str(mod)))
        strings.append(("Flags:", ", ".join(self.creature.flags)))
        artist.drawStrings(dc, strings, 0, 0)



## This Prompt asks a user what exactly they want to do with a given Item.
class InteractWithItemPrompt(Prompt):
    def __init__(self, *args, **kwargs):
        ## Whether or not the item in question could be put into or taken out
        # of a container.
        self.canInteractWithContainers = kwargs.pop('canInteractWithContainers', False)
        Prompt.__init__(self, *args, **kwargs)
        ## The item we're interacting with.
        self.item = self.container[0]
        ## List of actions we can perform with the item. This doesn't exist
        # until we're drawn, since we don't currently have access to the
        # GameMap and thus the player.
        self.interactions = []


    ## Draw a list of actions the user can perform
    def draw(self, dc, artist, gameMap):
        self.interactions = [
                (commands.INSPECT_ITEM, 'Inspect'),
                (commands.DROP_ITEM, 'Drop'),
                (commands.THROW_ITEM, 'Throw'),
        ]
        if self.canInteractWithContainers:
            self.interactions.append(
                    (commands.PUT_ITEM, 'Put into/out of container'))
        if self.item.isContainer():
            text = ['Open', 'Close'][self.item.isOpen()]
            self.interactions.append((commands.OPEN_ITEM, text))
        player = gameMap.getContainer(container.PLAYERS)[0]
        if self.item in player.equipment.values():
            # Item is currently equipped.
            self.interactions.append((commands.REMOVE_ITEM, 'Take off'))
        elif self.item.canEquip():
            # Item is not equipped but could be.
            self.interactions.append((commands.WIELD_ITEM, 'Wield'))
        if self.item.canUse():
            self.interactions.append((commands.USE_ITEM, 'Use'))
        artist.writeString(dc, 'WHITE', 0, 0, self.item.getShortDescription())
        artist.writeString(dc, 'WHITE', 0, 1, 'What do you want to do?')
        strings = []
        for command, text in self.interactions:
            key = gui.keymap.convertCommandToKey(command)
            strings.append(('%s)' % chr(key), text))
        artist.drawStrings(dc, strings, 2)


    ## Just perform the corresponding command to the input, on the item.
    def receiveKeyInput(self, input, gameMap):
        desiredCommand = gui.keymap.convertKeyToCommand(input)
        for command, text in self.interactions:
            if command == desiredCommand:
                return (None, command)
        # No valid command. 
        return (self, None)



## This Prompt displays a list of Items and asks the user to select one. We
# invoke our callback with the selection if one is made.
class ItemListPrompt(Prompt):
    def __init__(self, *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        if self.container is None:
            raise RuntimeError("ItemListPrompt created without a container of items")


    ## Interpret keys as indexes into the list.
    # \todo What if the container is too big to handle with just the keys?
    def receiveKeyInput(self, input, gameMap):
        key = gui.keymap.getKey(input)
        try:
            index = ord(chr(key).lower()) - ord('a')
        except ValueError:
            index = -1
        result = things.mixins.carrier.indexIntoInventory(self.container,
                index)
        if result is not None:
            return (None, result)
        return (self, None)


    ## Draw the Prompt.
    def draw(self, dc, artist, gameMap):
        artist.writeString(dc, 'WHITE', 0, 0, self.message)
        strings = []
        for mark, desc, weight in self.getItemStrings():
            strings.append(("%s %s" % (mark, desc), weight))
        artist.drawStrings(dc, strings, 1)


    ## Generate a list of tuples of
    # (selection label, item description, item weight).
    # For example,
    # ("c)", "10 Potions of Cure Light Wounds", "1.0")
    # or
    # ("f) on your head", "a Steel Helmet [6, +0]", "4.5")
    # We display the contents of containers indented a level.
    def getItemStrings(self):
        items = None
        if isinstance(self.container, container.ContainerMap):
            items = self.container.items()
        else:
            items = things.mixins.carrier.generateItemList(self.container)
        selectors = []
        names = []
        weights = []
        offset = 0
        for entry in items:
            selectors.append(chr(ord('a') + offset) + ')')
            offset += 1
            item = entry
            indent = ''
            if isinstance(self.container, container.ContainerMap):
                key, item = entry
                # Add the key to the selector.
                selectors[-1] += ' %s:' % key
            else:
                # Each entry is a length-N tuple of items describing the
                # containers that an item is in.
                item = entry[-1]
                indent = '  ' * (len(entry) - 1)
            names.append(indent + item.getShortDescription())
            weights.append("%3.1f" % (item.quantity * item.getStat('weight') + .05))

        return zip(selectors, names, weights)


## Prompt for a number to be entered
class NumericPrompt(Prompt):
    def __init__(self, shouldStopOnOtherKey=False, *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        self.number = 0
        self.shouldStopOnOtherKey = shouldStopOnOtherKey


    def receiveKeyInput(self, input, gameMap):
        digit = gui.keymap.convertKeyToNumber(gui.keymap.getKey(input))
        if digit is None:
            if self.shouldStopOnOtherKey or gui.keymap.isReturnKey(input):
                return (None, self.number)
        else:
            self.number = self.number * 10 + digit
        self.message += str(digit)
        return (self, None)



## Prompt for pulling up information on a creature.
# In practice, we just hand off to a proc since procs know what information
# is important enough to show.
class RecallCreaturePrompt(Prompt):
    def __init__(self, creature, *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        ## A CreatureFactory instance for the creature we're supposed to
        # display.
        self.creature = creature


    ## Any input cancels the Prompt.
    def receiveKeyInput(self, *args):
        return (None, True)


    ## Just hand off to the creature and tell them to invoke their
    # "on recall" procs.
    def draw(self, dc, artist, gameMap):
        self.creature.triggerProcs('display recall', self.creature,
                dc, artist, gameMap)


## Prompt for Scanning the level
class ScanPrompt(Prompt):
    def __init__(self, *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        self.message = "Scanning"
        ## Current tile for screen center.
        self.centerTile = None


    ## Direction to scan
    def receiveKeyInput(self, input, gameMap):
        if self.centerTile is None:
            player = gameMap.getContainer(container.PLAYERS)[0]
            self.centerTile = list(player.pos)
        command = gui.keymap.convertKeyToCommand(input)
        if command is not None:
            direction = commands.getDirectionFromInput(command)
            ## Shift direction by 50/25 squares.  This number should
            # probably be based on how many columns/rows there are
            # but I couldn't figure out how to implement that.
            if direction:
                #New x direction
                if direction[0] < 0:
                    self.centerTile[0] = max(0,
                        self.centerTile[0] + direction[0] * 50)
                if direction[0] > 0:
                    self.centerTile[0] = min(gameMap.width,
                        self.centerTile[0] + direction[0] * 50)
                # New y direction
                if direction[1] < 0:
                    self.centerTile[1] = max(0,
                        self.centerTile[1] + direction[1] * 25)
                if direction[1] > 0:
                    self.centerTile[1] = min(gameMap.width,
                        self.centerTile[1] + direction[1] * 25)
            events.publish('center point for display', self.centerTile)
        return (self, None)


    def draw(self, dc, artist, gameMap):
        artist.writeString(dc, 'WHITE', 0, 0, self.message)
        artist.drawMap(dc, False)


    def onCancel(self):
        events.publish('center point for display', None)



## This Prompt asks the user to choose from a list of options.
class StringSelectionPrompt(Prompt):
    def __init__(self, *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        ## The offset in the container where the currently displayed set of
        # strings starts
        self.displayOffset = 0
        ## The max number of strings that can be displayed
        self.displayLength = 23
        ## The currently displayed set of strings
        self.displayedStrings = self.getSubset()


    def receiveKeyInput(self, input, gameMap):
        key = gui.keymap.getKey(input)
        try:
            index = ord(chr(key).lower()) - ord('a')
        except ValueError:
            index = -1
        if index >= 0 and index < len(self.displayedStrings):
            item = self.displayedStrings[index]
            if item == '--more--':
                self.nextScreen()
                return (self, None)
            elif item == '--back--':
                self.prevScreen()
                return (self, None)
            else:
                return (None, item)
        else:
            return (self, None)


    ## Get one screen's worth of strings from the container
    # If this subset doesn't go to the end, then replace the
    # last entry with '--more--'
    # If this subset doesn't start at the beginning, then
    # start with '--back--'
    def getSubset(self):
        start = self.displayOffset
        if start:
            subset = ['--back--']
            numberLeft = self.displayLength - 1
        else:
            subset = []
            numberLeft = self.displayLength
        subset.extend(self.container[start:start + numberLeft])
        if start + numberLeft < len(self.container):
            subset[self.displayLength - 1] = '--more--'
        return subset


    ## Display the next screen of strings
    def nextScreen(self):
        if self.displayOffset:
            self.displayOffset += self.displayLength - 2
        else:
            self.displayOffset += self.displayLength - 1
        self.displayedStrings = self.getSubset()


    ## Display the previous screen of strings
    def prevScreen(self):
        self.displayOffset -= self.displayLength - 2
        if self.displayOffset == 1:
            self.displayOffset = 0
        self.displayedStrings = self.getSubset()


    ## Draw the Prompt. We draw each string to its own line.
    def draw(self, dc, artist, gameMap):
        artist.writeString(dc, 'WHITE', 0, 0, self.message)
        strings = []
        for i, string in enumerate(self.displayedStrings):
            mark = chr(ord('a') + i)
            # \todo Having the empty string here just so we can work with
            # artist.drawStrings' assumption that we're passing in string
            # pairs is pretty hacky.
            strings.append(("%s) %s" % (mark, string), ''))
        artist.drawStrings(dc, strings, 1, 20)



## This Prompt allows the entry of a free-form string
class TextPrompt(Prompt):
    def __init__(self, *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        self.inputText = u''
        self.originalMessage = self.message


    def receiveKeyInput(self, input, gameMap):
        key = gui.keymap.getKey(input)
        if gui.keymap.isReturnKey(input):
            return (None, self.inputText)
        (isDelete, direction) = gui.keymap.isDeleteKey(input)
        if isDelete:
            self.inputText = self.inputText[:-1]
        elif key < 256:
            self.inputText += unicode(chr(key))
        self.message = self.originalMessage + self.inputText
        return (self, None)



## This Prompt just asks the user a yes/no question.
# \todo Allow yes to be the default response; currently no is always the
# default.
class YesNoPrompt(Prompt):
    ## Interpret 'y' or 'Y' as affirmative; everything else is negative. In
    # any case, we exit immediately.
    def receiveKeyInput(self, input, gameMap):
        key = gui.keymap.getKey(input)
        return (None, key < 256 and chr(key) in ['y','Y'])


    def draw(self, dc, artist, gameMap):
        artist.writeString(dc, 'WHITE', 0, 0, self.message)



## This Prompt lets the user select a tile or creature on the map, and stick
# it into the TARGETED container in the game map.
class TargetPrompt(Prompt):
    def __init__(self, *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        ## Currently-targeted tile.
        self.targetTile = None
        ## Whether we are skipping over non-interesting tiles.
        self.amSkippingBoringTiles = True


    ## Return True if the provided input selects the current tile as the
    # target.
    def doesKeySelectTarget(self, input):
        raise NotImplementedError("%s class is missing doesKeySelectTarget required by super class TargetPrompt" % self)


    ## Return True if the provided input switches between manual positioning,
    # and skipping over boring tiles.
    def doesKeySwitchModes(self, input):
        return gui.keymap.getKey(input) == ord('o')


    ## Move the cursor around, or select a tile.
    def receiveKeyInput(self, input, gameMap):
        if self.doesKeySelectTarget(input):
            # Select something to target in the current tile. Either a
            # Creature, or the tile itself.
            creatures = gameMap.getContainer(tuple(self.targetTile), container.CREATURES)
            if not creatures:
                return (None,tuple(self.targetTile))
            else:
                return (None,creatures[0])
        elif self.doesKeySwitchModes(input):
            self.amSkippingBoringTiles = not self.amSkippingBoringTiles
            return (self, None)

        command = gui.keymap.convertKeyToCommand(input)
        if command is None:
            return (self, None)

        direction = commands.getDirectionFromInput(command)
        if not direction:
            return (self, None)

        if self.amSkippingBoringTiles:
            # Scan outwards from our current targetTile to find the closest
            # interesting thing vaguely in the specified direction.
            width, height = gameMap.getDimensions()
            for cell in util.geometry.generateCone(self.targetTile, direction):
                if ((cell[0] < 0 or cell[0] >= width) and
                        (cell[1] < 0 or cell[1] >= height)):
                    # Ran out of map to examine.
                    break
                contents = gameMap.filterContainer(
                        gameMap.getContainer(cell),
                        container.INTERESTING)
                if contents:
                    # Found a cell with something interesting in it.
                    self.targetTile = cell
                    break
        else:
            self.targetTile = (self.targetTile[0] + direction[0],
                    self.targetTile[1] + direction[1])
        events.publish('center point for display', self.targetTile)
        return (self, None)


    ## Draw a box around our current tile, and print a description of its
    # contents.
    def draw(self, dc, artist, gameMap):
        ## Initialize self.targetTile now.
        # \todo I'm pretty sure this is guaranteed to happen before
        # self.receiveKeyInput can be called, but is it really?
        if self.targetTile is None:
            player = gameMap.getContainer(container.PLAYERS)[0]
            self.targetTile = list(player.pos)
        self.drawTargetDetails(dc, artist, gameMap)


    def drawTargetDetails(self, dc, artist, gameMap):
        artist.writeString(dc, 'WHITE', 0, 0,
                u"Targeting (%d, %d)" % tuple(self.targetTile))
        contents = gameMap.getContainer(tuple(self.targetTile))
        if contents:
            strings = map(unicode, contents)
            maxLen = max(map(len, strings))
            for i, desc in enumerate(strings):
                artist.writeString(dc, 'WHITE', artist.numColumns - maxLen,
                        i + 1, desc)


    def onCancel(self):
        events.publish('center point for display', None)



## Handle a request by something elsewhere in the code that needs information
# from the user. Suspend this thread while we wait for that 
# information to be provided. 
def resolvePrompt(newPrompt):
    # Send the new prompt to the I/O execution context, and wait for it to 
    # respond that the prompt has been resolved via a "prompt complete" event.
    result = events.executeAndWaitFor('prompt complete', 
            events.publish, 'resolve prompt', newPrompt)
    return result
