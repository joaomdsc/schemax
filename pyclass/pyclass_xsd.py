# pyclass_xsd.py - a python class generated from an Xml Schema

"""\ Classes generated from an Xml Schema have a few specific characteristics:
they never have dictionary properties (those would be complexTypes), they have
lists, of which we know the item type (elements with maxOccurs greater than 1),
and we want to json-serialize them, so we want to implement dictify().

"""

import sys

from schemax.pyclass.pyclass import pysafe, PyClass, PyModule

#-------------------------------------------------------------------------------

# Globals (indent stuff to go into a dedicated "code formatting" class)
indent_sz = 4
ind = ' '*indent_sz
quot3 = '"'*3

#-------------------------------------------------------------------------------

class PyClassXsd(PyClass):
    """A python class generated from an XML Schema.

    The classes we generate from XML Schemas are used to parse instance
    documents, so we define a 'build' class method to build instances from XML;
    since we get detailed type information from the schema, we can also define
    a 'dictify' method and use that for json serialization, which is also how
    we implement the class's __str__ method, so we get a standard method for
    dumping out the python objects.

    For re-creating an XML tree from our python objects, we implement a
    'to_xml' method (defined in the toplevel superclasses) that uses 'attrs'
    and 'sub_elems' methods from the derived classes. This is useful for
    checking that we reconstruct an identical XML object from python, with no
    information loss.

    The python sub-class hierarchy is defined from the 'extension'
    relationships given in the schema.

    """
    
    def __init__(self, name, doc, args_req=None, args_opt=None, parent=None,
                 attrs=None, elems=None):
        super().__init__(name, doc, args_req=args_req, args_opt=args_opt,
                         parent=parent)
        self.attrs = attrs
        self.elems = elems

        self.methods.append(self.gen_build())
        self.methods.append(self.gen_dictify())
        self.methods.append(self.gen_attrs(attrs))
        self.methods.append(self.gen_elems(elems))

        if self.parent is None:
            self.methods.append(self.gen_to_xml())

    #---------------------------------------------------------------------------

    def build_elements(self):
        s = ''
        # Build self's own attributes and elements
        if (len(self.args_req), len(self.args_opt)) != (0, 0):
            s += f'{ind}x = {self.name}.build(xsd, nd)\n'
            params = [pysafe(name) for name, _ in self.attrs] + \
                [name for name, _, _, _ in self.elems]
            for p in params:
                s += f'{ind}{p} = x.{p}\n'

        # Build the ancestors' attributes and elements, if any
        if self.parent is not None:
            # Ancestors first, self later
            s = self.parent.build_elements() + s

        return s

    #---------------------------------------------------------------------------

    def gen_build(self):
        """Return the source code for this class's build() factory method.

        The build function has three parts: first it builds an instance of each
        ancestor, to extract their attributes and elements from the XML tree;
        then it extracts self's attributes; then it extracts self's
        sub-elements; and finally it creates and returns an object instance
        using all the extracted data.

        """
        s = ''
        s += f"""\
@classmethod
def build(cls, xsd, nd):
"""
        # Generate code for getting the ancestor elements
        if self.parent is not None:
            s += f'{ind}# Get ancestor elements\n'
            s += self.parent.build_elements()
            s += '\n'

        # Code to extract self's attributes from the XML tree. Integers and
        # booleans require a conversion to the right python type, all the
        # others are strings.
        if len(self.attrs) > 0:
            s += f"{ind}# Get self's attributes\n"
        for name, attr_type in self.attrs:
            s += f'{ind}{pysafe(name)} = '
            s += 'int(' if attr_type == int else 'py_bool(' \
                if attr_type == bool else ''
            s += f"nd.attrib['{name}']"
            s += ')' if attr_type in {int, bool} else ''
            s += f" if '{name}' in nd.attrib else None\n"
        if len(self.attrs) > 0:
            s += '\n'
        
        # Code to extract self's sub-elements from the XML tree.
        if len(self.elems) > 0:
            s += f"{ind}# Get self's sub-elements\n"
        for name, elem_type, card_many, head in self.elems:
            if head:
                # tag(k) will be the element name of the s.g. member. To call
                # the build method, we need to generate code to get its
                # type. The code needs to access a mapping of element names to
                # types, and that's exactly what 'klasses' is. So we must
                # generate the 'klasses' map.
                s += f'{ind}nodes = [k for k in nd ' \
                    f"if tag(k) in members['{name}']]\n"
                s += f'{ind}{name} = [(tag(k), ' \
                    'klasses[tag(k)].build(xsd, k)) for k in nodes]\n'
            elif card_many:
                # Cardinality many
                s += f"{ind}nodes = [k for k in nd if tag(k) == '{name}']\n"
                s += f'{ind}{name} = ['
                if elem_type == str:
                    s += 'k.text.strip()'
                else:
                    s += f'{elem_type}.build(xsd, k)'
                s += ' for k in nodes]\n'
            else:
                # Cardinality single
                s += f"{ind}k = next((k for k in nd if tag(k) == '{name}')" \
                    ', None)\n'
                s += f'{ind}{name} = '
                if elem_type == str:
                    s += 'k.text.strip()'
                else:
                    s += f'{elem_type}.build(xsd, k)'
                s += ' if k is not None else None\n'
        if len(self.elems) > 0:
            s += '\n'

        # Return from the build factory method
        all_params = [a.name for a in self.all_reqs() + self.all_opts()]
        s += f'{ind}return cls('
        s += ', '.join([f'{p}={p}' for p in all_params])
        s += ')\n'

        return s
        
    #---------------------------------------------------------------------------

    # Here we define gen_dictify as a method of the PyClass subclass, instead
    # of defining PyDictifyFunc as a sub-class of PyFunction like we did for
    # init ()we don't need the gen_signature functionality).
    def gen_dictify(self):
        """Return the source code for this class's dictify() method.

        We ignore empty collections and None properties, because the schemas
        include every possible property and those properties are not always
        found in the instances, so we try to limit ourselves to what is
        actually present.

        Note that this hides the distinction between empty and absent
        collections.

        """
        s = ''
        s += f"""\
def dictify(self):
    d = """
        s += 'super().dictify()' if self.parent is not None else '{}'
        s += '\n'

        # Self's attributes (types are always string-based)
        for name, _ in self.attrs:
            s += f'{ind}if self.{pysafe(name)} is not None:\n'
            s += f"{ind*2}d['{name}'] = self.{pysafe(name)}\n"
            
        # Self's sub-elements
        for name, elem_type, card_many, head in self.elems:
            if head:
                # tag(k) will be the element name of the subst.gr. member.
                s += f'{ind}if len(self.{name}) > 0:\n'
                s += f"{ind*2}d['{name}'] = [(k, v.dictify())" \
                        f' for k, v in self.{name}]\n'
            elif card_many:
                # Cardinality many
                s += f'{ind}if len(self.{name}) > 0:\n'
                if elem_type == str:
                    s += f"{ind*2}d['{name}'] = self.{name}\n"
                else:
                    s += f"{ind*2}d['{name}'] = [x.dictify()" \
                        f' for x in self.{name}]\n'
            else:
                # Cardinality single
                s += f'{ind}if self.{name} is not None:\n'
                s += f"{ind*2}d['{name}'] = self.{name}"
                if elem_type != str:
                    s += '.dictify()'
                s += '\n'

        s += f'{ind}return d\n'
        return s
        
    #---------------------------------------------------------------------------

    def gen_attrs(self, attrs):
        """Return the source code for this class's attrs() method.

        attrs is a list of (name, safe_name, attr_type) tuples, where attr_type
        is one of {str, int, bool}.

        """
        s = ''
        s += f"""\
def attrs(self):
    d = """
        s += 'super().attrs()' if self.parent is not None else '{}'
        s += '\n'
            
        # Self's attributes
        for name, attr_type in attrs:
            s += f'{ind}if self.{pysafe(name)} is not None:\n'
            s += f"{ind*2}d['{name}'] = "
            s += 'str(' if attr_type == int else 'xml_bool(' \
                if attr_type == bool else ''
            s += f'self.{pysafe(name)}'
            s += ')' if attr_type in {int, bool} else ''
            s += '\n'

        s += f'{ind}return d\n'

        return s
        
    #---------------------------------------------------------------------------

    def gen_elems(self, elems):
        """Return the source code for this class's elems() method.

        elems is a list of (name, elem_type, card_many, head) tuples.

        """
        s = ''
        s += f"""\
def sub_elems(self):
    nodes = """
        s += 'super().sub_elems()' if self.parent is not None else '[]'
        s += '\n'
        
        # Self's sub-elements
        for name, elem_type, card_many, head in elems:
            if head:
                s += f'{ind}for k, v in self.{name}:\n'
                s += f'{ind*2}nodes.append(v.to_xml())\n'
            elif card_many:
                # Cardinality many
                s += f'{ind}for x in self.{name}:\n'
                if elem_type == str:
                    s += f"{ind*2}nd = et.Element(semns('{name}')" \
                        ', nsmap=nsmap)\n'
                    s += f'{ind*2}nd.text = x\n'
                    s += f'{ind*2}nodes.append(nd)\n'
                else:
                    s += f'{ind*2}nodes.append(x.to_xml())\n'
            else:
                # Cardinality single
                s += f'{ind}if self.{name} is not None:\n'
                if elem_type == str:
                    s += f"{ind*2}nd = et.Element(semns('{name}')" \
                        ', nsmap=nsmap)\n'
                    s += f'{ind*2}nd.text = self.{name}\n'
                    s += f'{ind*2}nodes.append(nd)\n'
                else:
                    s += f'{ind*2}nodes.append(self.{name}.to_xml())\n'

        s += f'{ind}return nodes\n'

        return s
        
    #---------------------------------------------------------------------------

    def gen_to_xml(self):
        """Return the source code for this class's to_xml() method."""
        s = f"""\
def to_xml(self):
    {quot3}Return self as an XML (etree) element{quot3}
    nd = et.Element(semns(self.__class__.__name__), nsmap=nsmap)
    # Attributes
    nd.attrib.update(self.attrs())
    # Elements
    for k in self.sub_elems():
        nd.append(k)
    return nd
"""
        return s

