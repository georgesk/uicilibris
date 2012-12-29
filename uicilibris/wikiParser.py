#!/usr/bin/env python
# 	$Id: wikiParser.py 45 2011-08-14 17:22:26Z georgesk $	
#
# wikiParser.py is part of the package uicilibris
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


import sys, url, StringIO, re, os, urllib2
from regularExpressions import *
from BeautifulSoup import BeautifulSoup
from plugin.plugin import plugins
from templateParser import imageParser
import mediawiki
from PyQt4.QtCore import SIGNAL

wParser=None # global variable: the last and only wikiParser object
             # this global is used by some plugins.

def getWikiContents(completeUrl):
    """
    @param completeUrl the url of a wiki page, encoded in utf-8
    @return the base URL of the wiki and the wiki code for the page, else two void strings
    """
    result=("","")
    baseUrl=re.match(r"^(http://[^/]+/).*",completeUrl).group(1)
    try:
        sPage=url.urlopen(completeUrl)
    except urllib2.HTTPError:
        return result
    if sPage:
        soup=BeautifulSoup(sPage.read())
        pattern=re.compile('/(.*)/index.php\?title=.*action=edit$')
        editAddress=soup.find(href=pattern)
        if editAddress != None:
            localUrl=editAddress.attrMap["href"]
            base=pattern.match(localUrl).group(1)
            completeUrl=baseUrl+localUrl
        else:
            return result
    else:
        return result
    bPage=url.urlopen(completeUrl)
    if bPage:
        soup=BeautifulSoup(bPage.read())
        area=soup.find('textarea', id="wpTextbox1")
        if area and len(area.contents)>0 :
            result = (baseUrl+base, area.contents[0])
    return result

def findDivById(n,_id):
    """
    browses to search a 'div' with a given id
    @param n a node
    @param _id attribute to search
    @return a node with the right 'div' else None
    """
    return findTagById(n,'div',_id)

def findTagById(n,tag,_id):
    """
    browses to search a subnode with a given tag and a given id
    @param n a node to begin with
    @param tag the tag to search
    @param _id attribute to search
    @return a node with the right tag and id, else None
    """
    for node in n.childNodes:
        if node.nodeType != node.ELEMENT_NODE:
            continue
        if node.nodeName==tag and node.getAttribute('id')==_id:
            return node
        test=findTagById(node,tag,_id)
        if test:
            return test
    return None

############# a callback function for the image parser
def imgFun(d):
    """
    the standarda custom parser for a dictionary coming from an image
    which adds the feature of registering images for further process
    """
    global wParser
    modifiers=""
    if "width" in d:
        modifiers+="width=%s, " %d["width"]
    if "height" in d:
        modifiers+="height=%s, " %d["height"]
    code="\\includegraphics"
    if modifiers:
        code+="[%s]" %modifiers[:-2]
    code+="{%s}" %d["imgFile"]
    # embedding the image in a figure should be made whenether
    # there is a caption or when the image is a wiki thumnail
    figure=False
    caption=""
    for k in d: # iterate over d to find the caption, which must be last
        if type(k)==type(0): #the key must be a number
            if d[k][-2:]!="px": #not the width spec for the wiki!
                caption=d[k]
                figure=True
    for k in d:
        if type(k)==type(0): # for the numeric keys
            if d[k]=="thumb":
                figure=True
    if figure:
        code="\\begin{figure}[h!]\n\\begin{center}\n\\caption{%s}\\vspace{0.5em}\n%s\n\\end{center}\n\\end{figure}\n" %(caption, code)
    wParser.registerImage(d["imgFile"])
    return code

