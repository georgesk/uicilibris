# the plugin isn_creditphoto is part of the package uicilibris
# -*- coding: utf-8 -*-
#
# (c) 20113      Georges Khaznadar (georgesk@ofset.org)
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

def pCreditPhoto(d):
    result="~\\\\[1em] \\textbf{[[%s|%s]]}" %(d["page"],d["ancre"])
    if "complement" in d and len(d["complement"])>0:
        result+="\\textbf{%s}\\\\" %d["complement"]
    result+=" \\indent \\copyright  %s, licence : %s\\\\" %(d["copyright"],d["licence"],)
    if "lieu" in d and len(d["lieu"])>0:
        result+=" \\indent %s" %(d["lieu"],)
    if "lien" in d and len(d["lien"])>0:
        result+=", voir \\href{%s}{%s}" %(d["lien"],d["ancrelien"])
    else:
        result+="."
    return result

class isn_creditphoto(templateParser, plugin):
    def __init__(self):
        plugin.__init__(self)
        templateParser.__init__(self, "ISN:creditphoto", fun=pCreditPhoto)

register_plugin(isn_creditphoto)
