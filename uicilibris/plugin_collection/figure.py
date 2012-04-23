# the plugin figure is part of the package uicilibris
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
import sys
import wikiParser

def pFigure(d):
    result="\\begin{figure}[h!]\n\\begin{center}"
    if "caption" in d and "label" in d:
        # !! the space after \\label{%s}%s is mandatory to avoid "}}"
        # in some cases
        result+="\n\\caption{\\label{%s}%s }\\vspace{0.5em}" %(d["label"], d["caption"])
    elif "caption" in d:
        result+="\n\\caption{%s}\\vspace{0.5em}" %d["caption"]
    if "schematic" in d and d["schematic"]:
        wikiParser.wParser.registerImage("Schematic-%s" %d["schematic"])
        result+="\n\\includegraphics[width=0.4\\textwidth, height=0.3\\textwidth, keepaspectratio]{Schematic-%s}" %d["schematic"]
    if "pic" in d and d["pic"]:
        wikiParser.wParser.registerImage("Pic-%s" %d["pic"])
        result+="\n\\includegraphics[width=0.4\\textwidth, height=0.3\\textwidth, keepaspectratio]{Pic-%s}" %d["pic"]
    result +="\n\\end{center}\n\\end{figure}\n"
    result=result.replace("_",'-') # to protect Latex. Don't use image names with underscores
    return result

class figure(templateParser, plugin):
    def __init__(self):
        plugin.__init__(self)
        templateParser.__init__(self, "Latex:Figure", fun=pFigure)

register_plugin(figure)