class lineJoiner:
    """
    a class to join lines taking in account some wiki syntax
    """

    def __init__(self, f, encoding=None, oldWiki2=False):
        """
        the constructor
        @ param f a file-like readable object
        @param encoding triggers some specific encoding if different from None
        @param oldWiki2 True to process an old style wiki2beamer source
        """
        self.encoding=encoding
        self.oldWiki2=oldWiki2
        self.lines=self.joinLines(f.readlines())

    def getLines(self):
        """
        @return the lines
        """
        return self.lines

    def joinLines(self, lines):
        """
        join lines ending with unescaped percent signs,
        unless inside codemode or nowiki mode
        @param lines a list of text lines
        """
        nowikimode = False
        codemode = False
        r = []  # result array
        s = ''  # new line
        for _l in lines:
            if self.encoding:
                _l=_l.encode(self.encoding)
            (_,nowikimode) = get_nowikimode(_l, nowikimode)
            if not nowikimode:
                (_,codemode) = get_codemode(_l, codemode)

            if not codemode:
                l = _l.rstrip() # return chars are kept only for <code>
            else:
                l = _l

            #restore markups like <math></math>, etc.
            for m in ('math', 'code', 'ref'):
                l=re.sub('&amp;lt;(/?)'+m+'&gt;', r'<\1'+m+'>', l)
            l=re.sub('"&amp;lt;references */&gt;','<references />',l)

            if (not self.oldWiki2) and l=="" and r and r[-1]!="\n\n" :
                l="\n\n" # simplify and keep the return codes for LaTeX
            if not (nowikimode or codemode) and (len(l) > 1) and (l[-1] == "%") and (l[-2] != "\\"):
                s = s + l[:-1]
            elif not (nowikimode or codemode) and (l == "%"):
                s = s + l[:-1]
            else: # when l=="" or codemode, or nowikimode, or ...
                # output a line
                s = s + l
                if (not self.oldWiki2) and len(s)>0:
                    r.append(s+"\n")
                else:
                    r.append(s)
                s = ''
                

        return r
    
class txtFileCacher:
    """
    a cache for text files
    """
    def __init__(self, oldWiki2=False):
        """
        the constructor
        @param oldWiki2 True to process an old style wiki2beamer source
        """
        self.reset()
        self.oldWiki2=oldWiki2

    def __str__(self):
        result="CACHE:\n=====\n"
        for k in self._cache.keys():
            result += " * %15s : %s\n" %(k,self._cache[k][:61])
        return result

    def reset(self):
        """
        makes a brand new cache
        """
        self._cache = dict()

    def addLines(self, filename, lines):
        """
        caches some lines
        @param filename the name of the file which contained the lines
        @param lines the contents
        """
        if not filename in self._cache:
           self._cache[filename] = lines

    def getLines(self,filename):
        """
        retrieval of data from the cache. If filename refers to a file
        whose lines are not in the cache, the lines are cached on the fly.
        @param filename
        """
        if filename in self._cache:
            return self._cache[filename]
        else:
            lines = self.read_file_to_lines(filename)
            self._cache[filename] = lines
            return lines
           
    def read_file_to_lines(self, filename, fileObj=None, encoding=None):
        """
        read file
        @param filename the name of the file to read
        @param fileObj an already open file objet if it is given
        @param encoding triggers some specific encoding if different from None
        @return the lines read from this file
        """
        if not fileObj:
            f = open(filename, "r")
            lines=lineJoiner(f, encoding, oldWiki2=self.oldWiki2).getLines()
            f.close()
        else:
            lines=lineJoiner(fileObj, encoding, oldWiki2=self.oldWiki2).getLines()
            self.addLines(filename, lines)

        return lines

    def clear(self):
        """
        clears the cache
        """
        self._cache = dict()

