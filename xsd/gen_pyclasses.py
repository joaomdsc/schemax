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
from datetime import datetime

from x4b.tree import TreeSet
from xsd import SubstitutionGroups
from schemax.pyclass.pyclass import PyArg, PyClass

#-------------------------------------------------------------------------------

def tag(nd):
    return et.QName(nd).localname

#-------------------------------------------------------------------------------

builtins_list = dir(builtins)

def protect(name):
    """Change 'name' to avoid keywords and builtins.

    Many XML grammars include an "id" element, for example, but this conflicts
    with python's 'id' builtin. To avoid these kinds of conflicts, we append an
    underscore to the name.

    """

    return f'{name}_' if iskeyword(name) or name in builtins_list else name

#-------------------------------------------------------------------------------

class XsdAttribute:
    def __init__(self, ref=None, name=None, type_=None, use=None, default=None):
        # In Semantic.xsd there are non "ref"
        self.ref = ref
        self.name = name
        self.type_ = type_
        self.use = use
        self.default = default

        self.safe_name = protect(self.name)

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

    def dictify(self):
        d = {}
        if self.ref is not None:
            d['ref'] = self.ref
        if self.name is not None:
            d['name'] = self.name
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
    def __init__(self, elem_tag, ref=None, name=None, type_=None, minOccurs=None,
                 maxOccurs=None, subst_grp=None):
        # Some elements have name == ref == type_ == None, typically the 'any'
        # elements, such as:
        #
        # <xsd:any namespace="##any" processContents="lax" minOccurs="0"/>
        
        self.elem_tag = elem_tag
        self.ref = ref
        self.name = name
        self.type_ = type_
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
            
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
        ref = nd.attrib['ref'] if 'ref' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        type_ = nd.attrib['type'] if 'type' in nd.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in nd.attrib else None
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in nd.attrib else None
        subst_grp = nd.attrib['substitutionGroup'] \
            if 'substitutionGroup' in nd.attrib else None
        return cls(elem_tag, ref=ref, name=name, type_=type_, minOccurs=minOccurs,
                   maxOccurs=maxOccurs, subst_grp=subst_grp)

    def dictify(self):
        d = {}
        if self.ref is not None:
            d['ref'] = self.ref
        if self.name is not None:
            d['name'] = self.name
        if self.type_ is not None:
            d['type'] = self.type_
        if self.minOccurs is not None:
            d['minOccurs'] = self.minOccurs
        if self.maxOccurs is not None:
            d['maxOccurs'] = self.maxOccurs
        if self.subst_grp is not None:
            d['subst_grp'] = self.subst_grp
        return d

#-------------------------------------------------------------------------------

