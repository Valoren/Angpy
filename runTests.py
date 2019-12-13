import os
import sys


# Run each module in the commandline arguments, in order. This is helpful
# for some test scripts that need to be run from the root level of the 
# program (e.g. to access Container or other constructs). 
for module in sys.argv[1:]:
    module = module.replace(os.path.sep, '.')
    __import__(module[:-3]) # Ignore the ".py" at the end.


