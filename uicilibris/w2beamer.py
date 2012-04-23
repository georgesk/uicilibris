# -*- coding: utf-8 -*-
# 	$Id: w2book.py 42 2011-08-13 16:11:32Z georgesk $	
#
# w2beamer.py is part of the package uicilibris 
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
from transform import transform
from expand import *
from BeautifulSoup import BeautifulSoup
from w2bstate import w2bstate

tableHeadPattern =re.compile(r"\\begin{tabular}\[table id=([0-9]+)\]")

lstbasicstyle=\
r"""{basic}{
    captionpos=t,%
    basicstyle=\footnotesize\ttfamily,%
    numberstyle=\tiny,%
    numbers=left,%
    stepnumber=1,%
    frame=single,%
    showspaces=false,%
    showstringspaces=false,%
    showtabs=false,%
    %
    keywordstyle=\color{blue},%
    identifierstyle=,%
    commentstyle=\color{gray},%
    stringstyle=\color{magenta}%
}"""

autotemplate = [\
    ('documentclass', '{beamer}'),\
    ('usepackage', '{listings}'),\
    ('usepackage', '{wasysym}'),\
    ('usepackage', '{graphicx}'),\
    ('date', '{\\today}'),\
    ('lstdefinestyle', lstbasicstyle),\
    ('titleframe', 'True')\
]

nowikistartre = re.compile(r'^<\[\s*nowiki\s*\]')
nowikiendre = re.compile(r'^\[\s*nowiki\s*\]>')
codestartre = re.compile(r'^<\[\s*code\s*\]')
codeendre = re.compile(r'^\[\s*code\s*\]>')

