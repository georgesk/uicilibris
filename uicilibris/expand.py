#!/usr/bin/env python
# 	$Id: expand.py 19 2011-08-09 16:09:53Z georgesk $	
#
# expand.py is part of the package uicilibris
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

import random, re, string, hashlib, sys

def syntax_error(message, code):
    print >>sys.stderr, 'syntax error in [expand]: %s' % message
    print >>sys.stderr, '\tcode:\n%s' % code
    sys.exit(-3)

def md5hex(string):
    return hashlib.md5(string).hexdigest()

def expand_code_make_defverb(content, name):
    return "\\defverbatim[colored]\\%s{\n%s\n}" % (name, content)

def expand_code_make_lstlisting(content, options):
    return "\\begin{lstlisting}%s%s\\end{lstlisting}" % (options, content)

def expand_code_search_escape_sequences(code):
    open = '1'
    close = '2'
    while code.find(open) != -1 or code.find(close) != -1:
        open = open + chr(random.randint(48,57))
        close = close + chr(random.randint(48,57))

    return (open,close)

def expand_code_tokenize_anims(code):
    #escape
    (esc_open, esc_close) = expand_code_search_escape_sequences(code)
    code = code.replace('\\[', esc_open)
    code = code.replace('\\]', esc_close)

    p = re.compile(r'\[\[(?:.|\s)*?\]\]|\[(?:.|\s)*?\]')
    non_anim = p.split(code)
    anim = p.findall(code)
    
    #unescape
    anim = map(lambda s: s.replace(esc_open, '\\[').replace(esc_close, '\\]'), anim)
    non_anim = map(lambda s: s.replace(esc_open, '[').replace(esc_close, ']'), non_anim)

    return (anim, non_anim)

def expand_code_parse_overlayspec(overlayspec):
    overlays = []

    groups = overlayspec.split(',')
    for group in groups:
        group = group.strip()
        if group.find('-')!=-1:
            nums = group.split('-')
            if len(nums)<2:
                syntax_error('overlay specs must be of the form <(%d-%d)|(%d), ...>', overlayspec)
            else:
                try:
                    start = int(nums[0])
                    stop = int(nums[1])
                except ValueError:
                    syntax_error('not an int, overlay specs must be of the form <(%d-%d)|(%d), ...>', overlayspec)

                overlays.extend(range(start,stop+1))
        else:
            try:
                num = int(group)
            except ValueError:
                syntax_error('not an int, overlay specs must be of the form <(%d-%d)|(%d), ...>', overlayspec)
            overlays.append(num)
    
    #make unique
    overlays = list(set(overlays))
    return overlays

def expand_code_parse_simpleanimspec(animspec):
    #escape
    (esc_open, esc_close) = expand_code_search_escape_sequences(animspec)
    animspec = animspec.replace('\\[', esc_open)
    animspec = animspec.replace('\\]', esc_close)

    p = re.compile(r'^\[<([0-9,\-]+)>((?:.|\s)*)\]$')
    m = p.match(animspec)
    if m != None:
        overlays = expand_code_parse_overlayspec(m.group(1))
        code = m.group(2)
    else:
        syntax_error('specification does not match [<%d>%s]', animspec)

    #unescape code
    code = code.replace(esc_open, '[').replace(esc_close, ']')
    
    return [(overlay, code) for overlay in overlays]


def expand_code_parse_animspec(animspec):
    if len(animspec)<4 or not animspec.startswith('[['):
        return ('simple', expand_code_parse_simpleanimspec(animspec))
    
    #escape
    (esc_open, esc_close) = expand_code_search_escape_sequences(animspec)
    animspec = animspec.replace('\\[', esc_open)
    animspec = animspec.replace('\\]', esc_close)
    
    p = re.compile(r'\[|\]\[|\]')
    simple_specs = map(lambda s: '[%s]'%s, filter(lambda s: len(s.strip())>0, p.split(animspec)))

    #unescape
    simple_specs = map(lambda s: s.replace(esc_open, '\\[').replace(esc_close, '\\]'), simple_specs)
    parsed_simple_specs = map(expand_code_parse_simpleanimspec, simple_specs)
    #print parsed_simple_specs
    unified_pss = []
    for pss in parsed_simple_specs:
        unified_pss.extend(pss)
    #print unified_pss
    return ('double', unified_pss)
    

def expand_code_getmaxoverlay(parsed_anims):
    max_overlay = 0
    for anim in parsed_anims:
        for spec in anim:
            if spec[0] > max_overlay:
                max_overlay = spec[0]
    return max_overlay

