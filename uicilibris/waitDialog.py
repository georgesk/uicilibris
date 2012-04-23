# -*- coding: utf-8 -*-
# 	$Id: waitDialog.py 50 2011-08-15 15:00:29Z georgesk $
#
# waitDialog.py is part of the package uicilibris
#
# (c) 2011      Georges Khaznadar (georgesk@ofset.org)
#
#     This file is part of uicilibris.
# uicilibris is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# uicilibris is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with uicilibris.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class spinWheelWaitDialog(QDialog):
    """
    implements a QDialog to display a waiting wheel spinner during some event
    """
    def __init__(self, parent=None, cbStop=None, title=None, closeButtonMsg=""):
        """
        the constructor
        @param parent a parent widget
        @param cbStop a callback procedure to be called when the dialog is closed
        @param title a title for the dialog window
        @param closeButtonMsg a message to display on the button if the user is supposed to close the dialog explicitely upon completion. If this parameter is omitted, the dialog closes itself directly.
        """
        QDialog.__init__(self, parent)
        if title != None:
            self.setWindowTitle(title)
        self.closeButtonMsg=closeButtonMsg
        hLayout=QHBoxLayout()
        self.dial=QDial(self)
        self.dial.setMinimum(0)
        self.dial.setMaximum(100)
        hLayout.addWidget(self.dial)
        self.button=QPushButton("Cancel", self)
        self.connect(self.button, SIGNAL("clicked()"), self.close)
        if cbStop != None:
            self.connect(self, SIGNAL("spwDialogClosed"), cbStop)
        hLayout.addWidget(self.button)
        self.dialPos=0
        self.timer=dialTimer(self,self.dial)
        self.connect(self.timer, SIGNAL("timeout()"), self.animateLcDial)
        self.timer.start()
        self.setLayout(hLayout)

    def close(self):
        """
        redefinition of the default slot
        """
        self.emit(SIGNAL("spwDialogClosed"))
        QDialog.close(self)
        
    def animateLcDial(self):
        """
        moves the cursor of the QDial object
        """
        self.dialPos+=1
        if self.dialPos > 100:
            self.dialPos=0
        self.dial.setSliderPosition(self.dialPos)

    def stopAnimation(self):
        """
        Stops the animation and waits for a click on the close button
        """
        self.timer.stop()
        if self.closeButtonMsg:
            self.button.setText(self.closeButtonMsg)
        else:
            self.close()
        return

class dialTimer(QTimer):
    def __init__(self, parent, dial, interval=50):
        """
        creates a timer to animate a dial
        @param parent the widget owning the timer
        @param dial the QDial objet to animate
        @param interval the timespan between animations, defaults to 50 ms.
        """
        QTimer.__init__(self, parent)
        self.dial=dial
        self.setInterval(interval)        
        
