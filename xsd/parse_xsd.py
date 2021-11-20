# parse_xsd.py - parse an XML Schema file (assumed to be valid)

import sys
import json
import lxml.etree as et
from lxml import objectify

#-------------------------------------------------------------------------------

def tag(nd):
    return et.QName(nd).localname

#-------------------------------------------------------------------------------

class XsdAppinfo:
    """Specifies information to be used by applications within an annotation
    element.

    Content: ({any})*

    """
    def __init__(self, source=None, content=None):
        self.source = source
        self.content = content

    @classmethod
    def build(cls, xsd, nd):
        # Attributes
        source = nd.attrib['source'] if 'source' in n.attrib else None
        
        # Sub-elements
        content = nd.text.strip()

        return cls(source, content)

#-------------------------------------------------------------------------------

class XsdDocumentation:
    """Specifies information to be used by applications within an annotation
    element.

    Content: ({any})*

    """
    def __init__(self, source=None, lang=None, content=None):
        self.source = source
        self.lang = lang
        self.content = content

    @classmethod
    def build(cls, xsd, nd):
        # Attributes
        source = nd.attrib['source'] if 'source' in n.attrib else None
        lang = nd.attrib['lang'] if 'lang' in n.attrib else None
        
        # Sub-elements
        content = nd.text.strip()

        return cls(source, content)

#-------------------------------------------------------------------------------

class XsdAnnotation:
    """Defines an annotation.

    Content: (appinfo | documentation)*
    """
    def __init__(self, id_=None, appinfos=None, docs=None):
        self.id_ = id_

        self.appinfos = []
        if appinfos is not None:
            self.appinfos = appinfos

        self.docs = []
        if docs is not None:
            self.docs = docs

    @classmethod
    def build(cls, xsd, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in n.attrib else None
        
        # Sub-elements
        appinfos = []
        docs = []
        for k in nd:
            if tag(k) == 'appinfo':
                appinfos.append(XsdAppinfo.build(xsd, nd))
            elif tag(k) == 'documentation':
                docs.append(XsdDocumentation.build(xsd, nd))

        return cls(id_, appinfos, docs)

#-------------------------------------------------------------------------------

class XsdGroup:
    """This class represents an XSD group."""
    def __init__(self, id_=None, name=None, minOccurs=None, maxOccurs=None,
                 annotation=None, elems=None):
        self.id_ = id_
        self.name = name
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, xsd, nd):
        """nd is an eTree node with tag 'xs:group'.

        Content: (annotation?, (all | choice | sequence))
        """
        # Reference to a group declared in this schema
        ref = nd.attrib['ref'] if 'ref' in n.attrib else None

        if ref is not None:
            return xsd.groups[ref]

        # Group definition, attributes
        id_ = nd.attrib['id'] if 'id' in n.attrib else None
        name = nd.attrib['name'] if 'name' in n.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in n.attrib else None
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in n.attrib else None

        # Elements
        elems = []
        note = None
        for k in nd:
            if tag(k) == 'annotation':
                note = XsdAnnotation.build(xsd, nd)
            if tag(k) == 'all':
                elems.extend(XsdAll.build(xsd, nd))
            elif tag(k) == 'choice':
                elems.extend(XsdChoice.build(xsd, nd))
            elif tag(k) == 'sequence':
                elems.extend(XsdSequence.build(xsd, nd))
            else:
                raise RuntimeError(f'Unexpected tag "{tag(k)}" inside an xs:group')

#-------------------------------------------------------------------------------

class XMLSchema:
    """This class represents an entire XML Schema."""
    def __init__(self, filepath):
        self.filepath = filepath
        self.types = {}
        self.elems = {}
        self.groups = {}

        # Ignore comments
        p = et.XMLParser(remove_comments=True)
        self.root = objectify.parse(filepath, parser=p).getroot()

        # Get groups for future reference
        for nd in self.root:
            if tag(nd) != 'group':
                continue
            g = XsdGroup.build(self, nd)
            self.groups[g.name] = g

        # Parse schema
        for nd in self.root:
            if tag(nd) == 'group':
                continue
            parse_node(nd)

    def dictify(self):
        return {
            'types': {k: v.dictify() for k, v in self.types.items()},
            'elems': {k: v.dictify() for k, v in self.elems.items()},
        }

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xsd filepath>')
        exit(-1)
    filepath = sys.argv[1]

    xsd = XMLSchema(filepath)
    # print(xsd)