class XsdComplexType:
    def __init__(self, name, abstract, mixed, base_type, attributes=None,
                 elements=None):
        self.name = name
        self.abstract = abstract
        self.mixed = mixed
        self.base_type = base_type
        
        self.attributes = []
        if attributes is not None:
            self.attributes = attributes
            
        self.elements = []
        if elements is not None:
            self.elements = elements

    @classmethod
    def build(cls, nd):
        type_name = nd.attrib['name']
        abstract = 'abstract' in nd.attrib and nd.attrib['abstract']
        mixed = 'mixed' in nd.attrib and nd.attrib['mixed']

        attributes = []
        elements = []
        
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
                    if elem_tag == 'any':
                        continue
                    ref = elem.attrib['ref'] if 'ref' in elem.attrib else None
                    # FIXME ugly hack, we've removed the extensionElements
                    # class (and others) because they don't have any attributes
                    # nor elements and it caused issues with the parsing code.
                    if ref == 'extensionElements':
                        continue
                    name = elem.attrib['name'] if 'name' in elem.attrib \
                        else None
                    type_ = elem.attrib['type'] if 'type' in elem.attrib \
                        else None
                    minOccurs = elem.attrib['minOccurs'] \
                        if 'minOccurs' in elem.attrib else None
                    maxOccurs = elem.attrib['maxOccurs'] \
                        if 'maxOccurs' in elem.attrib else None
                    elements.append(XsdElement(elem_tag, ref=ref, name=name, type_=type_,
                                               minOccurs=minOccurs,
                                               maxOccurs=maxOccurs))

            elif tag(k) == 'attribute':
                # Attributes
                ref = k.attrib['ref'] if 'ref' in k.attrib else None
                name = k.attrib['name'] if 'name' in k.attrib else None
                type_ = k.attrib['type'] if 'type' in k.attrib else None
                use = k.attrib['use'] if 'use' in k.attrib else None
                default = k.attrib['default'] if 'default' in k.attrib else None

                attributes.append(XsdAttribute(ref=ref, name=name,
                                    type_=type_, use=use, default=default))
            else:
                m = f'Tag "{tag(k)}" not implemented, ignoring.'
                print(m, file=sys.stderr)
                continue

        attr = attributes if len(attributes) > 0 else None
        elem = elements if len(elements) > 0 else None
        return cls(type_name, abstract, mixed, base_type, attributes=attr,
                   elements=elem)

    def dictify(self):
        d = {
            'name': self.name,
            'abstract': self.abstract,
            'mixed': self.mixed,
            'base_type': self.base_type,
        }
        if len(self.attributes) > 0:
            d['attributes'] = [x.dictify() for x in self.attributes],
        if len(self.elements) > 0:
            d['elements'] = [x.dictify() for x in self.elements],
        return d
        
    def __str__(self):
        # return json.dumps(self.dictify(), indent=4)
        return self.name

    #---------------------------------------------------------------------------

    def generate_init(self, all_params, ancestors, anc_params, self_names,
                      elems):
        """Generate the __init__ function"""
        # FIXME reorganize the instance variables so I don't have to pass all
        # this stuff around
        s = ''
        # Generate the __init__ function signature (all parameters optional)
        s += """
    def __init__(self, """
        s += ', '.join([f'{p}=None' for p in all_params])
        s += '):\n'

        # __init__ body: if this is a derived class, first we must call the
        # superclass's __init__ function, with just the ancestor's parameters
        if len(ancestors) > 0:
            s += f'{" "*8}super().__init__('
            s += ', '.join([f'{p}={p}' for p in anc_params])
            s += ')\n'

        # Assign self's parameters to the instance variables
        # FIXME I need to distinguish the mutable ones
        mutable = [name for (name, _, card_many, _) in elems if card_many]
        for p in self_names:
            if p in mutable:
                s += f"""\
        self.{p} = []
        if {p} is not None:
            self.{p} = {p}
"""
            else:
                s += f'{" "*8}self.{p} = {p}\n'
            
        return s

    #---------------------------------------------------------------------------

    def generate_build(self, all_params, ancestors, attrs, elems):
        """Generate the build factory method"""
        s = ''
        # Factory (class) method
        s += """
    @classmethod
    def build(cls, xsd, nd):
"""
        # Call each ancestor's build method
        if len(ancestors) > 0:
            s += f'{" "*8}# Get ancestor elements\n'
        for anc in ancestors:
            # FIXME anc might not have any attributes or elements, in that case
            # avoid generating the call to build()
            if len(anc.attributes) == len(anc.elements) == 0:
                continue
            s += f'{" "*8}x = {anc.name}.build(xsd, nd)\n'
            anc_elems = [e.as_param(xsd) for e in anc.elements \
                         if (e.name, e.ref) != (None, None)]
            params = [a.safe_name for a in anc.attributes] + \
                [name for name, _, _, _ in anc_elems]
            for p in params:
                s += f'{" "*8}{p} = x.{p}\n'
        if len(ancestors) > 0:
            s += '\n'
            
        # Code to extract self's attributes from the XML tree. Integers and
        # booleans require a conversion to the right python type, all the
        # others are strings.
        if len(attrs) > 0:
            s += f"{' '*8}# Get self's attributes\n"
        for name, safe_name, attr_type in attrs:
            s += f'{" "*8}{safe_name} = '
            s += 'int(' if attr_type == int else 'py_bool(' \
                if attr_type == bool else ''
            s += f"nd.attrib['{name}']"
            s += ')' if attr_type in {int, bool} else ''
            s += f" if '{name}' in nd.attrib else None\n"
        if len(attrs) > 0:
            s += '\n'

        # Code to extract self's sub-elements from the XML tree.
        if len(elems) > 0:
            s += f"{' '*8}# Get self's sub-elements\n"
        for name, elem_type, card_many, head in elems:
            if head:
                # tag(k) will be the element name of the s.g. member. To call
                # the build method, we need to generate code to get its
                # type. The code needs to access a mapping of element names to
                # types, and that's exactly what 'klasses' is. So we must
                # generate the 'klasses' map.
                s += f'{" "*8}nodes = [k for k in nd ' \
                    f"if tag(k) in members['{name}']]\n"
                s += f'{" "*8}{name} = [(tag(k), ' \
                    'klasses[tag(k)].build(xsd, k)) for k in nodes]\n'
            elif card_many:
                # Cardinality many
                s += f"{' '*8}nodes = [k for k in nd if tag(k) == '{name}']\n"
                s += f'{" "*8}{name} = ['
                if elem_type == str:
                    s += 'k.text.strip()'
                else:
                    s += f'{elem_type}.build(xsd, k)'
                s += ' for k in nodes]\n'
            else:
                # Cardinality single
                s += f"{' '*8}k = next((k for k in nd if tag(k) == '{name}')" \
                    ', None)\n'
                s += f'{" "*8}{name} = '
                if elem_type == str:
                    s += 'k.text.strip()'
                else:
                    s += f'{elem_type}.build(xsd, k)'
                s += 'if k is not None else None\n'
        if len(elems) > 0:
            s += '\n'

        # Return from the build factory method
        s += """\
        return cls("""
        s += ', '.join([f'{p}={p}' for p in all_params])
        s += ')\n'

        return s

    #---------------------------------------------------------------------------

    def generate_dictify(self, ancestors, attrs, elems):
        """Generate the __init__ function"""
        s = ''
        # Generate the dictify() definition
        s += f"""
    def dictify(self):
"""
        if len(ancestors) > 0:
            s += f'{" "*8}d = super().dictify()\n'
        else:
            s += f'{" "*8}d = {{}}\n'
            
        # Self's attributes
        for name, safe_name, attr_type in attrs:
            s += f'{" "*8}if self.{safe_name} is not None:\n'
            s += f"{' '*12}d['{name}'] = self.{safe_name}\n"
            
        # Self's sub-elements
        for name, elem_type, card_many, head in elems:
            if head:
                # tag(k) will be the element name of the s.g. member.
                s += f'{" "*8}if len(self.{name}) > 0:\n'
                s += f"{' '*12}d['{name}'] = [(k, v.dictify())" \
                        f' for k, v in self.{name}]\n'
            elif card_many:
                # Cardinality many
                s += f'{" "*8}if len(self.{name}) > 0:\n'
                if elem_type == str:
                    s += f"{' '*12}d['{name}'] = self.{name}\n"
                else:
                    s += f"{' '*12}d['{name}'] = [x.dictify()" \
                        f' for x in self.{name}]\n'
            else:
                # Cardinality single
                s += f'{" "*8}if self.{name} is not None:\n'
                s += f"{' '*12}d['{name}'] = self.{name}"
                if elem_type != str:
                    s += '.dictify()'
                s += '\n'

        s += f'{" "*8}return d\n'
           
        return s

    #---------------------------------------------------------------------------

    def generate_attrs(self, ancestors, attrs):
        """Generate the attrs method"""
        s = ''
        # Generate the dictify() definition
        s += f"""
    def attrs(self):
"""
        if len(ancestors) > 0:
            s += f'{" "*8}d = super().attrs()\n'
        else:
            s += f'{" "*8}d = {{}}\n'
            
        # Self's attributes
        for name, safe_name, attr_type in attrs:
            s += f'{" "*8}if self.{safe_name} is not None:\n'
            s += f"{' '*12}d['{name}'] = "
            s += 'str(' if attr_type == int else 'xml_bool(' \
                if attr_type == bool else ''
            
            s += f'self.{safe_name}'
            s += ')' if attr_type in {int, bool} else ''
            s += '\n'

        s += f'{" "*8}return d\n'
           
        return s

    #---------------------------------------------------------------------------

    def generate_sub_elems(self, ancestors, elems):
        """Generate the __init__ function"""
        s = ''
        # Generate the sub_elems() definition
        s += f"""
    def sub_elems(self):
"""
        if len(ancestors) > 0:
            s += f'{" "*8}nodes = super().sub_elems()\n'
        else:
            s += f'{" "*8}nodes = []\n'
            
        # Self's sub-elements
        for name, elem_type, card_many, head in elems:
            if head:
                s += f'{" "*8}for k, v in self.{name}:\n'
                s += f'{" "*12}nodes.append(v.to_xml())\n'
            elif card_many:
                # Cardinality many
                s += f'{" "*8}for x in self.{name}:\n'
                if elem_type == str:
                    s += f"{' '*12}nd = et.Element(semns('{name}')" \
                        ', nsmap=nsmap)\n'
                    s += f'{" "*12}nd.text = x\n'
                    s += f'{" "*12}nodes.append(nd)\n'
                else:
                    s += f'{" "*12}nodes.append(x.to_xml())\n'
            else:
                # Cardinality single
                s += f'{" "*8}if self.{name} is not None:\n'
                if elem_type == str:
                    s += f"{' '*12}nd = et.Element(semns('{name}')" \
                        ', nsmap=nsmap)\n'
                    s += f'{" "*12}nd.text = self.{name}\n'
                    s += f'{" "*12}nodes.append(nd)\n'
                else:
                    s += f'{" "*12}nodes.append(self.{name}.to_xml())\n'

        s += f'{" "*8}return nodes\n'
           
        return s

    #---------------------------------------------------------------------------

    def generate_as_xml(self):
        """Generate the __init__ function"""
        heredoc = '"""'
        s = f"""
    def to_xml(self):
        {heredoc}Return self as an XML (etree) element{heredoc}
        nd = et.Element(semns(self.__class__.__name__), nsmap=nsmap)
        # Attributes
        nd.attrib.update(self.attrs())
        # Elements
        for k in self.sub_elems():
            nd.append(k)
        return nd
"""
        return s

    #---------------------------------------------------------------------------

    def generate_class(self, xsd):
        s = ''

        # Ancestry if a list of classes (XsdComplexType instances)
        ancestors = xsd.t_deriv.ancestry(self)

        # Get the parameters (attributes/elements) from each ancestor. For the
        # ancestors, we only need the names (but refs must've been resolved,
        # hence the call to as_param()), and we don't need to distinguish attrs
        # and elems, they're just going to be passed to __init__.
        anc_params = []
        for anc in ancestors:
            anc_params.extend([a.safe_name for a in anc.attributes])
            anc_elems = [e.as_param(xsd) for e in anc.elements \
                         if (e.name, e.ref) != (None, None)]
            anc_params.extend([name for name, _, _, _ in anc_elems])

        # self's own parameters (attributes/elements). We also need the type
        # and cardinality, because we have to generate the code to extract the
        # data from the XML tree in the build() factory method.
        attrs = [(a.name, a.safe_name, a.attr_type) for a in self.attributes]
        elems = [e.as_param(xsd) for e in self.elements \
                 if (e.name, e.ref) != (None, None)]

        # Get all the parameters names
        self_names = [safe_name for _, safe_name, _ in attrs] + \
            [name for name, type_, _, _ in elems]
        all_params = anc_params + self_names

        parent = self.base_type if self.base_type is not None else ''

        #-----------------------------------------------------------------------
        # Separator and class declaration
