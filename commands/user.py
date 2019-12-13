import container
import events
import gui
import commands
import things.creatures.creatureLoader



## This Command simply interacts with stairs (and anything else that is an
# ASCENDABLE or DESCENDABLE). We use the same command for both
# up and down as their behaviors are almost identical.
class ClimbCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)
        self.energyCost = 1


    def execute(self):
        actionMap = {
                commands.ASCEND: (container.ASCENDABLES, 'up', 'ascend'),
                commands.DESCEND: (container.DESCENDABLES, 'down', 'descend')}
        bucket, direction, trigger = actionMap[self.input]
        stairs = self.gameMap.getContainer(self.subject.pos, bucket)
        if not stairs:
            gui.messenger.message("There is no way %s here." % direction)
            return
        stairs[0].interact(trigger, self.subject, self.gameMap, self.subject.pos)
        commands.Command.execute(self)



## This Command shows the player's stats to them.
class DisplayCharacterCommand(commands.Command):
    def contextualizeAndExecute(self):
        gui.prompt.resolvePrompt(
                gui.prompt.DisplayCreaturePrompt(self.subject))
        self.execute()



## Maps inputs to verbs describing them, as well as whether we start from the
# subject's inventory or their equipment.
EQUIPMENT_COMMAND_MAP = {
        commands.WIELD_ITEM: ('Wield', True),
        commands.REMOVE_ITEM: ('Remove', False),
}


## This Command handles interactions with the subject's equipment.
class EquipmentCommand(commands.Command):
    def __init__(self, *args, **kwargs):
        ## Item to be interacted with.
        self.selection = kwargs.pop('item', None)
        ## Slot item is in / is going to go in.
        self.slotDesc = None

        commands.Command.__init__(self, *args, **kwargs)
        self.energyCost = 1
        ## Verb describing the action.
        self.verb, shouldUseInventory = EQUIPMENT_COMMAND_MAP[self.input]
        self.targetContainer = self.subject.inventory
        if not shouldUseInventory:
            self.targetContainer = self.subject.equipment


    def contextualizeAndExecute(self):
        if self.selection is None:
            # Get the item the user wants to interact with.
            self.selection = gui.prompt.resolvePrompt(
                    gui.prompt.ItemListPrompt("%s which item?" % self.verb,
                    self.targetContainer))
            if self.selection is None:
                # Cancelled.
                return
        if self.input == commands.WIELD_ITEM:
            # Keep prompting the user for an item to equip until they select
            # one that is actually equippable.
            while not self.selection.equipSlots:
                gui.messenger.message("That item cannot be equipped.")
                self.selection = gui.prompt.resolvePrompt(
                        gui.prompt.ItemListPrompt("%s which item?" % self.verb,
                        self.targetContainer))
                if self.selection is None:
                    # Cancelled.
                    return
            # Find the slot the item is to go in. In the event of ambiguity,
            # prompt the user for which slot to use.
            # We assume that if there is any open slot, then the item can
            # go in that slot, so the only case in which there is ambiguity is
            # if all slots are already filled.
            itemSlotTypes = self.selection.equipSlots
            filledSlotDescs = []
            for slot in itemSlotTypes:
                if slot in self.subject.equipSlotToDescs:
                    for desc in self.subject.equipSlotToDescs[slot]:
                        if desc not in self.subject.equipment:
                            # Slot is empty, so we can stop now.
                            self.slotDesc = desc
                            break
                        else:
                            filledSlotDescs.append(desc)
                if self.slotDesc:
                    # Already found a match, so we can stop.
                    break
            if not self.slotDesc:
                # Couldn't find an empty slot to stick the item in.
                if len(filledSlotDescs) == 1:
                    # There's only one possibility, so no ambiguity.
                    self.slotDesc = filledSlotDescs[0]
                else:
                    # There's multiple possibilities; prompt the user for
                    # which to replace.
                    lines = []
                    for desc in filledSlotDescs:
                        lines.append("%s: %s" % (desc,
                            self.subject.equipment[desc].getShortDescription()))
                    self.slotDesc = gui.prompt.resolvePrompt(
                            gui.prompt.StringSelectionPrompt(
                            "Replace which equipped item?",
                            container.Container(members = lines)))
                    if self.slotDesc is None:
                        # Cancelled.
                        return
                    # \todo This is a pretty hacky way to extract the equipment
                    # slot back out.
                    self.slotDesc = self.slotDesc.split(':')[0]
        elif self.input == commands.REMOVE_ITEM:
            # Find the slot the item is currently in.
            for slotDesc, item in self.subject.equipment.iteritems():
                if item is self.selection:
                    self.slotDesc = slotDesc
                    break
        self.execute()


    def execute(self):
        if self.input == commands.WIELD_ITEM:
            if not self.slotDesc:
                # We were unable to find a valid slot to stick the item in.
                gui.messenger.message("You are unable to equip this item.")
            else:
                # Remove any item currently in the slot.
                if self.slotDesc in self.subject.equipment:
                    self.subject.unequipItem(self.slotDesc)
                # Add the item to the subject's equipment, and remove it from
                # their inventory.
                self.subject.equipItem(self.selection, self.slotDesc)
                self.subject.inventory.unsubscribe(self.selection)
        elif self.input == commands.REMOVE_ITEM:
            self.subject.unequipItem(self.slotDesc)
        commands.Command.execute(self)



