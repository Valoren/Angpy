## This module is responsible for loading all data that is specifically relied
# on by procs but not by the main engine.


def loadFiles():
    import element
    element.loadFiles()
    import spell
    spell.loadFiles()
    import status
    status.loadFiles()
