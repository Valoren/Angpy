## Load proc template records from data/proc_template.txt, and make them 
# available to the rest of the program. This works a bit differently from 
# most other loaders -- it's assumed that basically all procs will be either
# entirely defined inline in a data file, or just be based off of a single 
# template, so we don't have the whole FooFactory setup here; just the
# templates, which can be use to create an incomplete Proc, which is then
# filled in by any further details the client has. 

import proc
import util.record

import copy
import json
import os


## Maps proc template names to records for those templates.
TEMPLATE_NAME_MAP = {}


## Construct a proc.
# \param record A dictionary (generally loaded from a data file) describing
#        a proc. May be incomplete, in which case we look up the "name" field
#        for a template to fill in missing details.
# \param level Numerical value indicating the general "power" of the proc, 
#        as appropriate to context. Optional; defaults to None.
# \param trigger Trigger condition for the proc. Optional; defaults to None, in
#        which case the proc's own trigger condition (if any) is used.
def generateProcFromRecord(record, level = None, trigger = None):
    # First, check for a name indicating a template to be based on.
    name = None
    if type(record) in [str, unicode]:
        # Assume we just use the templated proc directly.
        name = record
    elif 'name' in record:
        name = record['name']
    if name in TEMPLATE_NAME_MAP:
        # Apply our template to the record. First, make a copy of the
        # template to modify.
        fullRecord = copy.deepcopy(TEMPLATE_NAME_MAP[name])
        if type(record) is dict:
            # Apply the rest of the records to the template.
            util.record.applyValues(record, fullRecord)
        record = fullRecord
    if 'code' not in record:
        # Assume the proc record's name refers to the code we want to call.
        record['code'] = name
    if 'triggerCondition' not in record or trigger is not None:
        # Use the optional trigger parameter instead.
        record['triggerCondition'] = trigger
    # We now have a dictionary representing the proc, so make a Proc from it.
    if record['code'] not in proc.PROC_NAME_MAP:
        raise RuntimeError("Unimplemented proc code string [%s]" % record['code'])
    # Note that we leave a bunch of extra stuff in the "params" parameter, 
    # including the proc's name and trigger condition, but this doesn't seem
    # likely to be harmful.
    return proc.PROC_NAME_MAP[record['code']](record['triggerCondition'], 
            params = record, procLevel = level)


## Directly request a proc with the given tuple or name
def getProc(key, triggerCondition, params, procLevel):
    if key not in proc.PROC_NAME_MAP:
        raise RuntimeError("Invalid proc name: [%s]" % key)
    return proc.PROC_NAME_MAP[key](triggerCondition, params, procLevel)


## Load our data file(s):
def loadFiles():
    templates = json.load(open(os.path.join('data', 'proc_template.txt'))) 

    for template in templates:
        TEMPLATE_NAME_MAP[template['name']] = template



