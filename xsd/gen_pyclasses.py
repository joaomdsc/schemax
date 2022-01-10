# gen_pyclasses.py - python module for XML Schema

"""Given an XML Schema, generate source code for the python classes that can
parse a conforming instance document. No validation will be performed by the
generated code, the document is assumed to be valid.

"""

import os
import sys
import json
from keyword import iskeyword
import builtins
import lxml.etree as et
from lxml import objectify

from x4b.tree import TreeSet
from xsd import SubstitutionGroups
from schemax.pyclass.pyclass import PyArg
from schemax.pyclass.pyclass_xsd import PyClassXsd, PyModuleXsd

#-------------------------------------------------------------------------------

def tag(nd):
    return et.QName(nd).localname

#-------------------------------------------------------------------------------

builtins_list = dir(builtins)

def protect(name):
    """Change 'name' to avoid keywords and builtins.

    Many XML grammars include an "id" element, for example, but this conflicts
    with python's 'id' builtin. To avoid these kinds of congflicts, we append an
    underscore to the name.

    """

    return f'{name}_' if iskeyword(name) or name in builtins_list else name

#-------------------------------------------------------------------------------

class XsdAttribute:
    def __init__(self, default=None, fixed=None, form=None, id_=None,
                 name=None, ref=None, type_=None, use=None):
        self.default = default
        self.fixed = fixed
        self.form = form
        self.id_ = id_
        self.name = name
        self.ref = ref
        self.type_ = type_
        self.use = use

        type_map = {
            'xsd:anyURI': str,
            'xsd:boolean': bool,
            'xsd:ID': str,
            'xsd:IDREF': str,
            'xsd:int': int,
            'xsd:integer': int,
            'xsd:NMTOKEN': str,
            'xsd:QName': str,
            'xsd:string': str,
            'xsd:token': str,
        }

        # All the attribute types are restrictions on strings. The only thing
        # we need to know is whether we need specific type python conversions
        # (int, bool) when extracting the data from the XML tree (in the
        # generated code).
        self.attr_type = type_map[self.type_] if self.type_ in type_map else str
    
    @classmethod
    def build(cls, nd):
        # Attributes
        default = nd.attrib['default'] if 'default' in nd.attrib else None
        fixed = nd.attrib['fixed'] if 'fixed' in nd.attrib else None
        form = nd.attrib['form'] if 'form' in nd.attrib else None
        id_ = nd.attrib['id'] if 'id_' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        ref = nd.attrib['ref'] if 'ref' in nd.attrib else None
        type_ = nd.attrib['type'] if 'type' in nd.attrib else None
        use = nd.attrib['use'] if 'use' in nd.attrib else None
        
        return cls(default=default, fixed=fixed, form=form, id_=id_, name=name,
                   ref=ref, type_=type_, use=use)

    def dictify(self):
        d = {}
        if self.default is not None:
            d['default'] = self.default
        if self.fixed is not None:
            d['fixed'] = self.fixed
        if self.form is not None:
            d['form'] = self.form
        if self.id_ is not None:
            d['id'] = self.id_
        if self.name is not None:
            d['name'] = self.name
        if self.ref is not None:
            d['ref'] = self.ref
        if self.type_ is not None:
            d['type'] = self.type_
        if self.use is not None:
            d['use'] = self.use
        if self.default is not None:
            d['default'] = self.default
        return d

#-------------------------------------------------------------------------------

