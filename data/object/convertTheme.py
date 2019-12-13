## Convert records in v4's ego_themes.txt to the new JSON format.

import collections
import json
import re

result = []
curRecord = collections.OrderedDict()
curAllocations = []
curAffixes = []
lineNum = 0
for line in open('../../angband-github/lib/edit/ego_themes.txt', 'r'):
    lineNum += 1
    line = line.strip()
    if line.startswith('N:') and curRecord:
        if curAllocations:
            curRecord['allocations'] = curAllocations
        if curAffixes:
            curRecord['affixes'] = curAffixes
        result.append(curRecord)
        curRecord = {}
        curAllocations = []
        curAffixes = []
    if not re.match('^\s*$', line) and not re.match('^\s*#', line):
        values = line.split(':')
        lineType = values[0]
        rest = values[1:]
        if lineType == 'N':
            curRecord['index'] = int(rest[0])
            curRecord['position'] = rest[1]
            curRecord['name']= rest[2]
        elif lineType == 'T':
            itemType = rest[0]
            min_sval = int(rest[1])
            max_sval = int(rest[2])
            minDepth, maxDepth = map(int, rest[3].split(' to '))
            if min_sval != 0 or max_sval != 99:
                itemTypeDict = { itemType: [min_sval, max_sval] }
            else:
                itemTypeDict = { itemType: ["all"] }
            curAllocations.append(
                       {'itemType': itemTypeDict,
                        'minDepth': minDepth,
                        'maxDepth': maxDepth}
            )
        elif lineType == 'A':
            name = rest[0]
            weighting = int(rest[1])
            if len(rest) > 2:
                chance = int(rest[2])
            else:
                chance = 100
            curAffixes.append({'name': name, 'weighting': weighting, 'chance': chance})
        elif lineType == 'D':
            if 'description' not in curRecord:
                curRecord['description'] = ''
            curRecord['description'] += ':'.join(rest)

print json.dumps(result, indent = 2)
