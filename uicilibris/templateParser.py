#!/usr/bin/env python
# 	$Id: templateParser.py 38 2011-08-13 09:50:01Z georgesk $	
#
# templateParser.py is part of the package uicilibris
#
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

import re, sys

class templateParser:
    """
    a class to parse wiki templates, based on the module re
    """

    def __init__(self, ident, fun):
        """
        the constructor
        @param ident the identifier of the template
        @param fun a function necessary to get the parameters and output the result
        """
        self.ident=ident
        self.parseFunc=self.pfMaker(fun)
        regexp=r"{{%s((?:\s*\|[^|}]+)*)}}" %self.ident
        self.pattern=re.compile(regexp)
        self.regexp=regexp

    def __str__(self):
        """
        returns a printable form
        """
        return "templateParser(%s, ...)" %self.ident
    
    def sub(self, text):
        """
        makes every substitution in a given text and returns the result
        @param text the given text
        @return the result with every substitution done
        """
        return self.pattern.sub(self.parseFunc, text)

    def pfMaker(self,fun):
        """
        creates a parse function
        @param fun a function getting the dictionary of parameters of a template
        @return a function whose profile is: input parameter = a match expression, result = a string
        """
        def pf(m):
            params=m.group(1)
            params=params[1:].split("|")
            dic={}
            i=0
            for p in params:
                m=re.match("([\S]+)=(.*)",p)
                if m:
                    dic[m.group(1)]=m.group(2)
                else:
                    dic[i]=p
                    i+=1
            try:
                return fun(dic)
            except:
                exctype, excval = sys.exc_info()[:2]
                exc=re.findall(".*\.(.*)'.*", "%s" %exctype)[0]
                pass
            return "{\\textbf{%s: %s}; could not translate the template '%s'}" %(exc, excval, self.ident)
        return pf

class imageParser(templateParser):
    """
    a class to parse wiki images, based on the module re
    """

    def __init__(self, fun=None):
        """
        the constructor
        @param fun a function necessary to get the parameters and output the result
        """
        if fun!=None:
            templateParser.__init__(self,"Image:", fun)
        else:
            templateParser.__init__(self,"Image:",self.imgFun)
        regexp=r"\[\[%s([^|\]]+)((?:\s*\|[^|\]]+)*)\]\]" %self.ident
        self.pattern=re.compile(regexp)
        self.regexp=regexp

    def imgFun(self,d):
        """
        the standard parser for a dictionary coming from an image
        """
        modifiers=""
        if "width" in d:
            modifiers+="width=%s, " %d["width"]
        if "height" in d:
            modifiers+="height=%s, " %d["height"]
        code="\\includegraphics"
        if modifiers:
            code+="[%s]" %modifiers[:-2]
        code+="{%s}" %d["imgFile"]
        figure=False
        caption=""
        for k in d:
            if type(k)==type(0): # for the numeric keys
                if d[k]=="thumb":
                    figure=True
                elif caption=="": # the first unindentified value becomes a caption
                    figure=True
                    caption=d[k]
        if figure:
            code="\\begin{figure}[h!]\n\\begin{center}\n\\caption{%s}\\\\ \n%s\n\\end{center}\n\\end{figure}\n" %(caption, code)
            
        return code

    def pfMaker(self,fun):
        """
        creates a parse function
        @param fun a function getting the dictionary of parameters of a template
        @return a function whose profile is: input parameter = a match expression, result = a string
        """
        def pf(m):
            dic={}
            dic["imgFile"]=m.group(1)
            i=0
            params=m.group(2)
            params=params.split("|")[1:]
            for p in params:
                m=re.match("([\S]+)=(.*)",p)
                if m:
                    dic[m.group(1)]=m.group(2)
                else:
                    dic[i]=p
                    i+=1
            try:
                return fun(dic)
            except:
                exctype, excval = sys.exc_info()[:2]
                exc=re.findall(".*\.(.*)'.*", "%s" %exctype)[0]
                pass
            return "{\\textbf{%s: %s}; could not translate the template '%s'}" %(exc, excval, self.ident)
        return pf




if __name__=="__main__":
    ############################################################
    ##### These examples give a demo of the templateParser class
    ############################################################
    input="""{{!}} bla bla {{!}} bla {{Latex:ref|fig:fig2}} bla bla
{{Latex:Figure|pic=onePic.png|schematic=oneSketch.png|caption=The caption|label=The label}}
bla bla {{Latex:Label|fig:other}} bla bla
a figure with a missing parameter:
{{Latex:Figure|schematic=oneSketch.png|caption=Figure with a missing param|label=fig:fig2}},
and now an image : [[Image:theImage.png|width=5cm|thumb|the Caption]]."""
    
    ####### nullary template
    bang=templateParser("!",fun=lambda x: "|")
    
    ####### templates with one mandatory anonymous parameter
    ref=templateParser("Latex:ref", fun=lambda d: " \\ref{%s}" %d[0])
    label=templateParser("Latex:Label", fun=lambda d: "\\label{%s}" %d[0])
    
    ####### a template with named *mandatory* parameters
    figure=templateParser("Latex:Figure", fun=lambda d: "\\begin{figure}[h!]\\begin{center}\\includegraphics[height=1.5cm]{pic-%s}\\includegraphics[height=1.5cm]{schematic-%s}\\\\ \\caption{%s\\label{%s}}\\end{center}\\end{figure}" %(d["pic"], d["schematic"],d["caption"],d["label"]))
    
    ####### a better template for named parameters, providing defauts
    def pFigure(d):
        result="\\begin{figure}[h!]\\begin{center}"
        if "pic" in d:
            result+="\\includegraphics[height=1.5cm]{pic-%s}" %d["pic"]
        if "schematic" in d:
            result+="\\includegraphics[height=1.5cm]{schematic-%s}" %d["schematic"]
        result+="\\\\ "
        if "caption" in d:
            result+="\\caption{%s" %d["caption"]
            if "label" in d:
                result+="\\label{%s}" %d["label"]
            result+="}"
        result +="\\end{center}\\end{figure}"
        return result
    figurePlus=templateParser("Latex:Figure", fun=pFigure)
            

    
    templates=[bang, ref, label, figure, figurePlus]
    
    code= "\\section{The input}\n"
    code+= "\\begin{verbatim*}input= " + input + "\\end{verbatim*}\n"
    for t in templates:
        code += "\\section{%s}\n" %t
        code += t.sub(input) + "\n"
    imgT=imageParser()
    code += "\\section{Images}\n"
    code += imgT.sub(input) + "\n"

    texSource="""\
\\documentclass{article}
%% -*- coding: utf-8 -*-

\\usepackage[utf8x]{inputenc}
\\usepackage{ucs}
\\usepackage{lmodern}
\\usepackage{graphicx}
\\usepackage[english]{babel}
\\usepackage{hyperref,wrapfig}

\\begin{document}
%s
\\end{document}
""" %code
    
    import subprocess
    outfile=open("essai.tex","w")
    outfile.write(texSource)
    outfile.close()
    cmd="pdflatex -interaction=batchmode essai.tex; pdflatex -interaction=batchmode essai.tex; evince essai.pdf"
    subprocess.call(cmd, shell=True)
    
    
    
        
