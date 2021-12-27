# dephrase.py - 

"""The <phrase> element in the W3C documents.

When diff is "add" or "chg", the whole <phrase> hierarchy (a mixed content
model) replaces the <phrase> node at that point in the XML tree.

<phrase diff="chg">A list of current W3C publications.</phrase>
<phrase diff="add">This is a W3C Recommendation.</phrase>

Inside a mixed content model:

<p>An XML Schema consists of information items (as defined in <bibref
ref="ref-xmlinfo"/>), and furthermore may specify augmentations to those items
and their descendants. <phrase diff="add"><termdef term="post-schema-validation
infoset" id="key-psvi">We refer to the augmented infoset which results from
conformant processing as defined in this specification as the
<term>post-schema-validation infoset</term>, or PSVI</termdef></phrase>.</p>

<p>An... <bibref>, ... descendants. <phrase> . </p>
                                        |
                                   <termdef>We refer... <term>, or PSVI</termdef>

When diff is "del", the <phrase> element (and its sub-tree) can be either
removed or ignored.

<phrase diff="del">the simple version</phrase>

"""

import os
import re
import sys

#-------------------------------------------------------------------------------
    
def dephrase(s):
    deleting = False
    out = ''
    pending = s
    pat = re.compile('<phrase diff="|</phrase>', re.MULTILINE)
    while True:
        m = re.search(pat, s)
        if m is None:
            # Output pending text, over.
            out += s
            return out
        
        # Keep intermediate text, pending output
        pending = s[:m.start()]
        s = s[m.start() + len(m.group()):]

        if deleting:
            if m.group().startswith('<phrase'):
                cnt += 1
            else:
                # </phrase>
                cnt -= 1
                if cnt == 0:
                    deleting = False
        else:
            out += pending
            if m.group().startswith('<phrase'):
                cmd = s[:3]
                s = s[5:]  # closing double quote plus &gt;
                if cmd == 'del':
                    deleting = True
                    cnt = 1

def write(s, label=None):
    base, _ = os.path.splitext(filepath)
    label = '' if label is None else f'.{label}'
    outpath = f'{base}{label}.xml'
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(s)
    
#-------------------------------------------------------------------------------
    
def dephrase_file(filepath):
    with open(filepath) as f:
        s = f.read()

    out = dephrase(s)
    print(out)

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xml filepath>')
        exit(-1)
    filepath = sys.argv[1]

    dephrase_file(filepath)
