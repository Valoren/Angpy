import container
import gui.colors
import proc
import procData
import util.boostedDie
import util.grammar

import numpy

# DisplayProcs are Procs that do drawing. They're thus sort of in the UI 
# layer.



## Handles displaying information about the creature.
class CreatureRecallProc(proc.Proc):
    def trigger(self, creature, dc, artist, gameMap):
        player = gameMap.getContainer(container.PLAYERS)[0]
        numColumns, numRows = artist.getViewDimensions()
        # Clear the background.
        artist.drawRectangle(dc, 'BLACK', 0, 0, -1, -1)
        # Start off with their name, symbol, level, speed, HP, EXP reward, 
        # and kill count, all on the same line.
        artist.writeString(dc, 'WHITE', 0, 0, creature.name)
        nameLen = len(creature.name)
        # Draw the symbol, with appropriate color.
        artist.writeString(dc, 'WHITE', nameLen + 1, 0, '(')
        artist.writeString(dc, creature.display['ascii']['color'], 
                nameLen + 2, 0, creature.display['ascii']['symbol'])
        artist.writeString(dc, 'WHITE', nameLen + 3, 0, ')')

        # Draw native depth.
        artist.writeString(dc, 'WHITE', nameLen + 5, 0, 'Level:')
        artist.writeString(dc, 'BLUE_SLATE', nameLen + 12, 0, str(creature.nativeDepth))
        # Draw hitpoints.
        artist.writeString(dc, 'WHITE', nameLen + 17, 0, 
                '%dHP' % creature.getStat('maxHitpoints'))
        # Draw speed. Adjust color so faster monsters look nastier (up to 
        # speed of 4).
        artist.writeString(dc, 'WHITE', nameLen + 26, 0, 'Speed:')
        speed = creature.getStat('speed')
        speedColor = gui.colors.hsvToRgb(min(360, 240 + 30 * speed),
                .5 + speed / 8.0, 1)
        speedColor = numpy.array(speedColor) * 255
        artist.writeString(dc, speedColor, nameLen + 33, 0, 
                "%.2f" % speed)
        # Draw experience reward.
        artist.writeString(dc, 'WHITE', nameLen + 38, 0, 
                "%dXP" % creature.experienceValue)
        # Draw kill count.
        count = player.getKnowledge('creature', creature.name, 'kills')
        if count is None:
            artist.writeString(dc, 'WHITE', numColumns - 9, 0, 'No kills')
        else:
            text = "%d kill%s" % (count, ['', 's'][count != 1])
            artist.writeString(dc, 'WHITE', numColumns - len(text) - 1, 0, text)

        # Draw melee attacks in a column on the left.
        artist.writeString(dc, 'ORANGE', 0, 1, 'Melee')
        artist.writeString(dc, 'WHITE', 5, 1, ':')
        knownBlows = []
        for i, blow in enumerate(creature.blows):
            damageRange = player.getKnowledge('creature', creature.name, 'blows', i)
            if damageRange is not None:
                knownBlows.append((blow, damageRange))
        if not knownBlows:
            # Special text for creatures with no attacks.
            artist.writeString(dc, 'GREEN', 0, 2, 'No known attacks!')
        for i, (blow, damageRange) in enumerate(knownBlows):
            offset = 0
            damage = "%d-%d" % damageRange
            if damageRange[0] == damageRange[1]:
                damage = str(damageRange[0])
            artist.writeString(dc, 'WHITE', 0, i + 2, damage)
            offset += len(damage) + 1
            # Draw element.
            if 'element' in blow:
                # Draw element short name.
                element = procData.element.getElement(blow['element'])
                artist.writeString(dc, element.display['ascii']['color'], 
                        offset, i + 2, element.shortName)
                offset += len(element.shortName) + 1
            # Draw verb.
            artist.writeString(dc, 'WHITE', offset, i + 2, blow['verb'])
            offset += len(blow['verb']) + 1
            # Draw effect, if any.
            if 'proc' in blow:
                artist.writeString(dc, 'WHITE', offset, i + 2, blow['proc'])

        # Draw elemental resistances in a block on the right. Only draw
        # elements where the player knows, one way or another, if the target
        # is resistant.
        artist.writeString(dc, 'ORANGE', 40, 1, 'Resistances')
        artist.writeString(dc, 'WHITE', 51, 1, ':')
        columnOffset = 40
        for i, element in enumerate(procData.element.getAllElements()):
            # Note, hasResistance is None for "player doesn't know".
            hasResistance = player.getKnowledge('creature', creature.name, 
                    'resist %s' % element.name)
            if hasResistance is not None:
                color = [gui.colors.getColor('L_DARK'), 
                        element.display['ascii']['color']][hasResistance]
                artist.writeString(dc, color, columnOffset, 2, 
                        element.shortName)
            columnOffset += len(element.shortName)
            
        # Draw evasion/absorption below the resistances.
        evasion = player.getKnowledge('creature', creature.name, 'evasion')
        if evasion is not None:
            artist.writeString(dc, 'ORANGE', 40, 3, 'Evasion')
            artist.writeString(dc, 'WHITE', 47, 3, ': %d' % evasion)
        absorption = player.getKnowledge('creature', creature.name, 'absorption')
        if absorption is not None:
            artist.writeString(dc, 'ORANGE', 40, 4, 'Absorption')
            artist.writeString(dc, 'WHITE', 50, 4, ': %d' % absorption)

        rowOffset = 2 + max(1, len(creature.blows))
        
        # Draw spell information, if any.
        record = creature.completeRecord
        frequency = player.getKnowledge('creature', creature.name, 'magic', 'frequency')
        if frequency is not None:
            artist.writeString(dc, 'ORANGE', 0, rowOffset, 'Spells')
            frequency = "1 time in %d" % record['magic']['frequency']
            if creature.getStat('smart spellcaster'):
                frequency += ', intelligently'
            artist.writeString(dc, 'WHITE', 7, rowOffset, "(%s):" % frequency)
            rowOffset += 1
            spells = record['magic']['spells']
            maxSpellLen = max([len(s) for s in spells]) + 1
            columnOffset = 0
            for spell in spells:
                if not player.getKnowledge('creature', creature.name, 'magic', 
                        'spells', spell):
                    # Player hasn't seen this spell yet.
                    continue
                artist.writeString(dc, 'WHITE', columnOffset, rowOffset, 
                        spell.capitalize())
                columnOffset += maxSpellLen
                if columnOffset > numColumns - maxSpellLen:
                    columnOffset = 0
                    rowOffset += 1
        rowOffset += 1

        # Draw drop information.
        # \todo For now, just maximizing the drop roll and reporting that.
        # Eventually drop profiles will need to be able to describe themselves.
        artist.writeString(dc, 'ORANGE', 0, rowOffset, 'Drop')
        artist.writeString(dc, 'WHITE', 4, rowOffset, ':')
        numItems = sum([util.boostedDie.roll(d.numDrops, creature.nativeDepth, shouldMaximize = True)
                for d in creature.drops])
        artist.writeString(dc, 'WHITE', 6, rowOffset, "%d items" % numItems)
        rowOffset += 1

        # Draw miscellaneous flags.
        flags = []
        for flag in ['movees through walls', 'tunnels through walls', 
                'pushes past weaker creatures', 'destroys weaker creatures', 
                'regenerates', 'picks up items']:
            if creature.getStat(flag):
                flags.append(flag)
        if flags:
            artist.writeString(dc, 'ORANGE', 0, rowOffset, 'Other:')
            rowOffset += 1
            flags = ", ".join(flags)
            for line in util.grammar.splitIntoLines(flags, numColumns, ', '):
                artist.writeString(dc, 'WHITE', 0, rowOffset, line)
                rowOffset += 1

        # Draw description.
        for line in util.grammar.splitIntoLines(creature.description, numColumns - 1):
            artist.writeString(dc, 'SLATE', 0, rowOffset, line)
            rowOffset += 1

