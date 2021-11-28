# pyclass_xsd.py - a python class generated from an Xml Schema

"""\ Classes generated from an Xml Schema have a few specific characteristics:
they never have dictionary properties (those would be complexTypes), they have
lists, of which we know the item type (elements with maxOccurs greater than 1),
and we want to json-serialize them, so we want to implement dictify().

"""

import sys
from schemax.pyclass.pyclass import PyClass

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
    dumping out thepythin objects.

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

    #---------------------------------------------------------------------------

    def build_elements(self):
        s = ''
        # Build self's own attributes and elements
        if (len(self.args_req), len(self.args_opt)) != (0, 0):
            s += f'{ind}x = {self.name}.build(xsd, nd)\n'
            params = [safe_name for _, safe_name, _ in self.attrs] + \
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
        for name, safe_name, attr_type in self.attrs:
            s += f'{ind}{safe_name} = '
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
                s += 'if k is not None else None\n'
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
        for name, safe_name, attr_type in self.attrs:
            s += f'{ind}if self.{safe_name} is not None:\n'
            s += f"{ind*2}d['{name}'] = self.{safe_name}\n"
            
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

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