class wikiParser:
    """
    A converter from wiki-style layout to many high-level syntaxes
    like LaTeX/Beamer
    """

    def __init__(self, args=[], isatty=True, isUrl=False, report=False, parent=None, latexReadyParam="", oldWiki2beamer=False):
        """
        The constructor
        @param args a list of filenames, or a single URL.
        When a single URL, it is meant to be the address of a wikimedia
        page which contains a series of other addresses of the same
        mediawiki in mediawiki syntax.
        @param isatty is True when data do not come from the standard input
        @param isUrl is True to force the initialization, by considering arg as a single url which is supposed to be a normal wiki page
        @param report if True, messages are emitted to sys.stderr;
        if it is callable, it is invoked with the same messages
        @param parent pointer to the main window
        @param latexReadyParam the parameter for a signal to be emitted
        upon completion of the process
        @param oldWiki2beamer when True, uses the modes of wiki2beamer
        """
        global wParser
        wParser=self
        self.lines=[]
        input_files = []
        self.imageSet=set()
        self.report=report
        self.parent=parent
        if parent:
            # creates a fake page name to initialize the parser by
            # getting a first response from the mediawiki
            parent.wb=self
            self.baseAddress=parent.wikiIndex.replace("http://","")
            self.host=re.match(r"([^/]+).*", self.baseAddress).group(1)
            args=[parent.wikiIndex.encode("utf-8")+"/fakePage"]
            isUrl=True
            oldWiki2beamer=parent.autoOldStyle()
        self.cache=txtFileCacher(oldWiki2= oldWiki2beamer)
        self.latexReadyParam=latexReadyParam
        self.oldWiki2beamer=oldWiki2beamer
        if not isatty:
            input_files.append('stdin')
            self.cache.read_file_to_lines(filename='stdin', fileObj=sys.stdin)
        if isUrl: #forced url system
            self.include_one_address(args[0])
            input_files.append('url')
            self.cache.read_file_to_lines(filename='url', fileObj=self.urlLines)
        elif self.isUrl(args):
            input_files.append('url')
            self.cache.read_file_to_lines(filename='url', fileObj=self.urlLines)
        else:
            input_files += args
            self.lines = []
        for file_ in input_files:
            self.lines += self.include_file_recursive(file_)

    def parseWikiSource(self):
        """
        parses a text provided by self.parent in its drop area
        """
        if not self.parent:
            return
        self.reloadCache(self.parent.wikiSource, oldWiki2beamer=self.oldWiki2beamer)
        self.parent.emit(SIGNAL("latexready"), self.latexReadyParam)

    def reloadCache(self, text, info="", oldWiki2beamer=False):
        """
        Reloads the cache from a given text, after running template processors.
        @param text a unicode string with wiki code.
        @param info some informative message
        param oldWiki2beamer if True, we are in the old wiki2beamer mode
        the text will be processed to revert some effects of
        python-BeautifulSoup. Plugins will be applied, but no submission
        will be done to the special page ExpandTemplates.
        """
        if info: print >> sys.stderr, "'%s'" %info
        if oldWiki2beamer:
            text=text.replace("&lt;", "<")
            text=text.replace("&amp;", "&")
        text=self.applyPlugins(text)
        if not oldWiki2beamer:
            text=self.wikiTemplates(text)
        self.loadUrlLines(text+"\n")
        self.cache.reset()
        self.lines=self.cache.read_file_to_lines(filename='url', fileObj=self.urlLines, encoding="utf-8")

    def reloadCacheIndirect(self, text, cbInfo=None):
        """
        Reloads the cache from the current mediawiki. The given text must
        provide a series of wiki addresses.
        @param text an utf-8 string with wiki code.
        @param cbInfo a callback function to display progress messages. It should accept one string as an input.
        """
        wikiAddresses=mediawiki.linksInText(text)
        self.cache.reset()
        if cbInfo==None:
            cbInfo=self.toStdErr # default callback
        self.include_addresses(wikiAddresses, cbInfo=cbInfo)
        self.url2lines()

    def url2lines(self):
        """
        loads self.lines from the file-like object self.urlLines
        """
        self.lines=self.cache.read_file_to_lines(filename='url', fileObj=self.urlLines)
        
    def getImages(self, path, report=None):
        """
        gets the necessary images from the mediawiki
        @param path the path to write images
        @param report if True, this method will output a few messages on sys.stderr;
        if report is a callback function, this function will be called with one parameter.
        """
        href=""
        for img in self.imageSet:
            completeUrl="http://%s/index.php/File:%s" %(self.baseAddress, img)
            page=url.urlopen(completeUrl)
            soup=BeautifulSoup(page.read())
            divs=soup.findAll("div", id="file")
            for div in divs:
                a=div.find("a")
                href=a["href"]
                if report==True:
                    print >> sys.stderr, "'%s'" %href
                elif callable(report):
                    report("'%s'" %href)
            imgData=url.urlopen("http://%s/%s" %(self.host,href))
            imgFile=open(os.path.join(path,img),"w")
            imgFile.write(imgData.read())
            imgFile.close()
        return
    
    def registerImage(self, img):
        """
        registers an image filename to retreive it later
        """
        self.imageSet.add(img)

    def imageCount(self):
        """
        @return the count of embedded images
        """
        return len(self.imageSet)

    def isUrl(self, arg):
        """
        @return True if arg is a valid Url to a mediawiki.
        As a side-effect, self.lines will be loaded with the
        downloaded contents
        """
        if len(arg)<1:
            return False
        pattern=re.compile("http://(.+)/[^/]+/(.+)")
        m=pattern.match(arg[0])
        if m:
            self.baseAddress=m.group(1).decode("utf-8")
            self.host=re.findall("([^/]+).*", self.baseAddress)[0]
            basePage=m.group(2).decode("utf-8")
            text=self.getWikiContentsByTitle(basePage)
            if text:
                wikiAddresses=re.findall("\[\[([^\]]+)\]\]", text)
                self.include_addresses(wikiAddresses, cbInfo=self.toStdErr)
                return True
        return False

    def getWikiContentsByTitle(self, title):
        """
        Gets the wiki code from the website, given a page's title
        @param title the title of a wiki page
        @return the wiki code for the page, else a void string
        """
        completeUrl="http://%s/index.php?title=%s" %(self.baseAddress,url.quote_plus(title.encode("utf-8")))
        return getWikiContents(completeUrl)[1]

    def applyPlugins(self, s):
        """
        fixes the strings "&lt;math>" and "&lt;/math>", then
        pre-processes a few simple templates which have a precise definition for
        LaTeX, then processes the images.
        @param s the string to be processed
        @return the processed string
        """
        s=s.replace("&lt;math>","$")
        s=s.replace("&lt;/math>","$")
        #== recodes File:.*.jpg, Fichier:.*.jpg, etc. into Image: templates
        s=re.sub(r"\[\[(File|Fichier):([-_0-9a-zA-Z]*)\.(jpg|JPG|png|PNG|gif|GIF)",r"[[Image:\2.\3",s)
        #== the parsers of every plugin are applied, then the image parser
        parsers=map(lambda c: c(), plugins)+[imageParser(imgFun)]
        for parser in parsers:
            s=parser.sub(s)
        return s
                    
    def wikiTemplates(self, contents):
        """
        calls the special page ExpandTemplates in the wiki
        to apply templates which must be processed by mediawiki
        @param contents the code with templates (unicode string)
        @result the code with all templates expanded
        """
        completeUrl="http://%s/index.php/%s" %(self.baseAddress, "Sp%C3%A9cial:ExpandTemplates")
        data={"contexttitle":"",
              "input":"%s" %contents.encode("utf-8"),
              "removecomments":"1",
              "generate_xml":"0"}
        data=url.urlencode(data)
        page=url.urlopen(completeUrl, data)
        soup = BeautifulSoup(page.read())
        area = soup.find('textarea', id="output")
        if area:
            processedContents=area.contents[0]
        else:
            processedContents=""
        return processedContents

    def include_one_address(self, completeUrl):
        """
        gets contents from a simple wiki page
        @param completeUrl an url
        """
        text=""
        pattern=re.compile("http://(.+)/index.php/(.+)")
        m=pattern.match(completeUrl)
        if m:
            self.baseAddress=m.group(1).decode("utf-8")
            self.host=re.findall("([^/]+).*", self.baseAddress)[0]
            basePage=m.group(2).decode("utf-8")
            text=self.getWikiContentsByTitle(basePage)
            if text==None:
                text="Error: the page %s does not exist" %completeUrl
            if self.report and completeUrl:
                print >> sys.stderr, "'%s'" %completeUrl
            elif callable(self.report) and completeUrl:
                self.report("'%s'" %completeUrl)
            text=self.applyPlugins(text)
            text=self.wikiTemplates(text)
            text=text.encode("utf-8")
        self.loadUrlLines(text)
            
    def loadUrlLines(self,text):
        """
        puts a text into the file-like object self.urlLines
        @param text the input
        """
        self.urlLines=StringIO.StringIO(text)

    def toStdErr(self, info):
        """
        sends a string to sys.stderr
        @param info the information to display
        """
        if info: print >> sys.stderr, "'%s'" %info
        return
        
    def include_addresses(self, wikiAddresses, cbInfo=None):
        """
        populates self.urlLines with data coming from addresses
        self.urlLines will be a file-like object.
        @param wikiAddresses a list of wikiaddresses to visit.
        @param cbInfo a callback used to display an information about each address included. It should accept one string as input
        """
        text=""
        for a in wikiAddresses:
            # prepares the wikiAddress
            pos=a.find("|")
            if pos > 0 and pos < len(a):
                a=a[:pos]
            if cbInfo: cbInfo(a)
            contents=self.getWikiContentsByTitle(a)
            contents=self.applyPlugins(contents)
            processedContents=self.wikiTemplates(contents)
            # if processedContents still contain some included images
            # run another template processor
            if "[[Image:" in processedContents:
                processedContents=self.applyPlugins(processedContents)
            text+="\n<!-- uicilibris: begin '%s' -->\n" %a
            text+=processedContents+"\n"
            text+="\n<!-- uicilibris: end '%s' -->\n" %a
        # enforce the same encoding as ordinary text files
        text=text.encode("utf-8")
        # and make it like a text file
        self.urlLines=StringIO.StringIO(text)
            

    def include_file_recursive(self, base):
        """
        makes a list of lines from a file, including recursively
        other files when necessary
        @param base the name of the file to process
        @return a list of lines
        """
        stack = []
        output = []
        def recurse(file_):
            stack.append(file_)
            nowikimode = False
            codemode = False
            for line in self.cache.getLines(file_):
                if nowikimode or codemode:
                    if nowikiendre.match(line):
                        nowikimode = False
                    elif codeendre.match(line):
                        codemode = False
                    output.append(line)
                elif nowikistartre.match(line):
                    output.append(line)
                    nowikimode = True
                elif codestartre.match(line):
                    output.append(line)
                    codemode = True
                else:
                    include = self.includeInstruction(line)
                    if include is not None:
                        if include in stack:
                            raise IncludeLoopException('Loop detected while trying '
                                    "to include: '%s'.\n" % include +
                                    'Stack: '+ "->".join(stack))
                        else:
                            recurse(include)
                    else:
                        output.append(line)
            stack.pop()
        recurse(base)
        return output

    def includeInstruction(self,line):
        """ Extract filename to include.

        @param line string
            a line that might include an inclusion
        @return string or None
            if the line contains an inclusion, return the filename,
            otherwise return None
        """
        p = re.compile("\>\>\>(.*)\<\<\<", re.VERBOSE)
        if p.match(line):
            filename = p.sub(r"\1", line)
            return filename
        else:
            return None    
                
