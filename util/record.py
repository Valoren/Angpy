## Various utility functions for interacting with data records.

import collections
import json
import re
import sys
import traceback

## Load the contents of the provided file path and generate a set of 
# class instances of the specified type; return a list of created instances.
# All extra parameters are passed to the constructor of the class alongside
# the loaded record.
def loadRecords(filePath, classType, *args, **kwargs):
    filehandle = open(filePath, 'r')
    try:
        records = json.load(filehandle)
    except Exception, e:
        print "Data file %s is not valid JSON: %s" % (filePath, e)
        raise e
    filehandle.close()
    result = []
    for i, record in enumerate(records):
        try:
            yield classType(record, *args, **kwargs)
        except Exception, e:
            # Figure out roughly where in the file we were when we failed. 
            # Tricky, since we loaded the entire file correctly, but one of 
            # the records in it was faulty in a JSON-compatible way.
            # For now, assuming that any line that begins with a '{' is a 
            # new record.
            filehandle = open(filePath, 'r')
            lineNum = 0
            curIndex = 0
            didFindRecord = False
            for j, line in enumerate(filehandle):
                lineNum += 1
                if line[0] == '{':
                    curIndex += 1
                    if curIndex == i:
                        print "Failed to load record %d starting on line %d from data file %s:" % (i, lineNum, filePath)
                        didFindRecord = True
                        break
            if not didFindRecord:
                print "Failed to load record %d from data file %s:" % (i, filePath)
            traceback.print_exc()
            sys.exit()


## Copy values from one dict to another -- generally used to apply a template
# to a record.
# \param shouldOverwrite True to replace lists; False to append to them
#        instead (scalars are always replaced; dicts are always merged). 
#        Defaults to False. When not in overwrite
#        mode and we encounter a key in both dicts that points to a list or
#        dict, we merge the two together. For example, if sourceDict is 
#        {'foo': [1, 2]} and targetDict is {'foo': [3, 4]}, then targetDict
#        will be modified to {'foo': [1, 2, 3, 4]}. 
# \param overwriteKeys A list or set of dict keys that cause us to set
#        shouldOverwrite when they are encountered. If the key points to a dict
#        then every list in that dict will be overwritten by lists in the 
#        source dict.
# \param ignoreKeys - Keys that should be ignored when copying from one
#        dict to the other, eg: for fields that aren't relevant except when
#        present on the final child object.
def applyValues(sourceDict, targetDict, shouldOverwrite = False, 
        overwriteKeys = {}, ignoreKeys = []):
    for key, value in sourceDict.iteritems():
        if key in ignoreKeys:
            continue
        amInOverwriteMode = shouldOverwrite or (key in overwriteKeys)
        if type(value) == list:
            if amInOverwriteMode:
                targetDict[key] = sourceDict[key]
                continue
            if key in targetDict and type(targetDict[key]) is not list:
                # Create a new list in the target containing the single 
                # element already there.
                targetDict[key] = [targetDict[key]]
            # Ensure the list exists.
            if key not in targetDict or targetDict[key] is None:
                targetDict[key] = []
            # Merge the two lists together.
            targetDict[key].extend(value)
        elif type(value) == dict:
            # Update the dict, recursively.
            if key not in targetDict or targetDict[key] is None:
                targetDict[key] = dict()
            applyValues(value, targetDict[key], amInOverwriteMode, 
                    overwriteKeys)
        else:
            # Replace the value, if it's there.
            targetDict[key] = value



## Build a complete record, inheriting from ancestor templates.
# \param myRecord - The record of the base object being built.
# \param templateLoader - Function used to request a new template.
def buildRecord(baseObject, templateLoader):
    # Inherit values from our templates first, so they can be overridden
    # by our own attributes as needed.
    # Always overwrite color because it has no meaning when lists are combined.
    # Always ignore template names for any except our own record.
    completeRecord = {}
    if 'templates' in baseObject.record and callable(templateLoader):
        templates = getRecordTemplates(baseObject, templateLoader)
        for template in map(templateLoader, templates):
            applyValues(template.record, completeRecord, overwriteKeys = ['color'], ignoreKeys = ['templateName'])
    applyValues(baseObject.record, completeRecord, overwriteKeys = ['color'])
    return completeRecord


