#!/usr/bin/env python
# 	$Id$	
#
# w2bstate.py is part of the package uicilibris
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

class w2bstate:
    """
    a class to implement the states of the engine which
    drives wiki2beamer objets
    """
    def __init__(self):
        """
        the constructor
        """
        self.frame_opened = False
        self.enum_item_level = ''
        self.frame_header = ''
        self.frame_footer = ''
        self.next_frame_footer = ''
        self.next_frame_header = ''
        self.current_line = 0
        self.autotemplate_opened = False
        self.defverbs = {}
        self.code_pos = 0
        self.tableStack=[]
        self.allTables=[]
        self.tableErrors=[]
        self.sourceCodeStack=[]
        self.sourceCodeActive=False
        self.sourceCodeLanguage=""
        self.currentPage=None
        return

    def __str__(self):
        result="w2bstate instance{"
        result+="enum_item_level = %s, " %self.enum_item_level
        result+="current_line = %s, " %self.current_line
        result+="defverbs = %s, " %self.defverbs
        result+="code_pos = %s, " %self.code_pos
        result+="tableStack = %s, " %self.tableStack
        result+="allTables = %s, " %self.allTables
        result+="tableErrors = %s, " %self.tableErrors
        result+="currentPage = %s" %self.currentPage
        result +="}"
        return result

    def flushTableStack(self):
        """
        resets the stack of tables
        """
        self.tableStack=[]
        return

    def switch_to_next_frame(self):
        self.frame_header = self.next_frame_header
        self.frame_footer = self.next_frame_footer
        return

