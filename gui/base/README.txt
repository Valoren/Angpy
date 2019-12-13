This directory contains the "base" GUI implementation that standard tile-based
UIs should inherit from. It's not complete, but provides a significant amount
of shared functionality that multiple different front-ends can benefit from.

 * animation.py: takes care of drawing animation effects (e.g. for 
   casting spells). 
 * commandHandler.py: handles communications between the game logic layer (in
   the commands directory) and the UI layer. 
 * artists: contains logic related to drawing the game state. Of course this
   base UI doesn't actually draw anything, but logic shared by multiple 
   drawing systems is consolidated here.
 * keymap.py: maps keyboard input to Command constants (see 
   commands/__init__.py)
 * prompt.py: contains the vast majority of in-game prompts (i.e. requests for
   input or information from the player, and corresponding displays, like 
   asking the player which potion to drink or which item to equip). 
