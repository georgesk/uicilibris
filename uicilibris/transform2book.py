#!/usr/bin/env python
# 	$Id: transform2book.py 36 2011-08-11 20:19:06Z georgesk $	
#
# transform2book.py is part of the package uicilibris
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

import re, sys

def transform_itemenums(string, state):
    """handle itemizations/enumerations"""
    preamble = ""   # for enumeration/itemize environment commands

    # handle itemizing/enumerations
    p = re.compile("^([\*\#]+).*$")
    m = p.match(string)
    if (m == None):
        my_enum_item_level = ""
    else:
        my_enum_item_level = m.group(1)

    # trivial: old level = new level
    if (my_enum_item_level == state.enum_item_level):
        pass
    else:
        # find common part
        common = -1 
        while (len(state.enum_item_level) > common + 1) and \
                (len(my_enum_item_level) > common + 1) and \
                (state.enum_item_level[common+1] == my_enum_item_level[common+1]):
            common = common + 1

        # close enum_item_level environments from back to front
        for i in range(len(state.enum_item_level)-1, common, -1):
            if (state.enum_item_level[i] == "*"):
                preamble = preamble + "\\end{itemize}\n"
            elif (state.enum_item_level[i] == "#"):
                preamble = preamble + "\\end{enumerate}\n"
        
        # open my_enum_item_level environments from front to back
        for i in range(common+1, len(my_enum_item_level)):
            if (my_enum_item_level[i] == "*"):
                preamble = preamble + "\\begin{itemize}\n"
            elif (my_enum_item_level[i] == "#"):
                preamble = preamble + "\\begin{enumerate}\n"
    state.enum_item_level = my_enum_item_level
    
    # now, substitute item markers
    p = re.compile("^([\*\#]+)(.*)$")
    _string = p.sub(r"  \\item\2", string)
    string = preamble + _string
 
    return string

class tableState:
    """
    a class to maintain the structure of a Latex table
    """
    autoinc=0
    
    def __init__(self):
        self.id=tableState.autoinc
        tableState.autoinc+=1
        self.currentCol=0
        self.columns=0
        self.lines=0
        self.colFormat=None
    def __str__(self):
        return "table{id:%d, columns:%d}" %(self.id,self.columns)
    def setColFormat(self, colFormat):
        self.colFormat=colFormat
        return
    def addCell(self):
        self.currentCol+=1
        if self.currentCol > self.columns:
            self.columns = self.currentCol
    def addLine(self):
        self.currentCol=0
        self.lines+=1
    def close(self):
        pass
    def latexHeader(self):
        return "\\begin{tabular}[table id=%d]\n\\hline\n" %self.id
    def latexCell(self,contents):
        if contents==None:
            contents="" # force a str type
        if self.currentCol>1:
            return "&"+contents
        else:
            return contents
    def latexLine(self):
        return "\n\\\\ \\hline\n"
    def latexFooter(self):
        return "\n\\\\ \\hline\n\\end{tabular}\\\\[0.5em]\n"

def flushTables(string, state, report=None):
    """
    flushes the table state
    @param string the line which is to process
    @state the current state of the automaton
    @param report if True, messages are emitted to sys.stderr;
    if it is callable, it is invoked with the same messages
    """
    if len(state.tableStack)==0 and len(state.tableErrors)==0:
        # fine !
        string=string[:-5]+ " tables OK"+string[-5:]
        return string
    else:
        t=tableState()
        reportErr("table not closed (%s)" %state.currentPage, report)
        state.flushTableStack()
        return (t.latexFooter() * len (state.tableStack)) +"\n"+ string[:-5] + " %d table(s) not closed." %len (state.tableStack)+string[-5:]

def reportErr(msg, report=None):
    """
    emits messages for the user
    @param report if True, messages are emitted to sys.stderr;
    if it is callable, it is invoked with the same messages
    """
    msg="Error: "+ msg
    if report==True:
        print >> sys.stderr, msg
    elif callable(report):
        report(msg)
    return
        