class XsdElement:
    """This class represents an XML Schema Element.

    It represents both toplevel elements in the schema, and elements defined in
    extension sequences. An element has either a name and a type, or it has a
    reference to another element (through the "ref" attirbute).

    """
    def __init__(self, elem_tag, maxOccurs=None, minOccurs=None, name=None,
                 ref=None, type_=None, subst_grp=None):
        # Some elements have name == ref == type_ == None, typically the 'any'
        # elements, such as:
        #
        # <xsd:any namespace="##any" processContents="lax" minOccurs="0"/>
        
        self.elem_tag = elem_tag
        self.maxOccurs = maxOccurs
        self.minOccurs = minOccurs
        self.name = name
        self.ref = ref
        self.type_ = type_
            
        # We distinguish single elements and lists (eventually empty), this
        # predicate "cardinality_many" is true for lists.
        self.card_many = self.maxOccurs not in {"0", "1"}

        # subst_grp = "xyz" means that "xyz" is the head of a substitution
        # group, and self is a member of that group. For example, "flowElement"
        # is the head of a group, and subChoreography, subProcess, task, etc,
        # are members.

        # Whenever we find a reference to the head of a group, inside a complex
        # type definition, that reference can be replaced with any member of
        # the group. I.e., when the schema says to expect a head, the parser
        # must accept any member.
        self.subst_grp = subst_grp

    def as_param(self, xsd):
        """Return the type and cardinality of this element.

        This cannot be determined during __init__ because there are references
        to other types that may not have been created yet, the XMLSchema init
        needs to be completed first.

        """
        # element name: resolve references if needed
        if self.name is not None:
            elem_name = protect(self.name)
        else:
            e = xsd.elems[self.ref]
            elem_name = protect(e.name)

        type_map = {
            'xsd:IDREF': str,
            'xsd:QName': str,
        }

        # For the extraction of data from the XML tree, we need to distinguish
        # the simple, string-based types that have an immediate value, and the
        # complex types with an element value, for which the generated code
        # will invoke that type's build() factory method.
        if self.type_ is None:
            # Use self.ref as the name of an *element* defined elsewhere in the
            # schema, and get that element's type attribute. 
            e = xsd.elems[self.ref]
            elem_type = e.type_
        elif self.type_ in type_map:
            # Predefined, string-based type. I don't actually need the 'str'
            # value, just the fact that it's string-based.
            elem_type = type_map[self.type_]
        else:
            # Use self.type_ as the name of a (probably complex) *type* defined
            # elsewhere in the schema.
            elem_type = self.type_

        # Head of a substitution group ?
        head = self.ref in xsd.sg_heads

        return elem_name, elem_type, self.card_many, head
    
    @classmethod
    def build(cls, nd):
        elem_tag = tag(nd)
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in nd.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        ref = nd.attrib['ref'] if 'ref' in nd.attrib else None
        type_ = nd.attrib['type'] if 'type' in nd.attrib else None
        subst_grp = nd.attrib['substitutionGroup'] \
            if 'substitutionGroup' in nd.attrib else None
        return cls(elem_tag, maxOccurs=maxOccurs, minOccurs=minOccurs,
                   name=name, ref=ref, type_=type_, subst_grp=subst_grp)

    def dictify(self):
        d = {}
        if self.maxOccurs is not None:
            d['maxOccurs'] = self.maxOccurs
        if self.minOccurs is not None:
            d['minOccurs'] = self.minOccurs
        if self.name is not None:
            d['name'] = self.name
        if self.ref is not None:
            d['ref'] = self.ref
        if self.type_ is not None:
            d['type'] = self.type_
        if self.subst_grp is not None:
            d['subst_grp'] = self.subst_grp
        return d

#-------------------------------------------------------------------------------

class XsdComplexType:
    def __init__(self, abstract=None, block=None, final=None, id_=None,
                 mixed=None, name=None, base_type=None, attributes=None,
                 elements=None):
        self.abstract = abstract
        self.block = block
        self.final = final
        self.id_ = id_
        self.mixed = mixed
        self.name = name
        self.base_type = base_type
        
        self.attributes = []
        if attributes is not None:
            self.attributes = attributes
            
        self.elements = []
        if elements is not None:
            self.elements = elements

    @classmethod
    def build(cls, nd):
        # Attributes
        abstract = nd.attrib['abstract'] if 'abstract' in nd.attrib else None
        block = nd.attrib['block'] if 'block' in nd.attrib else None
        final = nd.attrib['final'] if 'final' in nd.attrib else None
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        mixed = nd.attrib['mixed'] if 'mixed' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None

        attrs = []
        elems = []
        
        if tag(nd[0]) == 'complexContent':
            if tag(nd[0][0]) == 'extension':
                start = nd[0][0]
                base_type = start.attrib['base']
            else:
                raise NotImplementedError('complexContent but not extension')
        else:
            start = nd
            base_type = None

        for k in start:
            # Sequence
            if tag(k) == 'sequence':
                for elem in k:
                    elem_tag = tag(elem)
                    # FIXME ugly hacks 
                    if elem_tag in ['group', 'choice', 'sequence', 'any']:
                        continue
                    # At this point, the 'elem' thing is an 'element'.
                    
                    e = XsdElement.build(elem)
                    # FIXME ugly hack, we've removed the extensionElements
                    # class (and others) because they don't have any attributes
                    # nor elements and it caused issues with the parsing code.
                    if e.ref == 'extensionElements':
                        continue
                    
                    elems.append(e)

            elif tag(k) == 'attribute':
                # Attributes
                attrs.append(XsdAttribute.build(k))
            else:
                m = f'Tag "{tag(k)}" not implemented, ignoring.'
                print(m, file=sys.stderr)
                continue

        return cls(abstract=abstract, block=block, final=final, id_=id_,
                   mixed=mixed, name=name, base_type=base_type,
                   attributes=attrs, elements=elems)

    def dictify(self):
        d = {}
        # Attributes
        if self.abstract is not None:
            d['abstract'] = self.abstract
        if self.block is not None:
            d['block'] = self.block
        if self.final is not None:
            d['final'] = self.final
        if self.id_ is not None:
            d['id'] = self.id_
        if self.mixed is not None:
            d['mixed'] = self.mixed
        if self.name is not None:
            d['name'] = self.name
        if self.base_type is not None:
            d['base_type'] = self.base_type
        if len(self.attributes) > 0:
            d['attributes'] = [x.dictify() for x in self.attributes],
        if len(self.elements) > 0:
            d['elements'] = [x.dictify() for x in self.elements],
        return d
        
    def __str__(self):
        # return json.dumps(self.dictify(), indent=4)
        return self.name

    #---------------------------------------------------------------------------

    def generate_class(self, xsd):
        """Add the generated python class to the xsd.pyclasses array."""

        # self's own parameters (attributes/elements). We also need the type
        # and cardinality, because we have to generate the code to extract the
        # data from the XML tree in the build() factory method.
        attrs = [(a.name, a.attr_type) for a in self.attributes]
        elems = [e.as_param(xsd) for e in self.elements \
                 if (e.name, e.ref) != (None, None)]

        # Element arguments
        arr = []
        for name, type_, many, _ in elems:
            if many:
                type_ = list
            arr.append(PyArg(name, type_))
        pyargs =[PyArg(name, type_) for name, type_ in attrs] + arr

        # Superclass
        pyparent = xsd.pyclasses[self.base_type] if self.base_type is not None \
            else None
        
        # Generate the class declaration and __init__ function
        c = PyClassXsd(self.name, None, args_opt=pyargs, parent=pyparent,
                       attrs=attrs, elems=elems)
        xsd.pyclasses[self.name] = c

        return c

