import json

filehandle = open('/home/chrisc/workspace/pyrel/data/creature.txt', 'r')
try:
    records = json.load(filehandle)
except Exception, e:
    print "Data file %s is not valid JSON: %s" % (filePath, e)
    raise e
filehandle.close()

for record in records:
    if 'flags' in record:
        template = 'normal'
        itemType = {}
        drops = []
        if 'DROP_GOOD' in record['flags']:
            record['flags'].remove('DROP_GOOD')
            template = 'good'
        if 'DROP_GREAT' in record['flags']:
            record['flags'].remove('DROP_GREAT')
            template = 'great'
        if 'ONLY_ITEM' in record['flags']:
            record['flags'].remove('ONLY_ITEM')
            itemType = { 'money': 'none' }
        if 'ONLY_GOLD' in record['flags']:
            record['flags'].remove('ONLY_GOLD')
            itemType = { 'money': 'all' }
        if 'DROP_20' in record['flags']:
            record['flags'].remove('DROP_20')
            if itemType:
                drops = [{'template': template, 'number': 1,
                    'chance': 20, 'rules': { 'itemType': itemType }}]
            else:
                drops = [{'template': template, 'number': 1,
                    'chance': 20}]
        if 'DROP_40' in record['flags']:
            record['flags'].remove('DROP_40')
            if itemType:
                drops.extend([{'template': template, 'number': 1,
                    'chance': 40, 'rules': { 'itemType': itemType }}])
            else:
                drops.extend([{'template': template, 'number': 1,
                    'chance': 40}])
        if 'DROP_60' in record['flags']:
            record['flags'].remove('DROP_60')
            if itemType:
                drops.extend([{'template': template, 'number': 1,
                    'chance': 60, 'rules': { 'itemType': itemType }}])
            else:
                drops.extend([{'template': template, 'number': 1,
                    'chance': 60}])
        if 'DROP_1' in record['flags']:
            record['flags'].remove('DROP_1')
            if itemType:
                drops.extend([{'template': template, 'number': 1,
                    'rules': { 'itemType': itemType }}])
            else:
                drops.extend([{'template': template, 'number': 1}])
        if 'DROP_2' in record['flags']:
            record['flags'].remove('DROP_2')
            if itemType:
                drops.extend([{'template': template, 'number': 'd3',
                    'rules': { 'itemType': itemType }}])
            else:
                drops.extend([{'template': template, 'number': 'd3'}])
        if 'DROP_3' in record['flags']:
            record['flags'].remove('DROP_3')
            if itemType:
                drops.extend([{'template': template, 'number': '1+d3',
                    'rules': { 'itemType': itemType }}])
            else:
                drops.extend([{'template': template, 'number': '1+d3'}])
        if 'DROP_4' in record['flags']:
            record['flags'].remove('DROP_4')
            if itemType:
                drops.extend([{'template': template, 'number': '1+d5',
                    'rules': { 'itemType': itemType }}])
            else:
                drops.extend([{'template': template, 'number': '1+d5'}])

        if drops:
            record['drops'] = drops


print json.dumps(records, indent = 2)
