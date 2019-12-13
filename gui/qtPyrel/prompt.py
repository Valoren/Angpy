import gui.base.prompt
import mainApp

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt

## This Prompt lets the user select a tile or creature on the map, and stick
# it into the TARGETED container in the game map.
class TargetPrompt(gui.base.prompt.TargetPrompt):
    def doesKeySelectTarget(self, input):
        return input[0] in [Qt.Key_Enter, Qt.Key_Return]


    ## Draw a box around our current tile, and print a description of its
    # contents.
    def draw(self, qp, artist, gameMap):
        super(TargetPrompt, self).draw(qp, artist, gameMap)

        x, y, dx, dy = artist.getTileBox(self.targetTile)
        points = [(x, y), (x + dx, y), 
                  (x + dx, y), (x + dx, y + dy),
                  (x + dx, y + dy), (x, y + dy),
                  (x, y + dy), (x, y)]
        curPen = qp.pen()
        qp.setPen(QtGui.QPen(Qt.yellow, 1))
        qp.drawLines([QtCore.QPoint(*point) for point in points])
        qp.setPen(curPen)


