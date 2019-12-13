The data directory is where all in-game entities are described. Creatures, 
items (and their powers), terrain, etc. are all defined here. 

The datafile format is JSON, so you can load it with any JSON loader (python
includes a json module). 


colors.txt: Defines common color names that are used in other files.
creature.txt: Creature definitions -- names, stats, descriptions, etc.
creature_template.txt: Creature templates, so that creatures that share 
    characteristics can have more concise definitions in creature.txt.
element.txt: Describes various elemental damage types.
flavor_colors.txt: Provides names and associated colors for "flavored" item
    types (like potions, rings, and wands).
flavor_types.txt: Describes which groupings of flavors given item types use
    (e.g. staves select from the "wood" flavors, while wands select from the 
    "metal" flavors).
object: This directory contains all files associated with items.
proc_template.txt: Provides templates for procs so that multiple entities in 
    other files can refer to the same proc (or very similar procs) without 
    having lots of duplication.
terrain.txt: Defines terrain objects (walls, doors, stairs, traps, etc.). 