## Copy values from a record to the target object.
#  This should be called from within the target's __init__ function.
# \param target - The target object that we're setting values for.
# \param record - The data record to apply to the object
def applyRecord(target, record):
    if not target:
        raise RuntimeError("No target to save record to.")
    if not record:
        return
    for key, value in record.iteritems():
        # If we have fields defined as sets, update those sets rather
        # than replacing them with lists.  JSON doesn't have sets.
        targetField = getattr(target, key, None)
        if isinstance(targetField, set) and isinstance(value, list):
            targetField.update(value)
        else:
            setattr(target, key, value)


## Recursively get all templates for a given item record.
#  Allows templates to be based on other templates.
def getRecordTemplates(objWithRecord, templateLoader):
    allTemplates = []

    # If no top object passed in, we're at the end of the recursion
    if not objWithRecord:
        return allTemplates

    # If the object doesn't have a record field, we can't work
    # with it, so consider it the end of the recursion
    if not hasattr(objWithRecord, 'record'):
        return allTemplates

    # If the object doesn't have any 'templates' in its record,
    # that means we're as far into the template ancestry as we
    # can go; return all the templates we've accumulated.
    if 'templates' not in objWithRecord.record:
        return allTemplates

    curTemplates = objWithRecord.record['templates']
    # Make sure we're using a list
    if not isinstance(curTemplates, list):
        curTemplates = [curTemplates]

    # Append recursively so that we get the deepest ancestor
    # added at the front of the list.
    # Check to make sure we don't duplicate templates, as we
    # can end up having data we want from a later template
    # overwritten by a repeat of an earlier one.
    for template in map(templateLoader, curTemplates):
        if template.templateName not in allTemplates:
            ancestors = getRecordTemplates(template, templateLoader)
            for ancestor in ancestors:
                if ancestor not in allTemplates:
                    allTemplates.append(ancestor)
            allTemplates.append(template.templateName)

    return allTemplates


## Wrapper around serializeDict that puts keys in a specific order as provided
# in fieldOrder. Any keys in record not in fieldOrder will be appended in 
# arbitrary order at the end.
def serializeRecord(record, fieldOrder):
    orderedValues = collections.OrderedDict()
    usedKeys = set()
    for key in fieldOrder:
        if key is not None and key in record:
            orderedValues[key] = record[key]
            usedKeys.add(key)
    # Handle keys not in fieldOrder.
    for key, value in record.iteritems():
        if key is not None and key not in usedKeys:
            orderedValues[key] = value
    return serializeDict(orderedValues, fieldOrder)


## Return a string representing the JSON serialization of the provided 
# OrderedDict according to the provided field ordering. This allows us 
# to combine multiple entries on the same row for visual compactness, without
# sacrificing legibility by stuffing *everything* onto the same row.
def serializeDict(orderedValues, ordering):
    result = '{'
    # We omit items that don't have any meaningful data (e.g. weapon 
    # data for a non-weapon), so we need to track if we actually want
    # to print a newline when we encounter None in FIELD_ORDER
    haveMeaningfulRow = False
    for key in ordering:
        if key is None:
            if haveMeaningfulRow:
                result += "\n  "
                haveMeaningfulRow = False
        elif (key in orderedValues and 
                (orderedValues[key] or type(orderedValues[key]) is int)):
            result += '"%s": %s, ' % (key, json.dumps(orderedValues[key]))
            haveMeaningfulRow = True
    # All as-yet unused entries get appended onto the end, one per line.
    usedKeys = set(ordering)
    for key in orderedValues:
        if key is not None and key not in usedKeys:
            result += '  "%s": %s, \n' % (key, json.dumps(orderedValues[key]))
    # Remove the last comma (which would cause a parse error) and newline.
    match = re.search(',\s*$', result)
    if match is not None:
        result = result[:-len(match.group())]
    result += "}"
    return result


## Write out the provided list of records to a file at the given path.
# The records should be sortable and each must implement getSerialization().
def serializeRecords(path, records):
    records.sort()
    records = [e.getSerialization() for e in records]

    filehandle = open(path, 'w')
    filehandle.write('[\n')
    for record in records:
        # Can't have a comma after the last record.
        comma = ",\n\n"
        if record is records[-1]:
            comma = ''
        filehandle.write(record + comma)
    filehandle.write(']\n')
    filehandle.close()


