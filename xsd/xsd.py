# xsd.py - python module for XML Schema

"""\ Given an XML Schema, build the trees of substitution groups. This is
another case of building a tree from individual edges, without prior knowledge
of the tree's root.

"""

import sys
import lxml.etree as et
from lxml import objectify

from x4b.tree import TreeSet 

#-------------------------------------------------------------------------------

def tag(nd):
    return et.QName(nd).localname

#-------------------------------------------------------------------------------

class SubstitutionGroups:
    """This class represents the set of "substitution group" trees in a schema.
    """
    def __init__(self, xsd_root):
        self.xsd_root = xsd_root
        self.ts = TreeSet()
        
        for nd in self.xsd_root:
            if 'substitutionGroup' in nd.attrib:
                head = nd.attrib['substitutionGroup']
                member = nd.attrib['name']
                self.ts.add_edge(head, member)
                
    def member_of(self, member, head):
        return self.ts.child_of(member, head)

    def heads(self):
        return self.ts.parents()

    def members(self):
        return self.ts.children()

    def __str__(self):
        return str(self.ts) 
    
#-------------------------------------------------------------------------------

class TypeDerivations:
    """This class represents the set of "type derivation" trees in a schema.
    """
    def __init__(self, xsd_root):
        self.xsd_root = xsd_root
        self.ts = TreeSet()
        
        for nd in self.xsd_root:
            if tag(nd) == 'complexType':
                type_name = nd.attrib['name']
                if tag(nd[0]) == 'complexContent' and \
                   tag(nd[0][0]) == 'extension':
                    k = nd[0][0]
                    base_type = k.attrib['base']
                    self.ts.add_edge(base_type, type_name)

    def __str__(self):
        return str(self.ts) 

    def traverse(self):
        # This returns an array of payloads
        return self.ts.traverse()

class XMLSchema:
    def __init__(self, filepath):
        self.filepath = filepath

        # Ignore comments
        p = et.XMLParser(remove_comments=True)
        self.root = objectify.parse(filepath, parser=p).getroot()
        self.sg = SubstitutionGroups(self.root)
        self.td = TypeDerivations(self.root)
    
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xsd filepath>')
        exit(-1)
    filepath = sys.argv[1]

    xsd = XMLSchema(filepath)
    print('Substitution groups:\n')
    print(xsd.sg)
    print()
    
    print('Type derivations tree:\n')
    print(xsd.td)
    print()

    print()
    print('Type derivations tree traversal:\n')
    xsd.td.traverse()