def expand_code_getminoverlay(parsed_anims):
    min_overlay = sys.maxint
    for anim in parsed_anims:
        for spec in anim:
            if spec[0] < min_overlay:
                min_overlay = spec[0]
    if min_overlay == sys.maxint:
        min_overlay = 0
    return min_overlay


def expand_code_genanims(parsed_animspec, minoverlay, maxoverlay, type):
    #get maximum length of code
    maxlen=0
    if type=='double':
        for simple_animspec in parsed_animspec:
            if maxlen < len(simple_animspec[1]):
                maxlen = len(simple_animspec[1])
    
    out = []
    fill = ''.join([' ' for i in xrange(0, maxlen)])
    for x in xrange(minoverlay,maxoverlay+1):
        out.append(fill[:])

    for simple_animspec in parsed_animspec:
        out[simple_animspec[0]-minoverlay] = simple_animspec[1]

    return out

def expand_code_getname(code):
    asciihextable = string.maketrans('0123456789abcdef',\
                                     'abcdefghijklmnop')
    d = md5hex(code).translate(asciihextable)
    return d

def expand_code_makeoverprint(names, minoverlay):
    out = ['\\begin{overprint}\n']
    for (index, name) in enumerate(names):
        out.append('  \\onslide<%d>\\%s\n' % (index+minoverlay, name))
    out.append('\\end{overprint}\n')

    return ''.join(out)

def expand_code_get_unique_name(defverbs, code, lstparams):
    """generate a collision free entry in the defverbs-map and names-list"""
    name = expand_code_getname(code)
    expanded_code = expand_code_make_defverb(expand_code_make_lstlisting(code, lstparams), name)
    rehash = ''
    while name in defverbs and defverbs[name] != expanded_code:
        rehash += char(random.randint(65,90)) #append a character from A-Z to rehash value
        name = expanded_code_getname(code + rehash)
        expanded_code = expand_code_make_defverb(expand_code_make_lstlisting(code, lstparams), name)

    return (name, expanded_code)

   
def expand_code_segment(result, codebuffer, state):
    #treat first line as params for lstlistings
    lstparams = codebuffer[0]
    codebuffer[0] = ''
 
    #join lines into one string
    code = ''.join(codebuffer)
    #print code

    #tokenize code into anim and non_anim parts
    (anim, non_anim) = expand_code_tokenize_anims(code)
    #print anim
    #print non_anim
    if len(anim)>0:
        #generate multiple versions of the anim parts
        parsed_anims = map(expand_code_parse_animspec, anim)
        #print parsed_anims
        max_overlay = expand_code_getmaxoverlay(map(lambda x: x[1], parsed_anims))
        #if there is unanimated code, use 0 as the starting overlay
        if len(non_anim)>0:
            min_overlay = 1
        else:
            min_overlay = expand_code_getminoverlay(map(lambda x: x[1], parsed_anims))
        #print min_overlay
        #print max_overlay
        gen_anims = map(lambda x: expand_code_genanims(x[1], min_overlay, max_overlay, x[0]), parsed_anims)
        #print gen_anims
        anim_map = {}
        for i in xrange(0,max_overlay-min_overlay+1):
            anim_map[i+min_overlay] = map(lambda x: x[i], gen_anims)
        #print anim_map
    
        names = []
        for overlay in sorted(anim_map.keys()):
            #combine non_anim and anim parts
            anim_map[overlay].append('')
            zipped = zip(non_anim, anim_map[overlay])
            mapped = map(lambda x: x[0] + x[1], zipped)
            code = ''.join(mapped)
            
            #generate a collision free entry in the defverbs-map and names-list
            (name, expanded_code) = expand_code_get_unique_name(state.defverbs, code, lstparams)

            #now we have a collision free entry, append it
            names.append(name)
            state.defverbs[name] = expanded_code
        
        #append overprint area to result
        overprint = expand_code_makeoverprint(names, min_overlay)
        result.append(overprint)
    else:
        #we have no animations and can just put the defverbatim in
        #remove escapings
        code = code.replace('\\[', '[').replace('\\]', ']')
        (name, expanded_code) = expand_code_get_unique_name(state.defverbs, code, lstparams)  
        state.defverbs[name] = expanded_code
        result.append('\n\\%s\n' % name)

    #print '----'
    return

def expand_code_defverbs(result, state):
        result[state.code_pos] = result[state.code_pos] + '\n'.join(state.defverbs.values()) + '\n'
        state.defverbs={}