def get_frame_closing(state):
    return " %s \n\\end{frame}\n" % state.frame_footer

def syntax_error(message, code):
    print >>sys.stderr, 'syntax error: %s' % message
    print >>sys.stderr, '\tcode:\n%s' % code
    sys.exit(-3)

def get_nowikimode(line, nowikimode):
    """
    extracts the "nowiki" feature from a line
    @param line the line to process
    @param nowikimode the current mode regarding the "wiki" property
    @result a tuple (line, nowikimode) after processing
    """
    if not nowikimode and nowikistartre.match(line)!=None:
        line = nowikistartre.sub('', line)
        return (line, True)
    elif nowikimode and nowikiendre.match(line)!=None:
        line = nowikiendre.sub('', line)
        return (line, False)
    else:
        return (line, nowikimode)

def get_codemode(line, codemode):
    if not codemode and codestartre.match(line)!=None:
        line = codestartre.sub('', line)
        return (line, True)
    elif codemode and codeendre.match(line)!=None:
        line = codeendre.sub('', line)
        return (line, False)
    else:
        return (line, codemode)


class IncludeLoopException(Exception):
    pass


if __name__=="__main__":
    print "hello this a demo, here is a list of plugins"
    print plugins

    print "I shall create an instance of each class coming from the list of plugins"
    print "and print them"

    for p in plugins:
        print p()
    print
