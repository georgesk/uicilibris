# (c) 2011      Georges Khaznadar (georgesk@ofset.org)
#
# purpose: implement a simple plugin system
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
#
#--------------------------------------------------
#
# this plugin system has been inspired by the page
# http://blog.movementarian.org/2008/07/pure-python-plugins.html
# thanks to John Levon

import pkgutil
import imp
import os

# define a list of paths to plugin sources
# paths = ["/usr/share/uicilibris/plugin_collection"]
paths = ["plugin_collection"]

# iterates through the paths and loads the available plugins
for loader, name, ispkg in pkgutil.iter_modules(paths):
    file, pathname, desc = imp.find_module(name, paths)
    imp.load_module(name, file, pathname, desc)
    