## This command picks up items from the floor beneath the subject.
# \todo Allow selecting multiple items.
class GetItemCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)
        self.energyCost = 1
        ## Item the user wants to get.
        self.selection = None


    def contextualizeAndExecute(self):
        items = self.gameMap.getContainer(self.subject.pos, container.ITEMS)
        if len(items) == 1:
            # Only one possibility; no need to prompt the user.
            self.selection = items[0]
        elif len(items) > 1:
            # Multiple possibilities; prompt the user.
            self.selection = gui.prompt.resolvePrompt(
                    gui.prompt.ItemListPrompt(message = "Pick up what items?",
                    container = items))
            if self.selection is None:
                # Cancelled.
                return
        self.execute()


    def execute(self):
        if self.selection is None:
            gui.messenger.message("There is nothing to pick up.")
            return
        # Remove the item from the tile it currently occupies.
        self.gameMap.removeSubscriber(self.selection, self.subject.pos)
        gui.messenger.message("Picked up", self.selection.getShortDescription())
        self.subject.addItemToInventory(self.selection)
        commands.Command.execute(self)



## Maps commands to the containers they correspond to, as well as appropriate
# descriptions for the action.
INTERACTION_COMMAND_MAP = {
        commands.OPEN: (container.OPENABLES, 'Open'),
        commands.CLOSE: (container.CLOSABLES, 'Close'),
        commands.TUNNEL: (container.TUNNELABLES, 'Tunnel through'),
}

## This Command handles interacting with various Things that the subject may
# be adjacent to (e.g. opening/closing doors/chests, tunneling through walls,
# disarming traps). We try to automatically figure out what should be
# interacted with, but in the case of ambiguity we prompt for a direction.
class InteractNearbyCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)
        self.energyCost = 1
        ## Target Thing to interact with.
        self.target = None
        ## Position of that Thing
        self.targetPosition = None
        ## Container to search through, and message to display if none such
        # is available.
        self.containerType, self.message = INTERACTION_COMMAND_MAP[self.input]


    def contextualizeAndExecute(self):
        isSelectionAmbiguous = False
        curTarget = None
        # We track this separately because some terrain does not have a proper
        # pos field.
        targetPosition = None
        pos = self.subject.pos
        for dx, dy in commands.DIRECTION_OFFSETS:
            loc = (pos[0] + dx, pos[1] + dy)
            targets = self.gameMap.getContainer(loc, self.containerType)
            if targets:
                if curTarget:
                    # There's more than one possible direction to open things
                    # in, so we'll have to ask the user for a direction.
                    isSelectionAmbiguous = True
                    curTarget = None
                    break
                curTarget = targets[0]
                targetPosition = loc

        if isSelectionAmbiguous:
            # Prompt the user for a direction and take the first openable
            # from that direction.
            direction = gui.prompt.resolvePrompt(
                    gui.prompt.DirectionPrompt("%s what?" % self.message))
            if direction is None:
                # Cancelled.
                return
            dx, dy = direction
            loc = (pos[0] + dx, pos[1] + dy)
            targets = self.gameMap.getContainer(loc, self.containerType)
            if targets:
                curTarget = targets[0]
                targetPosition = loc

        self.target = curTarget
        self.targetPosition = targetPosition
        self.execute()


    ## Interact with the current target, if it is valid.
    # \todo It'd be nice if we didn't have a big if/elif/etc. block here, but
    # I can't think of a non-hackish way to stuff the necessary information
    # into INTERACTION_COMMAND_MAP.
    def execute(self):
        if self.target is None:
            gui.messenger.message("There is nothing there to %s." % self.message.lower())
        else:
            action = {commands.OPEN: 'open',
                      commands.CLOSE: 'close',
                      commands.TUNNEL: 'tunnel'}[self.input]
            self.target.interact(action, self.subject, self.gameMap, self.targetPosition)
        commands.Command.execute(self)



