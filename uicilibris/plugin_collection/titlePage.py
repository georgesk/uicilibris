# the plugin titlePage is part of the package uicilibris
#
# (c) 2011      Georges Khaznadar (georgesk@ofset.org)
#
# purpose: parsing a template defined in a mediawiki
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

from templateParser import templateParser, imageParser
from plugin.plugin import *
import wikiParser

def pTitlePage(d):
    result="\\begin{titlepage}"
    if "firstLine" in d:
        result+="{\\Large %s}\\\\[6em] \n" %d["firstLine"]
    result+="\\begin{center}"
    if "image" in d:
        result+="\\includegraphics[width=1.0\\textwidth]{%s}\\\\[1em] \n" %d["image"]
        wikiParser.wParser.registerImage(d["image"])
    if "topic" in d:
        result+="{\\large %s}\\\\[6em] \n" %d["topic"]
    if "title" in d:
        result+="{\\Huge %s}\\\\[1em] \n" %d["title"]
    if "subtitle" in d:
        result+="{\\Large %s}\\\\[3em] \n" %d["subtitle"]
    result+="\\end{center}"
    if "editor" in d:
        result+="{\\large %s}\\\\ \n" %d["editor"]
    result+="\\end{titlepage}"
    result+="\\pagebreak \\tableofcontents \\listoffigures\\pagebreak\n"

    return result

class titlePage(templateParser, plugin):
    def __init__(self):
        plugin.__init__(self)
        templateParser.__init__(self, "Latex:TitlePage", fun=pTitlePage)

register_plugin(titlePage)
