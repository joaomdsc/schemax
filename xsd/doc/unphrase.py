# w3c.py - convert W3C recommendations in HTML format to a Word file

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
import lxml.etree as et
from lxml import objectify

#-------------------------------------------------------------------------------

class XmlDocument:

    def do_phrase(self, nd, i, parent):
        """nd is a <phrase> node, and parent is the parent node.

        nd is the i-th child of parent.

        <p>good morning 
            <xyz>abc</xyz>toto
            <phrase>...</phrase>night
            <p>...</p>good night
        </p>

        Concat (parent.text|prev_sibling.tail) with phrase.text

        for k in phrase.kids: append k to parent (or maybe append_sibling),
        after prev_sibling

        Concat  (parent.text|prev_sibling.tail) with phrase.tail

        """
        print(f'parent={parent.tag}, i={i}, nd={nd.tag}')
        
        # Attributes: diff == add/chg: keep it, del: ignore it
        diff = nd.attrib.get('diff')
        if diff is not None and diff not in ['chg', 'add', 'del']:
            m = f'Unexpected diff attribute value "{diff}" in a <phrase> element'
            raise RuntimeError(m)

        if diff == 'del':
            return
        
        # Text before any eventual sub-element
        if nd.text is not None:
            print(f'text="{nd.text}"')
            if i == 0:
                if parent.text is None:
                    parent.text = nd.text
                else:
                    parent.text += nd.text
            else:
                if parent[i-1].text is None:
                    parent[i-1].text = nd.text
                else:
                    parent[i-1].text += nd.text

        last = parent
        if len(nd) != 0:
            # Re-attach child nodes on the parent
            for j, k in enumerate(nd):
                parent.insert(i+j, k)
                last = parent[i+j]

        if nd.tail is not None:
            print(f'last={last.tag}')
            if last.tail is None:
                last.tail = nd.tail
            else:
                last.tail += nd.tail

    #---------------------------------------------------------------------------

    def look_for(self, nd):
        """<spec> is the toplevel element in the XML tree."""

        for i, k in enumerate(nd):
            if k.tag == 'phrase':
                self.do_phrase(k, i, nd)
            else:
                self.look_for(k)

        # Remove all <phrase> elements
        for k in [k for k in nd if k.tag == 'phrase']:
            nd.remove(k)

    #---------------------------------------------------------------------------
    
    def __init__(self, filepath):
        self.filepath = filepath
        
        # Parse XML file, ignoring comments
        p = et.XMLParser(remove_comments=True)
        self.root = objectify.parse(filepath, parser=p).getroot()

        # Get the document contents
        self.look_for(self.root)
        self.write('unphrased')

    def write(self, label=None):
        base, _ = os.path.splitext(self.filepath)
        label = '' if label is None else f'.{label}'
        outpath = f'{base}{label}.xml'
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(et.tostring(self.root, method='c14n2').decode())
    
#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xml filepath>')
        exit(-1)
    filepath = sys.argv[1]

    d = XmlDocument(filepath)
