## Convert v4's list-object-flags.h to the JSON format.

import collections
import json
import re

result = []
curRecord = collections.OrderedDict()
curSlotPower = {}
lineNum = 0
for line in open('data/object_flags.txt', 'r'):
    lineNum += 1
    line = line.strip()
    if curRecord:
        if curSlotPower:
            curRecord['slotPower'] = curSlotPower
        result.append(curRecord)
        curRecord = {}
        curSlotPower = {}
    if not re.match('^\s*$', line) and not re.match('^\s*#', line):
        values = line.split(',')
        curRecord['label'] = values[0]
        if 'OFID_WIELD' in values[3]:
            curRecord['ID'] = "wield"
        if 'OFID_NORMAL' in values[3]:
            curRecord['ID'] = "normal"
        if 'OFID_TIMED' in values[3]:
            curRecord['ID'] = "timed"
        if 'OFID_NONE' in values[3]:
            curRecord['ID'] = "never"
        curRecord['flagType'] = values[4]
        if int(values[5]) != 0:
            curRecord['basePower'] = int(values[5])
        if int(values[6]) != 0:
            curRecord['powerMult'] = int(values[6])
        if int(values[7]) != 0:
            curSlotPower['weapon'] = int(values[7])
        if int(values[8]) != 0:
            curSlotPower['launcher'] = int(values[8])
        if int(values[9]) != 0:
            curSlotPower['finger'] = int(values[9])
        if int(values[10]) != 0:
            curSlotPower['neck'] = int(values[10])
        if int(values[11]) != 0:
            curSlotPower['light source'] = int(values[11])
        if int(values[12]) != 0:
            curSlotPower['body'] = int(values[12])
        if int(values[13]) != 0:
            curSlotPower['back'] = int(values[13])
        if int(values[14]) != 0:
            curSlotPower['shield'] = int(values[14])
        if int(values[15]) != 0:
            curSlotPower['head'] = int(values[15])
        if int(values[16]) != 0:
            curSlotPower['hands'] = int(values[16])
        if int(values[17]) != 0:
            curSlotPower['feet'] = int(values[17])
        curRecord['name'] = values[19]
        curRecord['ID message'] = values[20]


print json.dumps(result, indent = 2)