#-------------------------------------------------------------------------------

class PyModuleXsd(PyModule):
    def __init__(self, name, classes, xsd_filepath, map_classes, sg_members):
        super().__init__(name, classes)
        self.xsd_filepath = xsd_filepath
        self.map_classes = map_classes
        self.sg_members = sg_members

    def prologue(self):
        s = ''
        s += super().prologue()

        # Avoid mis-interpretations in the f-string
        ob3 = '{{{'
        cb3 = '}}}'

        s += f"""\
# Schema file: {self.xsd_filepath}

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
    {quot3}Qualify tag name 's' with the 'semantic' namespace{quot3}
    return f'{ob3}semantic_namespace{cb3}{{s}}'

# Namespaces mapping
nsmap = {{
    'semantic': semantic_namespace,
}}

"""
        return s
        
    #---------------------------------------------------------------------------

    def epilogue(self):
        s = ''
        s = f"""
#{"-"*79}

"""
        # Mapping of element names (tags) to classes
        s += '# Mapping of element names (tags) to python classes\n'
        s += 'klasses = {\n'
        for k, v in self.map_classes.items():
            s += f"{ind}'{k}': {v},\n"
        s += '}\n'
        s += '\n'

        # Mapping of s.g. heads to members
        s += '# Mapping of substitution group heads to members\n'
        s += 'members = {\n'
        for k, v in self.sg_members.items():
            s += f"{ind}'{k}': [\n"
            for m in v:
                s += f"{ind*2}'{m}',\n"
            s += f"{ind}],\n"
        s += '}\n'

        s += super().epilogue()

        return s

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
