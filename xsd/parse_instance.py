# parse_instance.py - read/parse a BPMN 2.0 XML file, using the XML Schema

"""\
This code reads and parses an XML file, guided by the knowldege of its
schema. 

Note: class inheritance must avoid forward references.

"""

import os
import sys
import json
import lxml.etree as et

import Semantic as sem

#-------------------------------------------------------------------------------

def tag(nd):
    return et.QName(nd).localname

def py_bool(b):
    return b == 'true'

#-------------------------------------------------------------------------------

class definitions():
    def __init__(self, imports=None, extensions=None, rootElements=None):
        self.imports = imports
        self.extensions = extensions
        self.rootElements = rootElements

    @classmethod
    def build(cls, xsd, nd):
        # Sub-elements
        # nodes = [k for k in nd if tag(k) == 'import']
        # imports = [sem.tImport.build(xsd, k) for k in nodes]
        
        nodes = [k for k in nd if tag(k) == 'extension']
        extensions = [tExtension.build(xsd, k) for k in nodes]

        # rootElement is the head of a substitution group, so here we can have
        # a list of many different types. The types may eventually be repeated,
        # so we can't use a dict, instead we create an array of (type name,
        # type class) couples.
        nodes = [k for k in nd if tag(k) in sem.members['rootElement']]
        rootElements = [(tag(k), sem.klasses[tag(k)].build(xsd, k)) for k in nodes]

        k = next((k for k in nd if tag(k) == 'BPMNDiagram'), None)
        if k is not None:
            print('"BPMNDiagram" element not implemented', file=sys.stderr)

        k = next((k for k in nd if tag(k) == 'relationship'), None)
        if k is not None:
            print('"relationship" element not implemented', file=sys.stderr)

        # return cls(imports=imports, extensions=extensions, rootElements=rootElements)
        return cls(extensions=extensions, rootElements=rootElements)

    def dictify(self):
        d = {}
        # if len(self.imports) > 0:
        #     d['imports'] =[x.dictify() for x in self.imports]
        if len(self.extensions) > 0:
            d['extensions'] =[x.dictify() for x in self.extensions]
        if len(self.rootElements) > 0:
            d['rootElements'] = [(k, v.dictify()) for k, v in self.rootElements]
        return d

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

    def attrs(self):
        return {}

    def sub_elems(self):
        nodes = []
        for x in self.extensions:
            nodes.append(x.to_xml())
        for k, v in self.rootElements:
            nodes.append(v.to_xml())
        return nodes

    def to_xml(self):
        """Return self as an XML (etree) element"""
        nd = et.Element(sem.semns(self.__class__.__name__), nsmap=sem.nsmap)
        # Attributes
        nd.attrib.update(self.attrs())
        # Elements
        for k in self.sub_elems():
            nd.append(k)
        return nd

#-------------------------------------------------------------------------------

def parse_instance(filepath):
    root = et.parse(filepath).getroot()

    # I'm reading a BPMN file, so root is a <semantic:definitions> element.
    defs = definitions.build(None, root)

    # Re-create an XML tree form the parsed data
    out_root = defs.to_xml()
    s = et.tostring(out_root, xml_declaration=True, encoding='utf-8',
                    standalone=True, pretty_print=True).decode()
    
    # Output file path: drop the original dirname, keep the file basename
    _, tail = os.path.split(filepath)
    base, _ = os.path.splitext(tail)
    outpath = f'{base}.xml'
    
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(s)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xml filepath>')
        exit(-1)
    filepath = sys.argv[1]
    
    parse_instance(filepath)
