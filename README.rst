======
PYREL!
======

Requirements
============

1. python 2.7 or greater
2. numpy (download from http://www.scipy.org)
3. Cython (download from http://www.cython.org)
4. A C compiler, to compile the _cmap.c module in the util directory. 
   For gcc, run this:

   gcc _cmap.c -o _cmap.so -fPIC -shared -O2 -std=c99 -Wall -Werror

5. Pyrel supports multiple graphical user interfaces (GUI).  Each GUI may
   have its own requirements, described in its respective subsection below.
   By default, the game starts with the wxWidgets GUI.  The GUI can be 
   specified at runtime with the --ui flag.  Valid values are:

* WX - wxWidgets_
* QT - `Qt Tool Kit`_
* CURSES - `text-based terminal`__

__ Curses_

Running the game
================

On Linux/Mac, to start pyrel, run::

    python pyrel.py

Or you may need to specify the version::

    python2.7 pyrel.py

On Windows, you need to specify the full path of your Python_ 
installation, e.g.::

    C:\Python27\python.exe pyrel.py

wxWidgets
=========

Requirements
------------

1. wxpython 2.9 or greater

The "Stable" wxPython available from http://wxpython.org is 32-bit only. 
If you have 64-bit Python_, then you should download the `"Cocoa" development
version`__ instead.  Note that this version is only available for Python_ 2.7. 

__ wxPythonCocoa_

Alternately, you can use the 32-bit wxpython by using the provided 
"python32" launcher script as follows::

    ./python32 pyrel.py

QT Tool Kit
===========

Requirements
------------

1. PyQt4 4.9 or greater

To start Pyrel in QT mode, run::

    python pyrel.py --ui=QT

Curses
======

Requirements
------------

1. An 80x35 character terminal with 256 color support

To start Pyrel in curses mode, run::

    python pyrel.py --ui=CURSES

Troubleshooting OSX
===================

Aside: as a general rule, developers on OSX are strongly recommended to install
their "own" Python_ instead of using and modifying the Python_ that comes 
installed with the OS. By using a custom Python_ install instead of the OS 
Python_, you avoid potentially confusing the OS. Perhaps more importantly, 
users cannot redistribute Apple's Python_, rendering it impossible to provide 
a standalone program for people who want to play Pyrel without having their 
own development environment set up.

.. _Python: http://www.python.org/
.. _wxPythonCocoa: http://downloads.sourceforge.net/wxpython/wxPython2.9-osx-2.9.4.0-cocoa-py2.7.dmg
