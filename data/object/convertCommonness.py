import json

filehandle = open('/home/chrisc/workspace/pyrel/data/object/artifact.txt', 'r')
try:
    records = json.load(filehandle)
except Exception, e:
    print "Data file %s is not valid JSON: %s" % (filePath, e)
    raise e
filehandle.close()

for record in records:
    if 'allocatorRules' in record:
        for rule in record['allocatorRules']:
            rule['commonness'] = float(rule['commonness'])
            rule['commonness'] /= 1500

print json.dumps(records, indent = 2)
