## Convert records in v4's ego_item.txt to the new JSON format.

import collections
import json
import re

result = []
curRecord = collections.OrderedDict()
curAllocations = []
curFlags = []
curPvals = []
curStats = {}
curRandoms = []
lineNum = 0
for line in open('../../angband/lib/edit/ego_item.txt', 'r'):
    lineNum += 1
    line = line.strip()
    if line.startswith('N:') and curRecord:
        if curAllocations:
            curRecord['allocations'] = curAllocations
        if curStats:
            curRecord['stats'] = curStats
        if curFlags:
            curRecord['flags'] = curFlags
        if curPvals:
            curRecord['mods'] = curPvals
        if curRandoms:
            curRecord['randoms'] = curRandoms
        result.append(curRecord)
        curRecord = {}
        curAllocations = []
        curFlags = []
        curPvals = []
        curStats = {}
        curRandoms = []
    if not re.match('^\s*$', line) and not re.match('^\s*#', line):
        values = line.split(':')
        lineType = values[0]
        rest = values[1:]
        if lineType == 'N':
            curRecord['index'] = int(rest[0])
            curRecord['affixType'] = rest[1]
            curRecord['name']= rest[2]
        elif lineType == 'C':
            if rest[0] != '0':
                curStats['finesseBonus'] = rest[0]
            if rest[1] != '0':
                curStats['prowessBonus'] = rest[1]
            if rest[2] != '0':
                curStats['armorBonus'] = rest[2]
            if len(rest) > 3 and rest[3] != '0':
                curStats['baseArmorMod'] = rest[3] + '%'
            if len(rest) > 4 and rest[4] != '0':
                curStats['weightMod'] = rest[4] + '%'
            if len(rest) > 5 and rest[5] != '0':
                curStats['extraDice'] = rest[5]
            if len(rest) > 6 and rest[6] != '0':
                curStats['extraSides'] = rest[6]
            if len(rest) > 7 and rest[7] != '0':
                curStats['balanceMod'] = int(rest[7]) * .01
            if len(rest) > 8:
                curStats['heftMod'] = int(rest[8]) * .01
        elif lineType == 'M':
            if rest[0] != '255':
                curStats['minFinesseBonus'] = rest[0]
            if rest[1] != '255':
                curStats['minProwessBonus'] = rest[0]
            if rest[2] != '255':
                curStats['minArmorBonus'] = rest[0]
        elif lineType == 'T':
            itemType = rest[0]
            min_sval = int(rest[1])
            max_sval = int(rest[2])
            affixLevel = rest[3]
            commonness = int(rest[4])
            minDepth, maxDepth = map(int, rest[5].split(' to '))
            curAllocations.append(
                    {'itemType': itemType,
                     'affixLevel': affixLevel,
                     'commonness': commonness,
                        'minDepth': minDepth,
                        'maxDepth': maxDepth}
            )
            if min_sval != 0 or max_sval != 99:
                curAllocations[-1]['subtypes'] = [min_sval, max_sval]
        elif lineType == 'F':
            curFlags.extend([s.strip() for s in rest[0].split('|')])
        elif lineType == 'L':
            pval = rest[0]
            min_pval = rest[1]
            flags = [s.strip() for s in rest[2].split('|')]
            curPvals.append({'bonus': pval, 'minimum': min_pval, 'flags': flags})
        elif lineType == 'R':
            num = rest[0]
            flagtypes = [s.strip() for s in rest[1].split('|')]
            curRandoms.append({'number': num, 'flag types': flagtypes})
        elif lineType == 'R2':
            num = rest[0]
            flags = [s.strip() for s in rest[1].split('|')]
            curRandoms.append({'number': num, 'flags': flags})
        elif lineType == 'D':
            if 'description' not in curRecord:
                curRecord['description'] = ''
            curRecord['description'] += ':'.join(rest)

print json.dumps(result, indent = 2)
