#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 	$Id$
#
# url.py is part of the package uicilibris
#
# (c) 2011      Georges Khaznadar (georgesk@ofset.org)
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

"""
This file implements web access through a cache
"""

import urllib2, urllib, StringIO, time

class Cache:
    """
    a class to implement an Internet cache in memory. Get the unique cache as
    Cache.cache()
    """

    theCache=None

    def __init__(self):
        """
        the constructor creates the first and only cache
        """
        if Cache.theCache==None:
            self.dict={}
            Cache.theCache=self
        else:
            raise IndexError, "no more than one instantiation of Cache can exist"

    def cache():
        if Cache.theCache:
            return Cache.theCache
        else:
            Cache.theCache=Cache()
            return Cache.theCache
        
    cache=staticmethod(cache)

    def toCache(url, data, contents):
        """
        @param url a valid URL
        @param data a data/url-encoded strig, or None
        @param contents a string
        """
        Cache.theCache.dict[(url, data)]=contents
    toCache=staticmethod(toCache)

    def fromCache(url, data):
        """
        @param url a valid URL
        @param data a data/url-encoded strig, or None
        @return a file-like objet giving access to the contents, or None
        """
        if (url,data) in Cache.theCache.dict.keys():
            return StringIO.StringIO(Cache.theCache.dict[(url, data)])
        else:
            return None
    fromCache=staticmethod(fromCache)

def urlopen(url, data=None):
    """
    @param url a valid URL
    @param data are url-encoded data to post
    @result a file-like object giving access to the URL's contents
    """
    r=Cache.fromCache(url, data)
    if r==None:
        time.sleep(0.2) # do not fire too fast, to avoid greylisting.
        headers = { 'User-Agent' : "Mozilla/5.0 (X11; Linux i686; rv:7.0.1) Gecko/20100101 Firefox/7.0.1",
                    'Pragma' : "no-cache",
                    'Referer' : "http://packages.debian.org/sid/uicilibris"
                    }
        nbtries=8
        finished=False
        contentsOK=True
        while not finished:
            try:
                r =  urllib2.urlopen(urllib2.Request(url, data=data, headers=headers), timeout=1)
                finished=True
                r=StringIO.StringIO(r.read())
            except Exception, e:
                nbtries=nbtries-1
                print "There was an error: %r, still %d tries" %(e, nbtries)
                if nbtries==0:
                    finished=True
                    contentsOK=False
                    r=StringIO.StringIO("")
        if contentsOK:
            # cache the data if the url is open
            nbtries=8
            finished=False
            while not finished:
                try:
                    Cache.toCache(url, data, r.read())
                    r.seek(0)
                    finished=True
                except Exception, e:
                    nbtries=nbtries-1
                    print "There was an error: %r, still %d tries" %(e, nbtries)
                    if nbtries==0:
                        finished=True
    return r

def quote_plus(text):
    """
    @param text
    @return the same text with url_quoted encoding
    """
    return urllib.quote_plus(text)

def urlencode(data):
    """
    @param data a dictioanry of keys/values
    @return a string in data/url-encoded format
    """
    return urllib.urlencode(data)


dummy=Cache()

if __name__=="__main__":
    dummy=Cache()
    Cache.toCache("a","b","the contents")
    r = Cache.fromCache("a", "b")
    if r:
        print r.read()
    else:
        print "noting cached"
    r = Cache.fromCache("a", "c")
    if r:
        print r.read()
    else:
        print "noting cached"
    
    
    