## Maps inputs to the verbs used to describe them and the filters used to
# reduce the available options, for InventoryCommand instances.
INVENTORY_COMMAND_MAP = {
        commands.DROP_ITEM: ('Drop', None),
        commands.INSPECT_ITEM: ('Inspect', None),
        commands.OPEN_ITEM: ('Open', container.CARRIERS),
        commands.PUT_ITEM: ('Put', None),
        commands.TWEAK_ITEM: ('Tweak', None),
}
# Augment with the various extra "use item" commands
for command in commands.USE_ITEM_COMMANDS:
    INVENTORY_COMMAND_MAP[command] = ('Use', container.USABLES)



## Parameters for attempting to use items; these can be mutated by Procs.
# This is just a simple container class.
class UseItemParameters:
    def __init__(self, canUse, shouldChargeTime):
        self.canUse = canUse
        self.shouldChargeTime = shouldChargeTime



## This Command handles interactions with items in the subject's inventory
# or equipment.
class InventoryCommand(commands.Command):
    def __init__(self, *args, **kwargs):
        ## Item to interact with.
        self.targetItem = kwargs.pop('item', None)
        commands.Command.__init__(self, *args)
        self.energyCost = 1
        self.verb, self.filter = INVENTORY_COMMAND_MAP[self.input]
        ## For putting items into / out of containers, the container to
        # interact with.
        self.targetContainer = None
        ## For putting items into / out of containers, whether we are putting
        # into or removing out of.
        self.amPuttingIntoContainer = False


    def contextualizeAndExecute(self):
        if self.targetItem is None:
            bucket = self.subject.inventory
            if self.filter is not None:
                bucket = self.gameMap.filterContainer(bucket, self.filter)
            self.targetItem = gui.prompt.resolvePrompt(
                    gui.prompt.ItemListPrompt("%s which item?" % self.verb,
                    bucket))
            if self.targetItem is None:
                # Cancelled.
                return
        if self.input == commands.INSPECT_ITEM:
            temp = container.Container(members = set([self.targetItem]))
            gui.prompt.resolvePrompt(
                    gui.prompt.DetailedItemPrompt(
                        "Examining %s" % self.targetItem.getShortDescription(),
                        container = temp))
            return
        elif self.input == commands.PUT_ITEM:
            # We either put the item into our subject's inventory if it's
            # currently in a container, or vice versa.
            for item in self.subject.inventory:
                if (item.isContainer() and item.contains(self.targetItem) and
                        item.getCanModifyInventory()):
                    self.targetContainer = item
                    break
            if self.targetContainer is None:
                self.amPuttingIntoContainer = True
                # Prompt the user for a container to put the item into.
                containerItems = self.gameMap.filterContainer(
                        self.subject.inventory, container.CARRIERS)
                # Further filter the containers based on if they can accept
                # the specified item.
                containerItems = filter(lambda c: c.getCanCarryItem(self.targetItem), containerItems)
                containerItems = container.Container(members = set(containerItems))
                if containerItems:
                    self.targetContainer = gui.prompt.resolvePrompt(
                            gui.prompt.ItemListPrompt(
                                message = "Put into what container?",
                                container = containerItems))
                    if self.targetContainer is None:
                        # Cancelled.
                        return
        self.execute()


    ## Call the appropriate method on the subject to deal with the item.
    # \todo Find a better way to map inputs to the functions to call?
    def execute(self):
        # Allow procs to mutate what we do based on these parameters.
        if self.input == commands.DROP_ITEM:
            self.subject.dropItem(self.targetItem)
        elif self.input in commands.USE_ITEM_COMMANDS:
            # Allow procs to change what we do. 
            params = UseItemParameters(canUse = True, shouldChargeTime = True)
            useVerb = self.targetItem.useVerb
            self.subject.triggerProcs(useVerb, target = self.subject, 
                    gameMap = self.gameMap, item = self.targetItem, 
                    itemUseParams = params)
            if params.canUse:
                self.subject.useItem(self.targetItem)
            elif not params.shouldChargeTime:
                # Don't charge the user for the action.
                return
        elif self.input == commands.OPEN_ITEM:
            self.targetItem.setIsOpen(not self.targetItem.isOpen())
            # Just redisplay the inventory with the now-toggled container.
            ItemListCommand(self.subject, self.input, self.gameMap).contextualizeAndExecute()
        elif self.input == commands.PUT_ITEM:
            if self.amPuttingIntoContainer:
                if not self.targetContainer:
                    gui.messenger.message("You have nothing to put it into.")
                else:
                    # Transfer from inventory to container.
                    self.targetContainer.addItemToInventory(self.targetItem)
                    self.subject.removeItemFromInventory(self.targetItem)
            else:
                # Transferm from container to inventory.
                self.targetContainer.removeItemFromInventory(self.targetItem)
                self.subject.addItemToInventory(self.targetItem)
        elif self.input == commands.TWEAK_ITEM:
            self.subject.tweakItem(self.targetItem)
        commands.Command.execute(self)



