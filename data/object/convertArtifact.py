## Convert records in Angband's object.txt to the new JSON format.

import collections
import json
import re


result = []
curRecord = collections.OrderedDict()
curAllocations = []
curFlags = []
curPvals = []
curStats = {}
curProcs = []
lineNum = 0
for line in open('../../../angband-github/lib/edit/artifact.txt', 'r'):
    lineNum += 1
    line = line.strip()
    if line.startswith('N:') and curRecord:
        if curAllocations:
            curRecord['allocatorRules'] = curAllocations
        if curFlags:
            curRecord['flags'] = curFlags
        if curPvals:
            curRecord['mods'] = curPvals
        if curProcs:
            curRecord['procs'] = curProcs
        if curStats:
            curRecord['stats'] = curStats
        result.append(curRecord)
        curRecord = {}
        curAllocations = []
        curStats = {}
        curProcs = []
        curFlags = []
        curPvals = []
    if not re.match('^\s*$', line) and not re.match('^\s*#', line):
        values = line.split(':')
        lineType = values[0]
        rest = values[1:]
        if lineType == 'N':
            curRecord['index'] = int(rest[0])
            curRecord['name'] = rest[1]
        elif lineType == 'I':
            curRecord['type'] = rest[0]
            curRecord['subtype'] = rest[1]
        elif lineType == 'W':
            curProcs.append({'complexity': int(rest[0])})
            curStats['weight'] = int(rest[2]) * .1
            if len(rest) > 4:
                curRecord['randomise'] = 'False'
        elif lineType == 'P':
            if rest[0] != '0':
                curStats['baseArmor'] = int(rest[0])
            if rest[4] != '0':
                curStats['armorBonus'] = int(rest[4])
            if rest[1] != '0d0':
                numDice, dieSize = map(int, rest[1].split('d'))
                curStats['numDice'] = numDice
                curStats['dieSize'] = dieSize
            if rest[2] != '0':
                curStats['finesseBonus'] = int(rest[2])
            if rest[3] != '0':
                curStats['prowessBonus'] = int(rest[3])
        elif lineType == 'A':
            commonness = int(rest[0])
            minDepth, maxDepth = map(int, rest[1].split(' to '))
            if maxDepth == 100 or maxDepth == 127:
                maxDepth = -1
            curAllocations.append(
                    {'commonness': commonness,
                        'minDepth': minDepth,
                        'maxDepth': maxDepth}
            )
        elif lineType == 'E':
            curProcs[0]['effect'] = rest[0]
            curProcs[0]['rechargeTime'] = rest[1]
        elif lineType == 'M':
            curProcs[0]['message'] = rest[0]
        elif lineType == 'F':
            curFlags.extend([s.strip() for s in rest[0].split('|')])
        elif lineType == 'L':
            pval = int(rest[0])
            flags = [s.strip() for s in rest[1].split('|')]
            curPvals.append({'bonus': pval, 'flags': flags})
        elif lineType == 'D':
            if 'description' not in curRecord:
                curRecord['description'] = ''
            curRecord['description'] += ':'.join(rest)
        elif lineType == 'affix' or lineType == 'theme':
            curRecord['namePrefix'] = rest[0]
         

print json.dumps(result, indent = 2)
