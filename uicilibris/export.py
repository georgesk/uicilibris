#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 	$Id:$	
#
# export.py is part of the package uicilibris
#
# uicilibris is based on wiki2beamer's code, which was authored by
# Michael Rentzsch and Kai Dietrich
#
# (c) 2007-2008 Michael Rentzsch (http://www.repc.de)
# (c) 2009-2010 Michael Rentzsch (http://www.repc.de)
#               Kai Dietrich (mail@cleeus.de)
# (c) 2011      Georges Khaznadar (georgesk@ofset.org)
#
# Create high-level parseable code from a wiki-like code, like LaTeX
#
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

"""
The module export aims to allow one to move uici libris books from
one mediawiki to another. It will be designed to take in account metadata
about authors and licenses.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Ui_export import Ui_exportDialog
import mediawiki

class Dialog(QDialog):
    """
    Dialog to manage parameter of an exportation
    """
    def __init__(self, parent):
        """
        the constructor
        @param parent the parent widget
        """
        QDialog.__init__(self, parent)
        self.ui=Ui_exportDialog()
        self.ui.setupUi(self)
        self.setValidState(-1)
        self.setLoggedState(-1)
        self.connect(self.ui.buttonBox, SIGNAL('accepted()'), self.doExport)
        self.connect(self.ui.checkButton, SIGNAL('clicked()'), self.doChecks)
        self.connect(self.ui.validButton, SIGNAL('clicked()'), self.explainValid)
        self.connect(self.ui.loggedButton, SIGNAL('clicked()'), self.explainLogged)

    def explainValid(self):
        """
        Shows a message about the mediawiki's validity
        """
        msg={-1: QApplication.translate("export", "No check of mediawiki has been performed yet", None, QApplication.UnicodeUTF8),
             0 : QApplication.translate("export", "The current mediawiki has been checked as INVALID", None, QApplication.UnicodeUTF8),
             1 : QApplication.translate("export", "The current mediawiki has been checked as VALID", None, QApplication.UnicodeUTF8)
             }
        title=QApplication.translate("export", "Mediawiki's validity", None, QApplication.UnicodeUTF8)
        reply=QMessageBox.information(self, title, msg[self.validState])

    def explainLogged(self):
        """
        Shows a message about the login state in the mediawiki
        """
        msg={-1: QApplication.translate("export", "No information about login available yet", None, QApplication.UnicodeUTF8),
             0 : QApplication.translate("export", "You are not logged in the mediawiki", None, QApplication.UnicodeUTF8),
             1 : QApplication.translate("export", "You are logged in the mediawiki", None, QApplication.UnicodeUTF8)
             }
        title=QApplication.translate("export", "Authentification state", None, QApplication.UnicodeUTF8)
        reply=QMessageBox.information(self, title, msg[self.logState])

    def doChecks(self):
        #text=self.parent().dropAreaText()
        #wikiLinks=mediawiki.linksInText(text)
        wikiUrl=u"%s" %self.ui.urlEdit.text()
        login=  u"%s" %self.ui.loginEdit.text()
        passwd= u"%s" %self.ui.passwdEdit.text()
        self.enableCheckGroup(False)
        if "try"=="try":
            mwo=mediawiki.MediawikiOpener(wikiUrl.encode("utf-8"),
                                          login, passwd)
            self.setValidState(mwo.isValid())
            self.setLoggedState(mwo.logged)
        ## except:
        ##     self.setValidState(0)
        ##     self.setLoggedState(-1)
        self.enableCheckGroup(True)

    def enableCheckGroup(self, state):
        """
        enables or disables the widget for the check
        @param state True of False
        """
        for widget in (self.ui.validButton, self.ui.loggedButton, self.ui.checkButton):
            widget.setEnabled(state)
            widget.repaint()
        
    def setLoggedState(self, state):
        """
        sets the information about login in the mediawiki
        @param state can be -1, 0 or 1 (undecided, False, True)
        """
        if state==True:
            state=1
        if state==False:
            state=0
        self.logState=state
        if state==0:
            self.ui.loggedButton.setIcon(QIcon("/usr/share/icons/Tango/scalable/emotes/face-plain.svg"))
            self.ui.loggedButton.setToolTip(QApplication.translate("export", "You are not logged", None, QApplication.UnicodeUTF8))
        elif state==1:
            self.ui.loggedButton.setIcon(QIcon("/usr/share/icons/Tango/scalable/emotes/face-glasses.svg"))            
            self.ui.loggedButton.setToolTip(QApplication.translate("export", "You are logged", None, QApplication.UnicodeUTF8))
        else:
            self.ui.loggedButton.setIcon(QIcon("/usr/share/icons/Tango/scalable/emotes/face-monkey.svg"))
            self.ui.loggedButton.setToolTip(QApplication.translate("export", "Authentification state undecided", None, QApplication.UnicodeUTF8))            

    def setValidState(self, state):
        """
        sets the information about the validity of the mediawiki
        @param state can be -1, 0 or 1 (undecided, false, true)
        """
        if state==True:
            state=1
        if state==False:
            state=0
        self.validState=state
        if state==0:
            self.ui.validButton.setIcon(QIcon("/usr/share/icons/Tango/scalable/status/weather-storm.svg"))
            self.ui.validButton.setToolTip(QApplication.translate("export", "The website is not a mediawiki", None, QApplication.UnicodeUTF8))            
        elif state==1:
            self.ui.validButton.setIcon(QIcon("/usr/share/icons/Tango/scalable/status/sunny.svg"))
            self.ui.validButton.setToolTip(QApplication.translate("export", "The website is a mediawiki", None, QApplication.UnicodeUTF8))            
        else:
            self.ui.validButton.setIcon(QIcon("/usr/share/icons/Tango/scalable/categories/applications-system.svg"))
            self.ui.validButton.setToolTip(QApplication.translate("export", "Validity state undecided", None, QApplication.UnicodeUTF8))            
        

    def doExport(self):
        self.parent().emit(SIGNAL("notYetImplemented"), "export to wiki")
