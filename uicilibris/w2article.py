# -*- coding: utf-8 -*-
# 	$Id: w2book.py 42 2011-08-13 16:11:32Z georgesk $	
#
# w2article.py is part of the package uicilibris 
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

import re, w2book, url, os.path, sys
import transform2article
from expand import *
from BeautifulSoup import BeautifulSoup
from w2bstate import w2bstate

tableHeadPattern =re.compile(r"\\begin{tabular}\[table id=([0-9]+)\]")

class wiki2(w2book.wiki2):
    """
    a class which modifies  w2book.wiki2 with a LaTeX/Article
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
        result=self.preamble(documentclass="article")
        for l in self.convert2(self.lines, self.report, transform=transform2article.transform):
            l=self.processTabular(l)
            l = self.sanitize(l)
            result += l
        result += self.postamble()
        return result
