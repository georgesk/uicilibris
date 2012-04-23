# the plugin putRef is part of the package uicilibris
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

class putRef(templateParser, plugin):
    def __init__(self):
        plugin.__init__(self)
        templateParser.__init__(self, "Latex:putRef", fun=lambda x: "")

register_plugin(putRef)