class wiki2(wikiParser.wikiParser):
    """
    a class which enriches wikiParser with a LaTeX/Beamer
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
        result=""
        selectedframemode = self.scan_for_selected_frames()
        if selectedframemode:
            result = self.convert2beamer_selected()
        else:
            result = self.convert2beamer_full()
        result="".join(result)
        return result

    def convert2beamer_selected(self):
        """
        converts only selected lines
        """
        selected_lines = self.filter_selected_lines()
        out = self.convert2beamer_full(selected_lines)
        return out

    def convert2beamer_full(self):
        """
        convert to LaTeX beamer
        @return the text in LaTeX format
        """
        state = w2bstate()
        result = [''] #start with one empty line as line 0
        codebuffer = []
        autotemplatebuffer = []
        autotemplate=[]

        nowikimode = False
        codemode = False
        autotemplatemode = False

        for line in self.lines:
            (line, nowikimode) = self.get_nowikimode(line, nowikimode)
            if nowikimode:
                result.append(line)
            else:
                (line, _codemode) = self.get_codemode(line, codemode)
                if _codemode and not codemode: #code mode was turned on
                    codebuffer = []
                elif not _codemode and codemode: #code mode was turned off
                    expand_code_segment(result, codebuffer, state)
                codemode = _codemode

                if codemode:
                    codebuffer.append(line)
                else:
                    (line, _autotemplatemode) = self.get_autotemplatemode(line, autotemplatemode)
                    if _autotemplatemode and not autotemplatemode: #autotemplate mode was turned on
                        autotemplatebuffer = []
                    elif not _autotemplatemode and autotemplatemode: #autotemplate mode was turned off
                        self.expand_autotemplate_opening(result, autotemplatebuffer, state, autotemplate)
                    autotemplatemode = _autotemplatemode

                    if autotemplatemode:
                        autotemplatebuffer.append(line)
                    else:
                        state.current_line = len(result)
                        result.append(transform(line, state))

        result.append(transform("", state))   # close open environments

        if state.frame_opened:
            result.append(self.get_frame_closing(state))
        if state.autotemplate_opened:
            result.append(self.get_autotemplate_closing())

        #insert defverbs somewhere at the beginning
        expand_code_defverbs(result, state)

        return result

    def get_autotemplate_closing(self):
        return '\n\end{document}\n'

    def get_frame_closing(self, state):
        return " %s \n\\end{frame}\n" % state.frame_footer

    def expand_autotemplate_opening(self, result, templatebuffer, state, autotemplate):
        """
        expands the output code to insert an automated template
        @param result
        @param templatebuffer
        @param state
        @param autotemplate
        """
        my_autotemplate = self.parse_autotemplate(templatebuffer)
        the_autotemplate = self.unify_autotemplates([autotemplate, my_autotemplate])

        opening = self.expand_autotemplate_gen_opening(the_autotemplate)

        result.append(opening)
        result.append('')
        state.code_pos = len(result)
        state.autotemplate_opened = True
        return

    def expand_autotemplate_gen_opening(self, autotemplate):
        """
        @param autotemplate (list)
            the specification of the autotemplate in the form of a list of tuples
        @return (string)
            the string the with generated latex code
        """
        titleframe = False
        out = []
        for item in autotemplate:
            if item[0]!='titleframe':
                out.append('\\%s%s' % item)
            else:
                titleframe = self.parse_bool(item[1])

        out.append('\n\\begin{document}\n')
        if titleframe:
            out.append('\n\\frame{\\titlepage}\n')

        return '\n'.join(out)

    def unify_autotemplates(self, autotemplates):
        usepackages = {} #packagename : options
        documentclass = ''
        titleframe = False

        merged = []
        for template in autotemplates:
            for command in template:
                if command[0] == 'usepackage':
                    (name, options) = self.parse_usepackage(command[1])
                    usepackages[name] = options
                elif command[0] == 'titleframe':
                    titleframe = command[1]
                elif command[0] == 'documentclass':
                    documentclass = command[1]
                else:
                    merged.append(command)

        autotemplate = []
        autotemplate.append(('documentclass', documentclass))
        for (name, options) in usepackages.items():
            if options != None and options.strip() != '':
                string = '%s{%s}' % (options, name)
            else:
                string = '{%s}' % name
            autotemplate.append(('usepackage', string))
        autotemplate.append(('titleframe', titleframe))

        autotemplate.extend(merged)

        return autotemplate

    def parse_autotemplate(self, autotemplatebuffer):
        """
        @param autotemplatebuffer (list)
            a list of lines found in the autotemplate section
        @return (list)
            a list of tuples of the form (string, string) with \command.parameters pairs
        """
        global autotemplate
        
        for line in autotemplatebuffer:
            if len(line.lstrip())==0: #ignore empty lines
                continue
            if len(line.lstrip())>0 and line.lstrip().startswith('%'): #ignore lines starting with % as comments
                continue

            tokens = line.split('=', 1)
            if len(tokens)<2:
                syntax_error('lines in the autotemplate section have to be of the form key=value', line)

            autotemplate.append((tokens[0], tokens[1]))

        return autotemplate

    def get_autotemplatemode(self, line, autotemplatemode):
        """
        detects the auto template mode
        @param line a line to be tested; will be eventualy stripped
        @param autotemplatemode to get the result of the detection
        """
        autotemplatestart = re.compile(r'^<\[\s*autotemplate\s*\]')
        autotemplateend = re.compile(r'^\[\s*autotemplate\s*\]>')
        if not autotemplatemode and autotemplatestart.match(line)!=None:
            line = autotemplatestart.sub('', line)
            return (line, True)
        elif autotemplatemode and autotemplateend.match(line)!=None:
            line = autotemplateend.sub('', line)
            return (line, False)
        else:
            return (line, autotemplatemode)

    def get_nowikimode(self, line, nowikimode):
        """
        detects the nowiki mode
        @param line a line to be tested; will be eventualy stripped
        @param nowikimode to get the result of the detection
        """
        global nowikistartre
        if not nowikimode and nowikistartre.match(line)!=None:
            line = nowikistartre.sub('', line)
            return (line, True)
        elif nowikimode and nowikiendre.match(line)!=None:
            line = nowikiendre.sub('', line)
            return (line, False)
        else:
            return (line, nowikimode)

    def get_codemode(self, line, codemode):
        """
        detects the code mode
        @param line a line to be tested; will be eventualy stripped
        @param codemode to get the result of the detection
        """
        global codestartre
        if not codemode and codestartre.match(line)!=None:
            line = codestartre.sub('', line)
            return (line, True)
        elif codemode and codeendre.match(line)!=None:
            line = codeendre.sub('', line)
            return (line, False)
        else:
            return (line, codemode)
        
    def filter_selected_lines(self):
        """
        @return the list of selected lines
        """
        selected_lines = []

        selected_frame_opened = False
        unselected_frame_opened = False
        frame_closed = True
        frame_manually_closed = False
        for line in self.lines:
            if line_opens_selected_frame(line):
                selected_frame_opened = True
                unselected_frame_opened = False
                frame_closed = False

            if self.line_opens_unselected_frame(line):
                unselected_frame_opened = True
                selected_frame_opened = False
                frame_closed = False

            if self.line_closes_frame(line):
                unselected_frame_opened = False
                selected_frame_opened = False
                frame_closed = True
                frame_manually_closed = True

            if selected_frame_opened or (frame_closed and not frame_manually_closed):
                selected_lines.append(line)

        return selected_lines

    def line_opens_selected_frame(self,line):
        """
        @return True if the line opens a select frame
        """
        p = re.compile("^!====\s*(.*?)\s*====(.*)", re.VERBOSE)
        if p.match(line) != None:
            return True
        return False

    def line_closes_frame(self,line):
        """
        @return True if the line closes a select frame
        """
        p = re.compile("^\s*\[\s*frame\s*\]>", re.VERBOSE)
        if p.match(line) != None:
            return True
        return False

    def scan_for_selected_frames(self):
        """
        scans for frames that should be rendered exclusively,
        @returns True if there are frames that should be rendered exclusively.
        """
        p = re.compile("^!====\s*(.*?)\s*====(.*)", re.VERBOSE)
        for line in self.lines:
            mo = p.match(line)
            if mo != None:
                return True
        return False

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
    
            
    def preamble(self):
        return """\
