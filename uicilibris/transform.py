#!/usr/bin/env python
# 	$Id: transform.py 31 2011-08-11 09:00:59Z georgesk $	
#
# transform.py is part of the package uicilibris
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

import re

def get_frame_closing(state):
    return " %s \n\\end{frame}\n" % state.frame_footer

def escape_resub(string):
    p = re.compile(r"\\")
    return p.sub(r"\\\\", string)

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
    _string = p.sub(r"  \\item \2", string)
    string = preamble + _string
 
    return string

def transform_define_foothead(string, state):
    """ header and footer definitions"""
    p = re.compile("^@FRAMEHEADER=(.*)$", re.VERBOSE)
    m = p.match(string)
    if (m != None):
        #print m.group(1)
        state.next_frame_header = m.group(1)
        string = ""
    p = re.compile("^@FRAMEFOOTER=(.*)$", re.VERBOSE)
    m = p.match(string)
    if (m != None):
        #print m.group(1)
        state.next_frame_footer = m.group(1)
        string = ""
    return string

def transform_detect_manual_frameclose(string, state):
    """ detect manual closing of frames """
    p = re.compile(r"\[\s*frame\s*\]>")
    if state.frame_opened:
        if p.match(string) != None:
            state.frame_opened = False
    return string

def transform_h4_to_frame(string, state):
    """headings (3) to frames"""
    frame_opening = r"\\begin{frame}\2\n \\frametitle{\1}\n %s \n" % escape_resub(state.next_frame_header)
    frame_closing = escape_resub(get_frame_closing(state))
    
    p = re.compile("^!?====\s*(.*?)\s*====(.*)", re.VERBOSE)
    if not state.frame_opened:
        _string = p.sub(frame_opening, string)
    else:
        _string = p.sub(frame_closing + frame_opening, string)

    if (string != _string):
        state.frame_opened = True
        state.switch_to_next_frame()

    return _string

def transform_h3_to_subsec(string, state):
    """ headings (2) to subsections """
    frame_closing = escape_resub(get_frame_closing(state))
    subsec_opening = r"\n\\subsection\2{\1}\n\n"

    p = re.compile("^===\s*(.*?)\s*===(.*)", re.VERBOSE)
    if state.frame_opened:
        _string = p.sub(frame_closing + subsec_opening, string)
    else:
        _string = p.sub(subsec_opening, string)
    if (string != _string):
        state.frame_opened = False
    
    return _string

def transform_h2_to_sec(string, state):
    """ headings (1) to sections """
    frame_closing = escape_resub(get_frame_closing(state))
    sec_opening = r"\n\\section\2{\1}\n\n"
    p = re.compile("^==\s*(.*?)\s*==(.*)", re.VERBOSE)
    if state.frame_opened:
        _string = p.sub(frame_closing + sec_opening, string)
    else:
        _string = p.sub(sec_opening, string)
    if (string != _string):
        state.frame_opened = False

    return _string

def transform_replace_headfoot(string, state):
    string = string.replace("<---FRAMEHEADER--->", state.frame_header)
    string = string.replace("<---FRAMEFOOTER--->", state.frame_footer)
    return string

def transform_environments(string):
    """
    latex environments, the users takes full responsibility
    for closing ALL opened environments
    exampe:
    <[block]{block title}
    message
    [block]>
    """
    # -> open
    p = re.compile("^<\[([^{}]*?)\]", re.VERBOSE)
    string = p.sub(r"\\begin{\1}", string)
    # -> close
    p = re.compile("^\[([^{}]*?)\]>", re.VERBOSE)
    string = p.sub(r"\\end{\1}", string)

    return string

def transform_columns(string):
    """ columns """
    p = re.compile("^\[\[\[(.*?)\]\]\]", re.VERBOSE)
    string = p.sub(r"\\column{\1}", string)
    return string

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

def _transform_mini_parser(character, replacement, string):
    # implemented as a state-machine
    output, typewriter = [], []
    seen_at, seen_escape = False, False
    for char in string:
        if seen_escape:
            if char == character:
                output.append(character)
            else:
                output.append('\\' + char)
            seen_escape = False
        elif char == "\\":
            seen_escape = True
        elif char == character:
            if seen_at:
                seen_at = False
                output, typewriter = typewriter, output
                output.append('\\'+replacement+'{')
                output += typewriter
                output.append('}')
                typewriter = []
            else:
                seen_at = True
                output, typewriter = typewriter, output
        else:
            output.append(char)
    if seen_at:
        output, typewriter = typewriter, output
        output.append(character)
        output += typewriter
    return "".join(output)

