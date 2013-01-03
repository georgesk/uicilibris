# -*- coding: utf-8 -*-
# 	$Id: uiciautotemplates $ 
#
# uiciautotemplates.py is part of the package uicilibris 
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

import re
from wikiParser import syntax_error

def collectAutoTemplates(lines):
    """
    collect templates from a list of lines
    @param lines a list of strings
    @result a dictionary of auto_templates
    """
    autotemplatebuffer = []
    autotemplate=[]
    autotemplatemode = False
    opening=""

    for line in lines:  
        (line, _autotemplatemode) = get_autotemplatemode(line, autotemplatemode)
        if _autotemplatemode and not autotemplatemode: #autotemplate mode was turned on
            autotemplatebuffer = []
        elif not _autotemplatemode and autotemplatemode: #autotemplate mode was turned off
            opening+="\n"+expand_autotemplate_opening(autotemplatebuffer, autotemplate)
        autotemplatemode = _autotemplatemode

        if autotemplatemode:
            autotemplatebuffer.append(line)
    return opening

def expand_autotemplate_opening(templatebuffer, autotemplate):
    """
    expands the output code to insert an automated template
    @param templatebuffer
    @param autotemplate
    """
    my_autotemplate = parse_autotemplate(templatebuffer)
    the_autotemplate = unify_autotemplates([autotemplate, my_autotemplate])

    opening = expand_autotemplate_gen_opening(the_autotemplate)
    return opening

def expand_autotemplate_gen_opening(autotemplate):
    """
    @param autotemplate (list)
        the specification of the autotemplate in the form of a list of tuples
    @return (string)
        the string the with generated latex code
    """
    out = []
    for item in autotemplate:
        out.append('\\%s%s' % item)
    return '\n'.join(out)

def unify_autotemplates(autotemplates):
    usepackages = {} #packagename : options

    merged = []
    for template in autotemplates:
        for command in template:
            if command[0] == 'usepackage':
                (name, options) = parse_usepackage(command[1])
                usepackages[name] = options
            else:
                merged.append(command)

    autotemplate = []
    for (name, options) in usepackages.items():
        if options != None and options.strip() != '':
            string = '%s{%s}' % (options, name)
        else:
            string = '{%s}' % name
        autotemplate.append(('usepackage', string))

    autotemplate.extend(merged)

    return autotemplate

def parse_autotemplate(autotemplatebuffer):
    """
    @param autotemplatebuffer (list)
        a list of lines found in the autotemplate section
    @return (list)
        a list of tuples of the form (string, string) with \command.parameters pairs
    """
    result=[]

    for line in autotemplatebuffer:
        if len(line.lstrip())==0: #ignore empty lines
            continue
        if len(line.lstrip())>0 and line.lstrip().startswith('%'): #ignore lines starting with % as comments
            continue

        tokens = line.split('=', 1)
        if len(tokens)<2:
            syntax_error('lines in the autotemplate section have to be of the form key=value', line)

        result.append((tokens[0], tokens[1]))

    return result

def get_autotemplatemode(line, autotemplatemode):
    """
    detects the auto template mode
    @param line a line to be tested; will be eventualy stripped
    @param autotemplatemode to get the result of the detection
    """
    autotemplatestart = re.compile(r'^<\s*\[\s*autotemplate\s*\]')
    autotemplateend = re.compile(r'^\[\s*autotemplate\s*\]\s*>')
    if not autotemplatemode and autotemplatestart.match(line)!=None:
        line = autotemplatestart.sub('', line)
        return (line, True)
    elif autotemplatemode and autotemplateend.match(line)!=None:
        line = autotemplateend.sub('', line)
        return (line, False)
    else:
        return (line, autotemplatemode)

def parse_usepackage(usepackage):
    """
    @param usepackage (str)
        the unparsed usepackage string in the form [options]{name}
    @return (tuple)
        (name(str), options(str))
    """

    p = re.compile(r'^\s*(\[.*\])?\s*\{(.*)\}\s*$')
    m = p.match(usepackage)
    g = m.groups()
    if len(g)<2 or len(g)>2:
        syntax_error('usepackage specifications have to be of the form [%s]{%s}', usepackage)
    elif g[1]==None and g[1].strip()!='':
        syntax_error('usepackage specifications have to be of the form [%s]{%s}', usepackage)
    else:
        options = g[0]
        name = g[1].strip()
        return (name, options)

def parse_bool(string):
    boolean = False

    if string == 'True' or string == 'true' or string == '1':
        boolean = True
    elif string == 'False' or string == 'false' or string =='0':
        boolean = False
    else:
        syntax_error('Boolean expected (True/true/1 or False/false/0)', string)

    return boolean

if __name__ == "__main__":
    text=u"""\
{{pageMoissonnable}}
<[ autotemplate ]
usepackage=[c++]{lstlistings}
[ autotemplate ] >

* [[ISN Représentation binaire]]
&lt;syntaxhighlight lang="php">
&lt;?php
    $v = "string";    // sample initialization
?>
html text
&lt;?
    echo $v;         // end of php code
?>
&lt;/syntaxhighlight>

"""
    print text
    text=text.split("\n")
    print (collectAutoTemplates(text))