def transform_tables(string, state, report=None):
    """
    handle mediawiki tables
    @param string the current line to transform
    @param state the state of the automaton
    @param report if True, messages are emitted to sys.stderr;
    if it is callable, it is invoked with the same messages
    """
    ### begin of included mediawiki page
    p = re.compile(r"^<!-- uicilibris: begin '(.*)' -->$")
    m=p.match(string)
    if m:
        state.currentPage=m.group(1)
        return string
    ### end of included mediawiki page
    p = re.compile(r"^<!-- uicilibris: end .* -->$")
    if p.match(string):
        return flushTables(string, state, report)
    ### table header
    p = re.compile("^({\|)(.*)$")
    m=p.match(string)
    if m:
        t=tableState()
        # recognition of latex="some columns format"
        p1 = re.compile("^{\|.*latex=&amp;quot;([^&]+)&amp;quot;")
        m1=p1.match(string)
        if m1:
            t.setColFormat(m1.group(1)) 
        state.tableStack.append(t)
        state.allTables.append(t)
        return t.latexHeader()
    ### table new line
    p = re.compile(r"^\|-+\s*$")
    m=p.match(string)
    if m:
        t=topOfStack(state.tableStack)
        if t!=None:
            t.addLine()
            return t.latexLine()
        else:
            reportErr("new table line, with no table (%s)" %state.currentPage, report)
            state.tableErrors.append("line")
            return string
    ### table end
    p = re.compile(r"^\|}\s*$")
    m=p.match(string)
    if m:
        if len(state.tableStack)>0:
            t=state.tableStack.pop()
            t.close()
            return t.latexFooter()
        else:
            reportErr("table footer with no table (%s)" %state.currentPage, report)
            state.tableErrors.append("footer")
            return string
    ### table cell
    p = re.compile(r"^\|([^\|].*)?$")
    m=p.match(string)
    if m:
        t=topOfStack(state.tableStack)
        if t != None:
            t.addCell()
            return t.latexCell(m.group(1))
        else:
            reportErr("table cell with no table (%s). This can be due to a double closing curly brace '}}' in a mathematic formula, which is inside a template. To avoid corrupting the model, replace '}}' by '} }' in the math formula." %state.currentPage, report)
            state.tableErrors.append("cell")
            return string
    p = re.compile(r"^!([^!].*)?$")
    m=p.match(string)
    if m:
        t=topOfStack(state.tableStack)
        if t != None:
            t.addCell()
            return t.latexCell("\\textbf{%s}" %m.group(1))
        else:
            reportErr("table highlighted cell with no table (%s)" %state.currentPage, report)
            state.tableErrors.append("highlighted cell")
            return string
    # default case: do nothing
    return string

def topOfStack(stack):
    """
    returns the top of the stack if any
    @param stack a sequence
    @return an objet, or else NOne
    """
    if len(stack)>0:
        return stack[-1]
    else:
        return None

def transform_h3_to_subsec(string, state):
    """ headings (2) to subsections """
    subsec_opening = r"\n\\subsection\2{\1}\n\n"

    p = re.compile("^===\s*(.*?)\s*===(.*)", re.VERBOSE)
    _string = p.sub(subsec_opening, string)
    
    return _string

def transform_h2_to_sec(string, state):
    """ headings (1) to sections """
    sec_opening = r"\n\\section\2{\1}\n\n"
    p = re.compile("^==\s*(.*?)\s*==(.*)", re.VERBOSE)
    _string = p.sub(sec_opening, string)

    return _string

def transform_h1_to_chap(string, state):
    """ headings (0) to chapters """
    sec_opening = r"\n\\chapter\2{\1}\n\n"
    p = re.compile("^=\s*(.*?)\s*=(.*)", re.VERBOSE)
    _string = p.sub(sec_opening, string)

    return _string

def transform_boldfont(string):
    """ bold font """
    p = re.compile("'''(.*?)'''", re.VERBOSE)
    string = p.sub(r"\\textbf{\1}", string)
    return string

def transform_italicfont(string):
    """ italic font """
    p = re.compile("''(.*?)''", re.VERBOSE)
    string = p.sub(r"\\emph{\1}", string) 
    return string

def transform_h4_to_subsubsec(string, state):
    """headings (3) to subsubsection"""
    subsubsec_opening = r"\n\\subsubsection\2{\1}\n\n"
    p = re.compile("^!?====\s*(.*?)\s*====(.*)", re.VERBOSE)
    _string = p.sub(subsubsec_opening, string)

    return _string

def transform_commentLines(string, state):
    """
    transform comment-only lines in LaTeX comment lines
    @param string a line
    @param state an object with the state of the process
    @return the line with transforms done
    """
    p = re.compile("^<!-- (.*) -->$")
    m=p.match(string)
    if m:
        return "\\comment{%s}\n" %m.group(1)
    else:
        return string
    
def transform(string, state, report=False):
    """
    convert/transform one line in context of state for w2book (wiki to book)
    @param string the current line to transform
    @param state the state of the automaton
    @param report if True, messages are emitted to sys.stderr;
    if it is callable, it is invoked with the same messages
    """
    string = transform_h4_to_subsubsec(string, state)
    string = transform_h3_to_subsec(string, state)
    string = transform_h2_to_sec(string, state)
    string = transform_h1_to_chap(string, state)
    string = transform_boldfont(string)
    string = transform_italicfont(string)

    string = transform_itemenums(string, state)
    string = transform_tables(string, state, report)
    string = transform_commentLines(string, state)

    return string