def transform_typewriterfont(string):
    """ typewriter font """
    return _transform_mini_parser('@', 'texttt', string)

def transform_alerts(string):
    """ alerts """
    return _transform_mini_parser('!', 'alert', string)

def transform_colors(string):
    """ colors """
    p = re.compile("_([^_\\\\{}]*?)_([^_]*?[^_\\\\{}])_", re.VERBOSE)
    string = p.sub(r"\\textcolor{\1}{\2}", string) 
    return string
   
def transform_footnotes(string):
    """ footnotes """
    p = re.compile("\(\(\((.*?)\)\)\)", re.VERBOSE)
    string = p.sub(r"\\footnote{\1}", string) 
    return string

def transform_graphics(string):
    """ figures/images """
    p = re.compile("\<\<\<(.*?),(.*?)\>\>\>", re.VERBOSE)
    string = p.sub(r"\\includegraphics[\2]{\1}", string) 
    p = re.compile("\<\<\<(.*?)\>\>\>", re.VERBOSE)
    string = p.sub(r"\\includegraphics{\1}", string) 
    return string

def transform_substitutions(string):
    """ substitutions """
    p = re.compile("(\s)-->(\s)", re.VERBOSE)
    string = p.sub(r"\1$\\rightarrow$\2", string) 
    p = re.compile("(\s)<--(\s)", re.VERBOSE)
    string = p.sub(r"\1$\\leftarrow$\2", string) 
    p = re.compile("(\s)==>(\s)", re.VERBOSE)
    string = p.sub(r"\1$\\Rightarrow$\2", string) 
    p = re.compile("(\s)<==(\s)", re.VERBOSE)
    string = p.sub(r"\1$\\Leftarrow$\2", string) 
    p = re.compile("(\s):-\)(\s)", re.VERBOSE)
    string = p.sub(r"\1\\smiley\2", string) 
    p = re.compile("(\s):-\((\s)", re.VERBOSE)
    string = p.sub(r"\1\\frownie\2", string)
    return string

def transform_vspace(string):
    """vspace"""
    p = re.compile("^\s*--(.*)--\s*$")
    string = p.sub(r"\n\\vspace{\1}\n", string)
    return string

def transform_vspacestar(string):
    """vspace*"""
    p = re.compile("^\s*--\*(.*)--\s*$")
    string = p.sub(r"\n\\vspace*{\1}\n", string)
    return string

def transform_uncover(string):
    """uncover"""
    p = re.compile("\+<(.*)>\s*{(.*)") # +<1-2>{.... -> \uncover<1-2>{....
    string = p.sub(r"\uncover<\1>{\2", string)
    return string

def transform_only(string):
    """only"""
    p = re.compile("-<(.*)>\s*{(.*)") # -<1-2>{.... -> \only<1-2>{....
    string = p.sub(r"\only<\1>{\2", string)
    return string

def transform(string, state, report=False):
    """
    convert/transform one line in context of state for w2beamer (wiki to beamer)
    @param string the current line to transform
    @param state the state of the automaton
    @param report if True, messages are emitted to sys.stderr;
    if it is callable, it is invoked with the same messages.
    this parameter is currently not used for "wiki to beamer"
    """

    #string = transform_itemenums(string, state)
    string = transform_define_foothead(string, state)
    string = transform_detect_manual_frameclose(string, state)
    string = transform_h4_to_frame(string, state)
    string = transform_h3_to_subsec(string, state)
    string = transform_h2_to_sec(string, state)
    string = transform_replace_headfoot(string, state)

    string = transform_environments(string)
    string = transform_columns(string)
    string = transform_boldfont(string)
    string = transform_italicfont(string)
    string = transform_typewriterfont(string)
    string = transform_alerts(string)
    string = transform_colors(string)
    string = transform_footnotes(string)
    string = transform_graphics(string)
    string = transform_substitutions(string)
    string = transform_vspacestar(string)
    string = transform_vspace(string)
    string = transform_uncover(string)
    string = transform_only(string)

    string = transform_itemenums(string, state)

    return string
