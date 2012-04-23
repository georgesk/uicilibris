#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 	$Id$
licence={}
licence['en']="""\
uicilibris version %s:

a program harvest a book from mediawiki contents

Copyright (C)2011 Georges Khaznadar <georgesk@ofset.org>

This program is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see
<http://www.gnu.org/licenses/>.
"""

licence['fr']=u"""\
uicilibris version %s:

un programme moisonner des livres à partir de contenus d'un mediawiki

Copyright (C) 2011 Georges Khaznadar <georgesk@ofset.org>

Ce projet est un logiciel libre : vous pouvez le redistribuer, le
modifier selon les terme de la GPL (GNU Public License) dans les
termes de la Free Software Foundation concernant la version 2 ou
plus de la dite licence.

Ce programme est fait avec l'espoir qu'il sera utile mais SANS
AUCUNE GARANTIE. Lisez la licence pour plus de détails.

<http://www.gnu.org/licenses/>.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Ui_uicilibris import Ui_MainWindow
from waitDialog import spinWheelWaitDialog
import version,wikiParser, w2book
import sys, re, StringIO, time, tempfile, subprocess, os.path

locale="C" # this global variable may be redefined later

class w2mMainWindow(QMainWindow):
    
    def __init__(self, parent, argv, locale="C"):
        """
        The constructor
        @param parent a parent window
        @param argv a list of arguments
        """
         ######QT
        QMainWindow.__init__(self)
        self.windowTitle="Wiki 2 Many"
        QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui_connections()
        self.locale=locale
        self.wikiIndex=None
        self.latexComp=None
        self.wb=None
        self.fragment=QString("")
        self.setPdfProductsEnabled(False)
        self.ui.searchCombo.addItem("")
        self.ui.searchCombo.addItem("Warning:")
        self.ui.searchCombo.addItem("Error:")
        return

    def autoOldStyle(self):
        """
        @return False as this class has nothing to do with wiki2beamer currently
        """
        return False
    
    def setPdfProductsEnabled(self, state):
        """
        enable/disable the buttons which depend from files output by pdflatex
        @param state: the new state of those elements
        """
        self.ui.viewPdfButton.setEnabled(state)
        self.ui.hackButton.setEnabled(state)
        self.ui.gotoLogButton.setEnabled(state)
        if not state:
            self.ui.logArea.clear()
        
    def ui_connections(self):
        """
        Connects signals with methods
        """
        self.connect(self.ui.action_Quit, SIGNAL('triggered()'), self.close)
        self.connect(self.ui.actionUser_manual, SIGNAL('triggered()'), self.displayManual)
        self.connect(self.ui.action_About, SIGNAL('triggered()'), self.about)
        self.connect(self.ui.text2latexButton, SIGNAL('clicked()'), self.toLatex)
        self.connect(self.ui.links2latexButton, SIGNAL('clicked()'), self.linksToLatex)
        self.connect(self.ui.baEditButton, SIGNAL('clicked()'), self.getWikiIndex)
        self.connect(self, SIGNAL("latexready"), self.feedIntoLatexArea)
        self.connect(self, SIGNAL("stopWaitLatex"), self.closeLatexWait)
        self.connect(self, SIGNAL("pdfready"), self.registerPdf)
        self.connect(self, SIGNAL("wikiAddress"), self.newWikiAddress)
        self.connect(self, SIGNAL("imgAddress"),  self.incCompileProgress)
        self.connect(self, SIGNAL("errMsg"),  self.displayErr)
        self.connect(self.ui.runPdflatexButton, SIGNAL('clicked()'), self.runPdfLatex)
        self.connect(self.ui.viewPdfButton, SIGNAL('clicked()'), self.viewPdfLatex)
        self.connect(self.ui.hackButton, SIGNAL('clicked()'), self.hack)
        self.connect(self.ui.gotoLogButton, SIGNAL('clicked()'), self.gotoLog)
        self.connect(self.ui.searchCombo, SIGNAL('editTextChanged(QString)'), self.search)
        self.connect(self.ui.searchNextButton, SIGNAL('clicked()'), self.searchNext)
        ### connect drop methods
        self.ui.wikiDropArea.__class__.dragEnterEvent = self.wa_dragEnterEvent
        self.ui.wikiDropArea.__class__.dropEvent = self.wa_dropEvent
        return

    #### wiki drop area methods

    def wa_dragEnterEvent(self, event):
        event.acceptProposedAction()
        return
    
    httpRegexp=re.compile(r"(http://.*/index.php)/[.-_\S:]+")
    
    def wa_dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasText():
            text=unicode(mimeData.text())
            m=w2mMainWindow.httpRegexp.match(text)
            if m:
                # get the web page's source
                text=wikiParser.getWikiContents(text)[1]
                self.ui.wikiDropArea.setPlainText(text)
                self.wikiIndex=m.group(1)
                self.ui.wikiIndex.setText(self.wikiIndex)
            else:
                self.ui.wikiDropArea.setPlainText(text)
        event.acceptProposedAction()
        return

    def closeEvent(self, event):
        """
        reimplements the close event: cleans up temporary dirs
        """
        if self.latexComp != None:
            del self.latexComp
        QMainWindow.closeEvent(self, event)

    def about(self):
        """
        displays the about dialog
        """
        global locale
        if locale[:2]=="fr":
            l="fr"
        else:
            l="en"
        msg=licence[l] %version.version
        QMessageBox.information(None, QApplication.translate("uicilibris", "À propos", None, QApplication.UnicodeUTF8), msg)
        return

    def displayManual(self):
        """
        displays the manual
        """
        cmd="(sensible-browser /usr/share/uicilibris/guide/index.html &)"
        subprocess.call(cmd, shell=True)
        return

    def search(self, fragment):
        """
        makes a search in the error tab
        @param fragment a QString to search
        """
        self.ui.logArea.moveCursor(QTextCursor.StartOfWord)
        self.fragment=fragment
        if self.fragment.length() > 0:
            self.ui.logArea.find(self.fragment)
        
    def searchNext(self):
        """
        search the next occurence of a fragment if it is defined
        """
        if self.fragment.length() > 0:
            self.ui.logArea.find(self.fragment)
        if self.fragment.length() > 4 and self.ui.searchCombo.findText(self.fragment) < 0:
            self.ui.searchCombo.addItem(self.fragment)

    def setImages(self, imageSet):
        """
        register the set of images to be used with one document
        @param imageSet a set of images filenames in unicode format
        """
        self.imageSet=imageSet
        return

    def toLatex(self):
        """
        turns the selected contents of the first tab into Latex code which is
        fed into the second tab. If nothing is selected previously, the whole
        contents are selected.
        """
        cursor=self.ui.wikiDropArea.textCursor()
        if not cursor.hasSelection():
            self.ui.wikiDropArea.selectAll()
            cursor=self.ui.wikiDropArea.textCursor()
        self.latexSource=unicode(cursor.selectedText())
        self.toLatexWait=spinWheelWaitDialog(self, self.stopToLatex, title="Expanding to LaTeX")
        self.toLatexWait.show()
        self.toLThread=toLatexThread(self)
        self.toLThread.start()

    def stopToLatex(self):
        """
        terminates the thread of LaTeX expansion if it is still running
        """
        if self.toLThread.isRunning():
            self.toLThread.terminate()

    def linksToLatex(self):
        """
        turns the selected contents of the first tab into Latex code which is
        fed into the second tab. The first tab is supposed to provide
        a series of links to wiki pages. If nothing is selected previously, the whole
        contents are selected.
        """
        cursor=self.ui.wikiDropArea.textCursor()
        if not cursor.hasSelection():
            self.ui.wikiDropArea.selectAll()
            cursor=self.ui.wikiDropArea.textCursor()
        self.inputText=unicode(cursor.selectedText())
        #initialize a wiki2book instance with the home page of the mediawiki
        if self.wikiIndex==None:
            self.getWikiIndex()
        self.homeUrl=self.wikiIndex.encode("utf-8")+"/fakePage"
        wikiAddresses=re.findall("\[\[([^\]]+)\]\]", self.inputText)
        self.currentWikiAddress=0 # number of addresses processed
        self.progressL2L=QProgressDialog("Connection to %s ..." %self.homeUrl, "Cancel", 0, len(wikiAddresses)+1, self)
        self.progressL2L.setWindowTitle("Links to LaTeX processing")
        self.progressL2L.show()
        self.connect(self.progressL2L, SIGNAL("canceled()"), self.killThreadLinksToLatex)
        self.threadLinksToLatex=l2lThread(self)
        self.threadLinksToLatex.start()

    def getWikiIndex(self):
        """
        inputs self.wikiIndex
        """
        wikiIndex, ok = QInputDialog.getText (self, u"Enter the base address of a mediawiki", u"Base address of a MediaWiki:")
        if ok:
            self.wikiIndex=unicode(wikiIndex)
            self.ui.wikiIndex.setText(wikiIndex)
        return


    def killThreadLinksToLatex(self):
        """
        stops the thread self.threadLinksToLatex
        """
        self.threadLinksToLatex.terminate()
        
    def newWikiAddress(self, a):
        """
        increments the progress bar in self.progressL2L
        and changes the text of the label
        @param a the wiki address just processed
        """
        self.currentWikiAddress+=1
        self.progressL2L.setValue(self.currentWikiAddress)
        self.progressL2L.setLabelText(u"processing '%s' ..." %a)

    def displayErr(self, msg):
        """
        appends a lin in the Error area
        @param msg an error message
        """
        self.ui.errorArea.append(msg)

    def feedIntoLatexArea(self, text, multi=None):
        """
        sets the contents of the latex area
        @param text the contents, which must be in unicode format
        @param multi must be True when a progressbar is used.
        """
        if multi != None:
            self.currentWikiAddress+=1
            self.progressL2L.setValue(self.currentWikiAddress)
            self.progressL2L.setLabelText(u"Finishing translation ...")
        self.ui.latexCodeArea.setPlainText(text)
        self.ui.tabWidget.setCurrentIndex(1)
        
    def closeLatexWait(self):
        """
        closes the wait spin dialog
        """
        self.toLatexWait.close()
            
            
    def registerPdf(self, lc):
        """
        registers a recently compiles PDF file and displays log data
        in the log panel. Closes eventual progress monitors
        @param lc a latexComp object
        """
        self.latexComp=lc
        if os.path.exists(self.latexComp.pdfFileName):
            self.setPdfProductsEnabled(True)
        else:
            self.ui.hackButton.setEnabled(True)
            QMessageBox.warning (self, u"Pdflatex failed", u"For some reason, Pdflatex failed.<b />Try to hack around." )
        logInput=open(self.latexComp.logFileName,"r")
        try:
            log=logInput.read().decode("utf-8")
        except:
            logInput.seek(0)
            log=logInput.read().decode("ISO-8859-1")
            pass
        logInput.close
        self.ui.logArea.setPlainText(log)
        self.compileProgress.close()
        
    def runPdfLatex(self):
        """
        runs PdfLatex with the contents available in self.ui.latexCodeArea
        """
        if self.latexComp != None:
            del (self.latexComp)
            self.latexComp=None
        self.setPdfProductsEnabled(False)
        self.currentImage=0
        self.compileProgress=QProgressDialog("Getting images ...", "Cancel", 0, self.wb.imageCount()+1, self)
        self.compileProgress.setWindowTitle("LaTeX compilation")
        self.compileProgress.show()
        self.connect(self.compileProgress, SIGNAL("canceled()"), self.stopPdfLatex)
        self.latexSource=unicode(self.ui.latexCodeArea.toPlainText())
        self.lcThread=latexCompileThread(self)
        self.lcThread.start()

    def incCompileProgress(self, info):
        """
        deals with a text information to deliver to self.compileProgress
        """
        self.currentImage+=1
        self.compileProgress.setValue(self.currentImage)
        self.compileProgress.setLabelText(u"getting '%s' ..." %info)
        return

    def stopPdfLatex(self):
        """
        terminates the thread of Latex compilation if it is still running
        """
        if self.lcThread.isRunning():
            self.lcThread.terminate()

    def viewPdfLatex(self):
        """
        launches a subprocess to view the PDF file if any
        """
        if self.latexComp and os.path.exists(self.latexComp.pdfFileName):
            cmd="(evince %s &)" %self.latexComp.pdfFileName
            subprocess.call(cmd, shell=True)
        else:
            QMessageBox.warning(self, "Cannot open PDF file", "There is no reachable PDF file. Compile the LaTeX source, or check the error tab.")

    def hack(self):
        """
        launches gnome-terminal and opens a shell in self.tmpDir
        """
        if self.latexComp!=None:
            tmpdir=self.latexComp.tmpdir
            cmd="(cd %s; gnome-terminal --title='%s' &)" %(tmpdir, "Uici Libris Terminal (%s)" %tmpdir)
            subprocess.call(cmd, shell=True)
        else:
            QMessageBox.warning(self, "Cannot find the temporary files", "There is no temporary files. Plese run Pdflatex.")
        return

    def gotoLog(self):
        """
        raises the log panel
        """
        self.ui.tabWidget.setCurrentIndex(2)
        return
       
        

class latexComp(QObject):
    """
    implements a process to compile LaTeX files and take in account
    the log file produced
    """
    def __init__(self, uici, parent=None, cbInfo=None):
        """
        the constructor
        @param uici uici.wb must be a w2book instance
        @param parent a parent for the QObject structure
        @param cbInfo a callback function to deal with information
        """
        QObject.__init__(self, parent)
        self.tmpdir=tempfile.mkdtemp(prefix="uici_")
        self.texFilename= os.path.join(self.tmpdir,"out.tex")
        self.pdfFileName= os.path.join(self.tmpdir,"out.pdf")
        self.auxFileName= os.path.join(self.tmpdir,"out.aux")
        self.logFileName= os.path.join(self.tmpdir,"out.log")
        uici.wb.toFile(self.texFilename, cbInfo)

    def __del__(self):
        """
        the destructor takes care of the temporary directory
        """
        import subprocess
        cmd="rm -rf %s" %self.tmpdir
        subprocess.call(cmd, shell=True)

    def compile(self):
        """
        launches the compilation of the source file
        """
        cmd="cd %s; pdflatex -interaction=nonstopmode out.tex" %self.tmpdir
        compileAgain=True
        while compileAgain:
            pipe=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.logOutput=pipe.communicate()
            compileAgain = len(self.labelWarning())>0

    def labelWarning(self):
        """
        @return the warning when cross-references are not fine
        """
        return re.findall(r"LaTeX Warning: Label\(s\) may have changed. Rerun to get cross-references right.", self.logOutput[0])

class l2lThread(QThread):
    """
    a class to run linksToLatex on the behalf of a main window
    it will accept an url and a text for its initialization,
    and will return a processed text upon thread's termination.
    """
    def run(self):
        """
        turns the contents of the parent's first tab into Latex code which is
        fed into the second tab. The first tab is supposed to provide
        a series of links to wiki pages
        """
        wb=w2book.wiki2([self.parent().homeUrl], parent=self.parent(), report=self.reportErr) # the fake homeUrl is there only to get the address of the wiki; as a side-effect, the cache will be loaded with fake data.
        wb.reloadCacheIndirect(self.parent().inputText, cbInfo=self.cbInfo)
        texSource=("%s" %wb).decode("utf-8")
        self.parent().emit(SIGNAL("latexready"), texSource, True)

    def cbInfo(self, info):
        """
        a callback function to display progress information
        """
        self.parent().emit(SIGNAL("wikiAddress"), info)

    def reportErr(self, msg):
        """
        a call back function to send message to the error tab in the main window
        """
        self.parent().emit(SIGNAL("errMsg"), msg)

class toLatexThread(QThread):
    """
    a class to expand wiki code to Latex source
    """
    def run(self):
        #initialize a wiki2book instance with the home page of the mediawiki
        homeUrl=self.parent().wikiIndex.encode("utf-8")+"/fakePage"
        wb=w2book.wiki2book([homeUrl], isUrl=True, report=False) # the fake homeUrl is there only to get the address of the wiki; as a side-effect, the cache will be loaded with fake data.
        wb.reloadCache(self.parent().latexSource)
        latexSource=("%s" %wb).decode("utf-8")
        # register the wiki2book structure
        self.parent().wb=wb
        self.parent().emit(SIGNAL("latexready"), latexSource)
        self.parent().emit(SIGNAL("stopWaitLatex"))
        
class latexCompileThread(QThread):
    """
    a class to compile a Latex source into a temporary directory
    when the thread terminates, it sends back an object with the
    necessary pointers to the compiled stuff
    """
    def run(self):
        """
        creates an object which owns a temporary directory,
        launches a compilation of Latex sources inside it,
        and returns this object upon completion
        """
        lc=latexComp(self.parent(), cbInfo=self.cbInfo)
        try:
            lc.compile()
        finally: #ensures that the signal is emitted even if the compilation fails inexpectedly
            self.parent().emit(SIGNAL("pdfready"), lc)

    def cbInfo(self, info):
        """
        a callback function to display progress information
        """
        self.parent().emit(SIGNAL("imgAddress"), info)

        
class latexViewThread(QThread):
    """
    a class to view a PDF file inside a thread
    """
    def __init__(self, parent, pdfFileName):
        QThread.__init__(parent)
        self.pdfFileName=pdfFileName
        
    def run(self):
        import subprocess
        cmd="evince %s" %self.pdfFileName
        subprocess.call(cmd, shell=True)
        self._exec()       
            
def run(argv):
    global locale
    app = QApplication(sys.argv)

    ###translation##
    locale = QLocale.system().name()
    qtTranslator = QTranslator()

    if qtTranslator.load("qt_" + locale):
        app.installTranslator(qtTranslator)
        
    appTranslator = QTranslator()
    if appTranslator.load("/usr/share/uicilibris/lang/uicilibris_" + locale):
        app.installTranslator(appTranslator)
    
    w = w2mMainWindow(None,argv,locale=locale)
    w.show()
    sys.exit(app.exec_())
    

if __name__=='__main__':
    run(sys.argv)
