## Convert records in Angband's object.txt to the new JSON format.

import colors
import setColors

import collections
import json
import re

objectTypes = {
    0: "NULL",
    1: "SKELETON",
    2: "BOTTLE",
    3: "JUNK",
    5: "SPIKE",
    7: "CHEST",
    16: "SHOT",
    17: "ARROW",
    18: "BOLT",
    19: "BOW",
    20: "DIGGING",
    21: "HAFTED",
    22: "POLEARM",
    23: "SWORD",
    30: "BOOTS",
    31: "GLOVES",
    32: "HELM",
    33: "CROWN",
    34: "SHIELD",
    35: "CLOAK",
    36: "SOFT_ARMOR",
    37: "HARD_ARMOR",
    38: "DRAG_ARMOR",
    39: "LIGHT",
    40: "AMULET",
    45: "RING",
    55: "STAFF",
    65: "WAND",
    66: "ROD",
    70: "SCROLL",
    75: "POTION",
    77: "FLASK",
    80: "FOOD",
    90: "MAGIC_BOOK",
    91: "PRAYER_BOOK",
    100: "GOLD",
    101: "MAX",
}

def parseMod(input):
    result = {}
    flatBonus = numDice = dieSize = depthMod = 0
    if 'd' not in input and 'M' not in input:
        # Just a flat bonus
        flatBonus = int(input)
        input = ''
    elif '+' in input:
        flatBonus, input = input.split('+')
        flatBonus = int(flatBonus)
    if 'M' in input:
        input, depthMod = input.split('M')
        depthMod = int(depthMod)
    input = input.strip()
    if input:
        numDice, dieSize = input.split('d')
        if not numDice:
            numDice = 1
        if not dieSize:
            dieSize = 1
        numDice = int(numDice)
        dieSize = int(dieSize)
    if flatBonus:
        result['constantBonus'] = flatBonus
    if numDice:
        result['numDice'] = numDice
        result['dieSize'] = dieSize
    if depthMod:
        result['depthMod'] = depthMod
    return result
    

result = []
curRecord = collections.OrderedDict()
curAllocations = []
curPile = {}
curTval = None
curFlags = []
curPvals = []
lineNum = 0
for line in open('../edit/object.txt', 'r'):
    lineNum += 1
#    print lineNum
    line = line.strip()
    if line.startswith('N:') and curRecord:
        if curAllocations:
            if curPile:
                for allocation in curAllocations:
                    allocation['piling'] = curPile
            curRecord['allocations'] = curAllocations
        if curFlags:
            curRecord['flags'] = curFlags
        if curPvals:
            curRecord['mods'] = curPvals
        result.append(curRecord)
        curRecord = {}
        curAllocations = []
        curPile = {}
        curTval = None
        curFlags = []
        curPvals = []
    if not re.match('^\s*$', line) and not re.match('^\s*#', line):
        values = line.split(':')
        type = values[0]
        rest = values[1:]
        if type == 'N':
            curRecord['index'] = int(rest[0])
            curRecord['subtype'] = rest[1]
        elif type == 'G':
            color = setColors.colorMap[rest[1]]
            color = colors.__dict__[color]
            curRecord['display'] = {'ascii': {'symbol': rest[0], 'color': color}}
        elif type == 'I':
            curTval = int(rest[0])
            curRecord['type'] = objectTypes[curTval].lower()
        elif type == 'W':
            rest = map(int, rest)
            curRecord['complexity'] = rest[0]
            curRecord['weight'] = rest[2] * .1
            curRecord['cost'] = rest[3]
        elif type == 'P':
            armor = {}
            if 30 <= curTval <= 38 or rest[0] != '0':
                armor['baseArmor'] = int(rest[0])
            if rest[4] != '0':
                armor['armorBonus'] = rest[4]
            if armor:
                curRecord['armor'] = armor
            weapon = {}
            if 16 <= curTval <= 23 or rest[1] != '1d1':
                if 16 <= curTval <= 23 and curTval != 19:
                    numDice, dieSize = map(int, rest[1].split('d'))
                    weapon['numDice'] = numDice
                    weapon['dieSize'] = dieSize
                if len(rest) > 5:
                    weapon['balance'] = int(rest[5]) * .01
                    weapon['heft'] = int(rest[6]) * .01
            if rest[2] != '0':
                weapon['finesseBonus'] = rest[2]
            if rest[3] != '0':
                weapon['prowessBonus'] = rest[3]
            if weapon:
                curRecord['weapon'] = weapon
        elif type == 'A':
            commonness = int(rest[0])
            minDepth, maxDepth = map(int, rest[1].split(' to '))
            curAllocations.append(
                    {'commonness': commonness,
                        'minDepth': minDepth,
                        'maxDepth': maxDepth}
            )
        elif type == 'C':
            curRecord['charges'] = rest[0]
        elif type == 'M':
            curPile['chance'] = int(rest[0])
            curPile['pileSize'] = rest[1]
        elif type == 'E':
            curRecord['effect'] = rest[0]
            if len(rest) > 1:
                curRecord['rechargeTime'] = rest[1]
        elif type == 'F':
            curFlags.extend([s.strip() for s in rest[0].split('|')])
        elif type == 'L':
            pval = rest[0]
            flags = [s.strip() for s in rest[1].split('|')]
            curPvals.append({'bonus': pval, 'flags': flags})
        elif type == 'D':
            if 'description' not in curRecord:
                curRecord['description'] = ''
            curRecord['description'] += ':'.join(rest)

print json.dumps(result, indent = 2)
