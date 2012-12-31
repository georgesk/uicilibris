#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 	$Id: uicimd5.py
#
# uicimd5.py is part of the package uicilibris
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

import md5

def digest(s):
    """
    @param s a unicode string or a simple string
    @return a hash code
    """
    if isinstance(s, unicode):
        s=s.encode("utf-8")
    s=s.encode("string-escape")
    return md5.new(s).hexdigest()

if __name__=="__main__":
    s=u"éèàçô"
    print s
    print digest(s)