\\documentclass{book}
% -*- coding: utf-8 -*-

\\usepackage[utf8x]{inputenc}
\\usepackage{ucs}
\\usepackage{lmodern}
\\usepackage{graphicx}
\\usepackage[frenchb]{babel}
\\usepackage{hyperref,wrapfig}
\\usepackage{amssymb}
\\usepackage{latexsym}

\\PrerenderUnicode{É} % Pre-render some accented chars for titles of chapter
\\PrerenderUnicode{À}

\\newcommand{\\nop}{}

\\begin{document}
"""

    def postamble(self):
        return """\
\\end{document}
"""

    def sanitize(self, s):
        """
        @return a sanitized output: get rid of <math>, &amp; etc.
        processes the comments left by previous works;
        processes underscores in lines where there is no maths
        turns lines with math-only contents to out-of text formulas
        takes in account url-like words
        """
        s=s.replace("&quot;","\"")
        s=s.replace("&amp;lt;math&gt;", "$")
        s=s.replace("&amp;lt;/math&gt;", "$")
        s=s.replace("&amp;lt;code&gt;", "\\texttt{")
        s=s.replace("&amp;lt;/code&gt;", "}")
        s=s.replace("&amp;lt;ref&gt;", "\\footnote{")
        s=s.replace("&amp;lt;/ref&gt;", " }")
        s=s.replace("&amp;lt;references /&gt;", "")
        s=s.replace("&amp;lt;", "<")
        s=s.replace("&gt;", ">")
        s=s.replace("&amp;","\\&")
        s=s.replace("%", "\\%{}")
        s=re.sub(r"\\comment\{(.*)\}",r"%% \1",s)
        if "$" not in s:
            s=s.replace("_","\\_")
        if len(s)>2 and s[0]=="$" and s[-1]=="$":
            s="$%s$" %s
        s=re.sub(r"(http://[^ \}]+)", r"\\href{\1 }{\mbox{\1} }",s)
        return s
    
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

        string="%s" %string
        if string == 'True' or string == 'true' or string == '1':
            boolean = True
        elif string == 'False' or string == 'false' or string =='0':
            boolean = False
        else:
            syntax_error('Boolean expected (True/true/1 or False/false/0)', string)

        return boolean

