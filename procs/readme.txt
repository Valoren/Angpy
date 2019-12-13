Procs are bits of code that modify the game world or control the flow of 
execution. Perhaps more usefully, procs are where all of the little details
of the game exist ("What happens when I cast fireball?" "How do we keep unique
monsters from being generated after they've been killed?" "How does the AI
decide what to do on its turn?"). 

For more information on procs, please see 
https://bitbucket.org/derakon/pyrel/wiki/ProcsGuide

 * aiProc.py: handles creature AI (pathfinding, melee, and spellcasting)
 * calculatorProc.py: contains Procs that generate numbers
 * damageProc.py: handles dealing damage to entities, and the consequences
   and side-effects.
 * displayProc.py: Procs that show things to the user, thus straddling the
   UI and game logic layers.
 * filterProc.py: Procs that return a boolean, causing program flow to branch.
 * nameProc.py: Procs that generate names for things.
 * proc.py: the base Proc class is defined here. Additionally, a dict that 
   maps various strings to the Proc sub-classes is declared here; any new
   Procs must be added to that mapping (PROC_NAME_MAP) before they can be 
   referred to in the data files.
 * procData: this directory contains logic related to loading proc datafiles, 
   for example describing damage elements or spell effects.
 * procLoader.py: loads the data/proc_template.txt datafile.
 * procUtil.py: various utility functions that multiple other modules depend
   on.
 * spellProc.py: Procs that are specifically implementing the effects of 
   spells.
 * statusProc.py: Procs that handle the consequences of status ailments.
