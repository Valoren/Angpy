This directory contains code for processing commands from the player. 
Commands are "symbolic" (i.e. they represent actions, not raw input). The base
Command class is in __init__.py; other modules contain subclasses. __init__.py
also contains a mapping of constants to Command subclasses (the dict
inputToCommandMap). If you want to add a new command, then it will need to be
inserted into that mapping, and a new constant created for it, before it can
be used. 