## This Command requests an item from the subject's inventory or equipment, and
# on selection gives them a list of interactions they can perform with the
# item.
class ItemListCommand(commands.Command):
    def __init__(self, *args, **kwargs):
        ## Item we are interacting with.
        self.item = kwargs.pop('item', None)
        commands.Command.__init__(self, *args, **kwargs)
        ## Command we are performing with the item.
        self.command = None


    def contextualizeAndExecute(self):
        items = self.subject.inventory
        message = 'inventory'
        if self.input == commands.LIST_EQUIPMENT:
            items = self.subject.equipment
            message = 'equipment'
        self.item = gui.prompt.resolvePrompt(gui.prompt.ItemListPrompt(
                message = "Examining %s" % message,
                container = items))
        if self.item is None:
            # Cancelled.
            return
        # Scan for containers the item could be put into or taken out of.
        # \todo Should allow interacting with containers on floor / in
        # equipment, not just in inventory.
        canInteractWithContainers = False
        for item in self.subject.inventory:
            if (item.isContainer() and
                    (item.getCanCarryItem(self.item) or item.contains(self.item))):
                canInteractWithContainers = True
                break
        self.command = gui.prompt.resolvePrompt(
                gui.prompt.InteractWithItemPrompt("What do you want to do?",
                    container = container.Container(members = set([self.item])),
                    canInteractWithContainers = canInteractWithContainers)
        )
        if self.command is None:
            # Cancelled.
            return
        self.execute()


    ## Generate a new command with the given item.
    def execute(self):
        if self.command is not None:
            events.publish('execute command', self.command, 
                    subject = self.subject, input = self.command, 
                    gameMap = self.gameMap, item = self.item)



## Simple container class holding the parameters for MovementCommands.
class MotionParameters:
    def __init__(self, direction, distance):
        self.direction = direction
        self.distance = distance


## This Command handles moving about the map. The only context we need is
# provided by our input, which maps to a direction.
class MovementCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)
        self.energyCost = 1


    def execute(self):
        direction = commands.getDirectionFromInput(self.input)
        # Allow procs to change how we move.
        params = MotionParameters(direction, 1)
        self.subject.triggerProcs('move', target = self.subject, 
                gameMap = self.gameMap, motionParams = params)
        target = (self.subject.pos[0] + params.direction[0] * params.distance,
                self.subject.pos[1] + params.direction[1] * params.distance)
        # Ensure we don't try to punch ourselves in the face when not moving.
        didAttack = False
        if target != self.subject.pos:
            obstructions = self.gameMap.moveMe(self.subject, self.subject.pos,
                    target)
            if obstructions:
                # Cause the subject to attempt to attack the things in the way.
                opponents = self.gameMap.filterContainer(obstructions, 
                        container.ATTACKERS)
                # Cast to list so we can handle things getting destroyed
                # mid-loop.
                for opponent in list(opponents):
                    self.subject.meleeAttack(opponent)
                    didAttack = True
        if didAttack:
            # We assume that attacking handles its own energy costs.
            self.energyCost = 0
        commands.Command.execute(self)



