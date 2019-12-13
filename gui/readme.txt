This directory contains all of the GUI (graphical user interface) code. We have
multiple front-ends for Pyrel, depending on how the player wants to interact
with the game (e.g. using a windowed game vs. playing in a terminal). 

The "base" directory contains common UI functionality that is 
fairly front-end-agnostic. It should support any top-down tile-based display. 
cursesPyrel, qtPyrel, and wxPyrel contain front-end implementations using
curses, Qt, and wxWidgets, respectively.

If you want to add a new front-end, then you'll need to modify the __init__.py
module here so that your front-end is loaded properly. Additionally, pyrel.py
will need to be updated so that you can specify your front-end as an option
when the game is run.

Otherwise, this directory contains:

 * colors.py: a utility module for loading color configuration data from
   data/colors.txt. Also contains functions for performing color mutations.
 * flavors.py: loads data/flavor_colors.txt and data/flavor_types.txt, for
   loading "flavor" information (e.g. Green Speckled Potions and Gold Wands), 
   and assigning it to objects.