#         s += f"""
# #{"-"*79}

# class {self.name}({parent}):
# """
#         # Generate the __init__ function
#         if len(all_params) > 0:
#             s += self.generate_init(all_params, ancestors, anc_params,
#                                     self_names, elems)
        #-----------------------------------------------------------------------

        # New version using the pyclass module from schemax.pyclass

        # Element arguments
        arr = []
        for name, type_, many, _ in elems:
            if many:
                type_ = list
            arr.append(PyArg(name, type_))
        pyargs =[PyArg(name, type_) for _, name, type_ in attrs] + arr
        pyparent = xsd.pyclasses[self.base_type] if self.base_type is not None \
            else None
        c = PyClass(self.name, None, args_opt=pyargs, parent=pyparent)
        xsd.pyclasses[self.name] = c

        # Generate the class declaration and __init__ function
        s += str(c)

        # Generate the build factory method
        s += self.generate_build(all_params, ancestors, attrs, elems)
        
        # Generate the dictify() definition
        s += self.generate_dictify(ancestors, attrs, elems)
        
        # Generate the attrs() method
        s += self.generate_attrs(ancestors, attrs)
        
        # Generate the sub_elems() method
        s += self.generate_sub_elems(ancestors, elems)
        
        # Generate the to_xml() method for classes that are not derived
        if len(ancestors) == 0:
            s += self.generate_as_xml()
                
        # Finished generating the python code for this XsdComplexType
        # End of the generate() method
        return s

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
        self.klasses = {}
        for name, elem in self.elems.items():
            self.klasses[name] = elem.type_ 

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

    def generate_prologue(self, filepath):
        head, tail = os.path.split(filepath)
        root, _ = os.path.splitext(tail)
        outpath = f'{root}.py'
        
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Avoid mis-interpretations in the f-string
        heredoc = '"""'
        ob3 = '{{{'
        cb3 = '}}}'
        
        s = f"""\
# {root}.py This file was generated on {dt}
# Schema file: {filepath}

import lxml.etree as et

#{"-"*79}

def tag(nd):
    return et.QName(nd).localname

def py_bool(b):
    return b == 'true'

def xml_bool(b):
    return 'true' if b else 'false'

#{"-"*79}

# BPMN 2.0 Semantic namespace defined in:
# https://www.omg.org/spec/BPMN/20100501/Semantic.xsd
semantic_namespace = 'http://www.omg.org/spec/BPMN/20100524/MODEL'

# Provide a universally qualified name for a tag
def semns(s):
    {heredoc}Qualify tag name 's' with the 'semantic' namespace{heredoc}
    return f'{ob3}semantic_namespace{cb3}{{s}}'

# Namespaces mapping
nsmap = {{
    'semantic': semantic_namespace,
}}

"""
        return s

    #---------------------------------------------------------------------------

    def generate_epilogue(self):
        s = f"""
#{"-"*79}

"""
        # Mapping of element names (tags) to classes
        s += '# Mapping of element names (tags) to python classes\n'
        s += 'klasses = {\n'
        for k, v in self.klasses.items():
            s += f"    '{k}': {v},\n"
        s += '}\n'
        s += '\n'

        # Mapping of s.g. heads to members
        s += '# Mapping of substitution group heads to members\n'
        s += 'members = {\n'
        for k, v in self.sg_members.items():
            s += f"{' '*4}'{k}': [\n"
            for m in v:
                s += f"{' '*8}'{m}',\n"
            s += f"{' '*4}],\n"
        s += '}\n'

        s += f"""
#{"-"*79}

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
"""
        return s

    #---------------------------------------------------------------------------

    def generate_classes(self):
        """Generate the python classes for the schema's types."""
        # Output file path: drop the original dirname, keep the file basename
        _, tail = os.path.split(self.filepath)
        base, _ = os.path.splitext(tail)
        outpath = f'{base}.py'

        # Source file prologue
        s = self.generate_prologue(self.filepath)

        # Get the class names top to bottom (from type derivations tree) to
        # avoid forward references to class declarations
        for c in self.t_deriv.traverse():
            s += self.types[c.name].generate_class(self)

        # Get the classes without any derivations...
        for c_name in sorted(self.missing):
            c = self.types[c_name]
            s += c.generate_class(self)

        # Source file epilogue
        s += self.generate_epilogue()

        # Write out the python source code file
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(s)

    #---------------------------------------------------------------------------

    def gen_module(self):
        """Generate a python module with all these types as classes."""
        # Output file path: drop the original dirname, keep the file basename
        _, tail = os.path.split(self.filepath)
        base, _ = os.path.splitext(tail)
        mod_name = f'{base}_pyclass'

        s = ''
        # Get the class names top to bottom (from type derivations tree) to
        # avoid forward references to class declarations
        for c in self.t_deriv.traverse():
            s += self.types[c.name].generate_class(self)

        # Get the classes without any derivations...
        for c_name in sorted(self.missing):
            c = self.types[c_name]
            s += c.generate_class(self)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xsd filepath>')
        exit(-1)
    filepath = sys.argv[1]

    xsd = XMLSchema(filepath)
    # print(xsd)
    xsd.generate_classes()
    # xsd.gen_module()