##Command for scanning, the capital 'L'ook command
class ScanCommand(commands.Command):
    def contextualizeAndExecute(self):
        self.dir = gui.prompt.resolvePrompt(
                 gui.prompt.ScanPrompt(None, None))



## This Command quits the game
class QuitCommand(commands.Command):
    def contextualizeAndExecute(self):
        shouldQuit = gui.prompt.resolvePrompt(gui.prompt.YesNoPrompt(
                message = "Really quit?"))
        if shouldQuit:
            self.execute()


    def execute(self):
        # Do other quitting things here, like saving
        # Finally tell the UI layer to quit
        events.publish("user quit")



## This Command lets the user pull up information on a creature, by asking
# for a name string and finding creatures that match it.
class RecallCreatureCommand(commands.Command):
    def contextualizeAndExecute(self):
        name = gui.prompt.resolvePrompt(
                gui.prompt.TextPrompt(message = "Creature name (or portion of name): "))
        if name is None:
            # Cancelled.
            return
        name = name.lower()
        creature = things.creatures.creatureLoader.getFactory(name,
                isCaseSensitive = False)
        if creature is None:
            # Not a valid name; try to find all creatures that match instead.
            options = []
            for creature in things.creatures.creatureLoader.getAllFactories():
                if name in creature.getName().lower():
                    options.append(creature.getName())
            if len(options) == 1:
                # Exactly one match, so we've found what the user wants.
                creature = things.creatures.creatureLoader.getFactory(options[0])
            elif options:
                # Multiple matches; prompt the user.
                options.sort()
                name = gui.prompt.resolvePrompt(
                        gui.prompt.StringSelectionPrompt(
                        message = "Couldn't find \"%s\"; did you mean one of these?" % name,
                        container = options)
                )
                if name is None:
                    # Cancelled.
                    return
                creature = things.creatures.creatureLoader.getFactory(name)
            else:
                gui.messenger.message("Couldn't find any creatures with names like \"%s\"" % name)
                creature = None
        if creature is not None:
            gui.prompt.resolvePrompt(
                    gui.prompt.RecallCreaturePrompt(creature))
        self.execute()



## This Command just passes the turn.
class RestCommand(commands.Command):
    def __init__(self, *args):
        commands.Command.__init__(self, *args)
        self.energyCost = 1



## This Command saves the game.
class SaveCommand(commands.Command):
    def execute(self):
        self.gameMap.save()
      


## This Command loads a saved game.
class LoadCommand(commands.Command):
    def execute(self):
        self.gameMap.load()



## This Command just creates a TargetPrompt to let the user look around.
class TargetCommand(commands.Command):
    def contextualizeAndExecute(self):
        self.target = gui.prompt.resolvePrompt(
                gui.prompt.TargetPrompt(None, None))
        self.execute()


    ## Set the subject's current target.
    def execute(self):
        self.subject.curTarget = self.target
        commands.Command.execute(self)



## This Command prompts the user for an item to throw and a direction to
# throw it in.
class ThrowCommand(commands.Command):
    def __init__(self, *args, **kwargs):
        ## Item being thrown
        self.targetItem = kwargs.pop('item', None)
        commands.Command.__init__(self, *args, **kwargs)
        ## Direction being thrown in.
        self.direction = None
        ## Alternately, location being thrown at.
        self.targetTile = None


    def contextualizeAndExecute(self):
        if self.targetItem is None:
            self.targetItem = gui.prompt.resolvePrompt(
                    gui.prompt.ItemListPrompt(
                        message = "Throw which item?",
                        container = self.subject.inventory)
            )
            if self.targetItem is None:
                # Cancelled.
                return
        if self.subject.curTarget is not None:
            # Use the subject's previous target.
            if type(self.subject.curTarget) is tuple:
                self.targetTile = self.subject.curTarget
            else:
                self.targetTile = self.subject.curTarget.pos
        else:
            # Prompt the user for a direction.
            self.direction = gui.prompt.resolvePrompt(
                    gui.prompt.DirectionPrompt("Throw in which direction?"))
            if self.direction is None:
                # Cancelled.
                return
        self.execute()


    def execute(self):
        end = self.targetTile
        if self.targetTile is None:
            end = (self.subject.pos[0] + self.direction[0] * 30,
                    self.subject.pos[1] + self.direction[1] * 30)
        gui.animation.drawProjectile(self.subject.pos, end, self.targetItem.display)
        commands.Command.execute(self)
