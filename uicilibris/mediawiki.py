# -*- coding: utf-8 -*-
# 	$Id: $	
#
# mediawiki.py is part of the package uicilibris
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

"""
the module mediawiki aims to implement a few utilities to access mediawikis
and parse texts in mediawiki language.
"""

import cookielib, urllib2, urllib, sys, re, time
from BeautifulSoup import BeautifulSoup
import MultipartPostHandler

class MediawikiOpener:
    """
    a class to get and put data from and to a mediawiki; when
    authentification is required a login/password pair is managed
    """

    def __init__(self, baseUrl, login="", password=""):
        """
        the constructor
        @param baseUrl the address of the main page of the mediawiki
        @param login a login required for authentification (defaults to "")
        @param password the password which matches the previous login (defaults to "")
        """
        self.login=login
        self.password=password
        self.baseUrl=""
        self.host=re.match(r"^http://([^/]+).*", baseUrl).group(1)
        self.viewSourceUrl=""
        self.logged=False
        self.loginUrl=""
        self.getLoginUrl(baseUrl)
        self.opener=None
        self.getOpener()


    def getBase(self):
        """
        @return the base address of the mediawiki
        """
        return self.baseUrl
    
    def getHost(self):
        """
        @return the host of the mediawiki
        """
        return self.host

    def isValid(self):
        """
        @return True when the targeted website is most probably a mediawiki.
        """
        return self.opener != None and self.loginUrl != "" and self.viewSourceUrl != ""

    def getLoginUrl(self, initUrl=""):
        """
        @param initUrl an initial URL to get the features of a mediawiki
        
        sets self.loginUrl, the url of the mediawiki's login page;
        sets also self.viewSourceUrl, the url which allows one to
        view the source of the base page;
        finally, sets self.baseUrl, which is usable to build other urls.
        @return self.loginUrl
        """
        if self.loginUrl != "":
            return self.loginUrl
        req = urllib2.Request(url=initUrl)
        f = urllib2.urlopen(req)
        s=BeautifulSoup(f)
        li=s.find("li",attrs={"id":"pt-login"})
        if li:
            resultUrl=li.a["href"]
            try:
                self.loginUrl=re.findall("(^.*)&.*",resultUrl)[0]
            except:
                pass
        li=s.find("li", attrs={"id":"ca-viewsource"}) # the page cannot be modified
        if li:
            self.viewSourceUrl=li.a["href"]
        li=s.find("li", attrs={"id":"ca-edit"}) # the page cannot be modified
        if li:
            self.viewSourceUrl=li.a["href"]
        if self.viewSourceUrl != "":
            m=re.match(r"^(/[^/]+)/index.php.*", self.viewSourceUrl)
            if m:
                self.baseUrl="http://"+self.host+m.group(1)
        return self.loginUrl
                
    def getOpener(self):
        """
        Sets self.opener with an opener which embeds authentification
        assets incliding cookies.
        Eventually sets self.logged.
        """
        if self.login=="" or self.password=="":
            opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
            self.opener=opener
            return
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), MultipartPostHandler.MultipartPostHandler)
        f = opener.open('http://%s%s' %(self.host, self.loginUrl))
        s=BeautifulSoup(f)
        form=s.form
        action=form["action"]
        inp=form.find("input", attrs={"name":"wpLoginToken"})
        if inp:
            return self.genuineMediawikiOpener(inp, opener, action)
        else:
            return self.altMediawikiOpener(s, opener, self.loginUrl)

    def altMediawikiOpener(self, soup, opener, action):
        """
        @param soup a BeautifulSoup object
        @param opener an opener able to manage cookies
        @param action the URL to send the request of login
        @return a string denoting the success of the operation
        """
        userInput=None
        passInput=None
        for f in soup.findAll("form"):
            for i in f.findAll("input"):
                if userInput==None and "user" in i["name"]:
                    userInput=i
                if passInput==None and "pass" in i["name"]:
                    passInput=i
        if userInput!=None and passInput!=None:
            data={}
            data["remember"]="0"
            data["submit"]="Login"
            data[userInput["name"]]=self.login
            data[passInput["name"]]=self.password
            f = opener.open('http://%s%s' %(self.host,action),
                              urllib.urlencode(data))
            s=BeautifulSoup(f)
            self.opener=opener
            return "Alternative mediawiki login"

    def genuineMediawikiOpener(self, tokeninput, opener, action):
        """
        @param tokeninput a BeautifulSoup element <input>
        @param opener an opener able to manage cookies
        @param action the URL to send the request of login
        @return a string denoting the success of the operation
        """
        token=tokeninput["value"]
        data={}
        data["wpName"]=self.login
        data["wpPassword"]=self.password
        data["wpRemember"]="0"
        data["wpLoginAttempt"]="Connexion"
        data["wpLoginToken"]=token
        f = opener.open('http://%s%s' %(self.host,action),
                          urllib.urlencode(data))
        s=BeautifulSoup(f)
        li=s.find("li",attrs={"id":"pt-logout"})
        if li:
            self.logged=True
            self.opener=opener
            return "True mediawiki login"

    def open(self, address, encodedData=None):
        """
        a method to open a page in a mediawiki, with previously
        stored credentials
        @param address the url of the page to open
        @param encodedData a string in url-encoded format
        @result a BeautifulSoup object made from the server's response
        """
        if encodedData:
            f=self.opener.open(address, encodedData)
        else:
            f=self.opener.open(address)
        return BeautifulSoup(f)

    def pageWrite(self, pageTitle, contents):
        """
        writes some contents into a page of the mediawiki
        @param pageTitle the title of the page (unicode string)
        @param contents a unicode string to write into this page
        @return the page given by the mediawiki as a feedback, in a
        BeautifulSoup object
        """
        pageTitle=pageTitle.encode("utf-8")
        contents=contents.encode("utf-8")
        soup=self.open(self.baseUrl+"/index.php?title=%s&action=edit" %pageTitle)
        form=soup.find("form", attrs={"name":"editform"})
        # ============== gathering inputs ======================
        inputs=[]
        hidden=form.findAll("input", attrs={"type":"hidden"})
        inputs+=hidden
        checkboxes=form.findAll("input", attrs={"type":"checkbox"})
        inputs+=checkboxes
        submit=form.findAll("input", attrs={"type":"submit"})
        inputs+=submit
        allinputs=form.findAll("input")
        defaultInputs=[]
        for d in allinputs:
            if d not in inputs:
                defaultInputs.append(d)
        inputs+=defaultInputs
        # ================= getting textarea ========================
        ta = form.textarea
        # =======================================================
        # ================= sending contents ====================
        # =======================================================
        address="http://"+self.host+form.attrMap["action"]
        for c in checkboxes:
            c["value"]="0"
        for d in defaultInputs:
            if d["name"]=="wpSummary":
                d["value"]="modified by Uici Libris, date = %s" %time.asctime()
        data={}
        for i in inputs:
            if i not in submit and i.attrMap.has_key("name") and i.attrMap.has_key("value"):
                data[i["name"]]=i["value"]
        data["wpSave"]="Publier"
        data["wpTextbox1"]="%s\n" %contents
        return self.open(address, urllib.urlencode(data))

    def filePut(self, localFileName, remoteFileName):
        """
        uploads a file to the mediawiki
        @param localFileName the file to upload
        @param the name to give inside the wiki
        @return the page given by the mediawiki as a feedback, in a
        BeautifulSoup object
        """
        f=self.opener.open('%s%s' %(self.baseUrl, "/index.php/Special:Upload"))
        s=BeautifulSoup(f)
        form=s.form
        # BeautifulSoup provides Unicode strings, which must be
        # encoded to be accepted by MultipartPostHandler without problem
        actionUrl=form["action"].encode("utf-8")
        token=form.find("input", attrs={"id":"wpEditToken"})["value"].encode("utf-8")
        params = {"wpUploadFile": open(localFileName, "rb"),
                  "wpDestFile": remoteFileName,
                  "wpWatchthis": "0",
                  "wpIgnoreWarning": "1",
                  "wpEditToken": token,
                  "title": urllib.quote("Special:Upload"),
                  "wpUpload": urllib.quote("Upload File"),
                  "wpUploadDescription": "Automatic upload by Uicilibris, date = %s" %time.asctime()
                  }
        f=self.opener.open(actionUrl, params)
        return BeautifulSoup(f)

def linksInText(text):
    """
    @param text a well-formed mediawiki source
    @result a list of Wikilinks coming from a text grabbed from the source
    of a mediawiki.
    """
    return re.findall("\[\[([^\]]+)\]\]", text)
