# -*- coding: utf-8 -*-
# 	$Id: w2book.py 42 2011-08-13 16:11:32Z georgesk $	
#
# w2book.py is part of the package uicilibris 
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

import re, wikiParser, url, os.path, sys
import transform2book
from expand import *
from BeautifulSoup import BeautifulSoup
from w2bstate import w2bstate

tableHeadPattern =re.compile(r"\\begin{tabular}\[table id=([0-9]+)\]")

class wiki2(wikiParser.wikiParser):
    """
    a class which enriches wikiParser with a LaTeX/Book
    export feature.

    The underlying wikiParser already processes input files or an url
    pointing to a table of contents in a mediawiki and modifies the
    content with templates defined in wikiParser.processTemplates4L
    """
    def __str__(self):
        """
        @return contents converted to Latex/Beamer syntax as a single string,
        encoded in utf-8
        """
        # finds the option for Babel, based on the current locale
        if "FR" in str(self.parent.locale):
            babelOpt="frenchb";
        else:
            babelOpt="english"
        result=self.preamble(babelOpt=babelOpt)
        for l in self.convert2(self.lines, self.report, transform=transform2book.transform):
            l=self.processTabular(l)
            l = self.sanitize(l)
            result += l
        result += self.postamble()
        result = self.processMath(result)
        return result

    def processMath(self, t):
        """
        processes math expressions inside a text
        @param t the input text
        @result the processed text
        """
        begin_arrays = [m.start() for m in re.finditer(r'\\begin{array}', t)]
        end_arrays = [m.start() for m in re.finditer(r'\\end{array}', t)]
        for i in range(len(begin_arrays)):
            b=begin_arrays[i]
            e=end_arrays[i]
            t1=t[b:e]
            t1=t1.replace('\\&','&')
            t1=t[:b]+t1+t[e:]
            t=t1
        return t

    def processTabular(self, l):
        m=tableHeadPattern.match(l)
        if m:
            tableId=int(m.group(1))
            for t in self.state.allTables:
                if t.id==tableId:
                    cols=t.columns
                    if cols < 1: cols=1
                    columns="|"+"l|"*cols
                    if t.colFormat!=None:
                        columns=t.colFormat
                    break
            l= tableHeadPattern.sub(r"\\begin{tabular}{%s}" %columns,l)
        return l

    def toFile(self, fileName, report=None):
        """
        write self contents to a file
        imports and writes necessary images
        @param report if True, this method will output a few messages on sys.stderr;
        if report is a callback function, this function will be called with one parameter.
        """
        outfile=open(fileName, "w")
        outfile.write("%s" %self)
        outfile.close()
        path=os.path.dirname(fileName)
        self.getImages(path, report)
        return

            
    def preamble(self, documentclass="book", babelOpt="frenchb"):
        """
        @param documentclass: the documentclass to use
        @ return a LaTeX preamble
        """
        return """\
\\documentclass{"""+documentclass+"""}
% -*- coding: utf-8 -*-

\\usepackage[utf8x]{inputenc}
\\usepackage{ucs}
\\usepackage{lmodern}
\\usepackage{graphicx}
\\usepackage[babelOpt]{babel}
\\usepackage{hyperref,wrapfig}
\\usepackage{amssymb}
\\usepackage{latexsym}

\\PrerenderUnicode{É} % Pre-render some accented chars for titles of chapter
\\PrerenderUnicode{À}

\\newcommand{\\nop}{}

\\begin{document}
""".replace("babelOpt", babelOpt)

    def postamble(self):
        return """\
\\end{document}
"""

    def sanitize(self, s):
        """
        @return a sanitized output: get rid of &amp; etc.
        processes the comments left by previous works;
        processes underscores in lines where there is no maths
        turns lines with math-only contents to out-of text formulas
        takes in account url-like words
        """
        # convert a few html entities introduced by beautifulsoup
        s=s.replace("&quot;","\"")
        s=s.replace("&amp;lt;math&gt;", "$")
        s=s.replace("&amp;lt;/math&gt;", "$")
        s=s.replace("&amp;lt;code&gt;", "\\texttt{")
        s=s.replace("&amp;lt;/code&gt;", "}")
        s=s.replace("&amp;lt;ref&gt;", "\\footnote{")
        s=s.replace("&amp;lt;/ref&gt;", " }")
        s=s.replace("&amp;lt;references /&gt;", "")
        s=s.replace("&amp;lt;", "<")
        s=s.replace("&amp;gt;", ">")
        s=s.replace("&gt;", ">")
        s=s.replace("&amp;amp;","\\&")
        s=s.replace("%", "\\%")
        s=re.sub(r"\\comment\{(.*)\}",r"%% \1",s)
        s=s.replace(" ;","~;")
        s=s.replace(" :","~:")
        s=s.replace(" !","~!")
        s=s.replace(" ?","~?")
        s=s.replace(" »","~»")
        s=s.replace("« ","«~")
        # some mediawiki instances do not provide the same results,
        # so here is a second pass to translate special markup
        s=s.replace("<math>", "$")
        s=s.replace("</math>", "$")
        s=s.replace("<code>", "\\texttt{")
        s=s.replace("</code>", "}")
        s=s.replace("<ref>", "\\footnote{")
        s=s.replace("</ref>", " }")
        s=s.replace("<references />", "")
        if "$" not in s:
            s=s.replace("_","\\_")
        if len(s)>2 and s[0]=="$" and s[-1]=="$":
            s="$%s$" %s
        # hyperlinks with an anchor
        olds=s
        s=re.sub(r"\[(http://[^ ]+) +(.+)]", r"\\href{\1 }{\mbox{\2} }",s)
        # http urls alone
        # avoid processing links already prefixed by "href{"
        s=re.sub(r"([^{])(http://[^ ]+)", r"\1\\href{\2 }{\mbox{\2} }",s)
        return s
    
    def convert2(self,lines, report=False, transform=lambda x, y, z: x):
        """
        convert to LaTeX book
        @param lines a list of lines
        @param report if True, messages are emitted to sys.stderr;
        if it is callable, it is invoked with the same messages
        @param transform a function to transform lines; its profile
        requires 3 parameters: a text to transform, a reference to
        the automatons's state, and a reference to a feedback (?) device;
        it returns the transformed string, and affects its other parameters
        as a side effect
        """
        self.state = w2bstate()
        result = [''] #start with one empty line as line 0
        codebuffer = []

        nowikimode = False
        codemode = False

        for line in lines:
            (line, nowikimode) = wikiParser.get_nowikimode(line, nowikimode)
            if nowikimode:
                result.append(line)
            else:
                (line, _codemode) = wikiParser.get_codemode(line, codemode)
                if _codemode and not codemode: #code mode was turned on
                    codebuffer = []
                elif not _codemode and codemode: #code mode was turned off
                    expand_code_segment(result, codebuffer, self.state)
                codemode = _codemode

                if codemode:
                    codebuffer.append(line)
                else:
                    self.state.current_line = len(result)
                    result.append(transform(line, self.state, report))

        result.append(transform("", self.state, report))   # close open environments

        #insert defverbs somewhere at the beginning
        expand_code_defverbs(result, self.state)
        return result

    def parse_usepackage(self, usepackage):
        """
        @param usepackage (str)
            the unparsed usepackage string in the form [options]{name}
        @return (tuple)
            (name(str), options(str))
        """

        p = re.compile(r'^\s*(\[.*\])?\s*\{(.*)\}\s*$')
        m = p.match(usepackage)
        g = m.groups()
        if len(g)<2 or len(g)>2:
            syntax_error('usepackage specifications have to be of the form [%s]{%s}', usepackage)
        elif g[1]==None and g[1].strip()!='':
            syntax_error('usepackage specifications have to be of the form [%s]{%s}', usepackage)
        else:
            options = g[0]
            name = g[1].strip()
            return (name, options)

    def parse_bool(self, string):
        boolean = False

        if string == 'True' or string == 'true' or string == '1':
            boolean = True
        elif string == 'False' or string == 'false' or string =='0':
            boolean = False
        else:
            syntax_error('Boolean expected (True/true/1 or False/false/0)', string)

        return boolean