#-------------------------------------------------------------------------------

class XMLSchema:
    """This class represents an entire XML Schema."""
    def __init__(self, filepath):
        self.filepath = filepath
        self.types = {}
        self.elems = {}
        self.pyclasses = {}

        # Ignore comments
        p = et.XMLParser(remove_comments=True)
        self.root = objectify.parse(filepath, parser=p).getroot()

        # Parse schema
        for nd in self.root:
            if tag(nd) == 'complexType':
                t = XsdComplexType.build(nd)
                self.types[t.name] = t
            elif tag(nd) == 'element':
                e = XsdElement.build(nd)
                self.elems[e.name] = e
        
        # Get the relationships between types
        self.sg = SubstitutionGroups(self.root)
        self.sg_heads = self.sg.heads()
        self.sg_members = self.sg.members()
        
        # Create the type derivations tree
        self.t_deriv = self.derivations()
        # print(self.t_deriv)

        # Missing types: classes without any derivations
        derived_types = set(c.name for c in self.t_deriv.traverse())
        all_types = set(self.types.keys())
        self.missing = all_types - derived_types

        # Map element names to types
        self.map_classes = {}
        for name, elem in self.elems.items():
            self.map_classes[name] = elem.type_ 

    def dictify(self):
        return {
            'types': {k: v.dictify() for k, v in self.types.items()},
            'elems': {k: v.dictify() for k, v in self.elems.items()},
        }

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

    #---------------------------------------------------------------------------
    
    def derivations(self):
        ts = TreeSet()
        for nd in self.root:
            if tag(nd) == 'complexType':
                type_name = nd.attrib['name']
                if tag(nd[0]) == 'complexContent' and \
                   tag(nd[0][0]) == 'extension':
                    k = nd[0][0]
                    base_type = k.attrib['base']
                    ts.add_edge(self.types[base_type],
                                     self.types[type_name])
        return ts

    #---------------------------------------------------------------------------

    def gen_module(self):
        """Generate a python module with all these types as classes."""
        # Output file path: drop the original dirname, keep the file basename
        _, tail = os.path.split(self.filepath)
        base, _ = os.path.splitext(tail)

        # Build the array of python classes for the module
        
        # FIXME we could've built the python class as soon as the complexType
        # was done ? Not sure, there's a forward reference somewhere...

        # Get the class names top to bottom (from type derivations tree) to
        # avoid forward references to class declarations.
        classes = [self.types[c.name].generate_class(self) \
                   for c in self.t_deriv.traverse()]

        # Add the classes that have no derivations
        classes.extend([self.types[c_name].generate_class(self) \
                        for c_name in sorted(self.missing)])

        m = PyModuleXsd(base, classes, self.filepath, self.map_classes,
                        self.sg_members)
        
        outpath = f'{base}.py'
        m.write(outpath)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xsd filepath>')
        exit(-1)
    filepath = sys.argv[1]

    xsd = XMLSchema(filepath)
    # print(xsd)
    xsd.gen_module()
