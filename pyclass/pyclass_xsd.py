# pyclass_xsd.py - a python class generated from an Xml Schema

"""\ Classes generated from an Xml Schema have a few specific characteristics:
they never have dictionary properties (those would be complexTypes), they have
lists, of which we know the item type (elements with maxOccurs greater than 1),
and we want to json-serialize them, so we want to implement dictify().

"""

import sys
from keyword import iskeyword
import builtins

#-------------------------------------------------------------------------------

# Globals (indent stuff to go into a dedicated "code formatting" class)
indent_sz = 4
ind = ' '*indent_sz
quot3 = '"'*3

#-------------------------------------------------------------------------------

class PyClassXsd(PyClass):
    """A python class generated from an Xml Schema.

    """
    def __init__(self, name, doc, args, parent=None):
        self.name = pysafe(name)
        self.doc = doc
        self.parent = parent

        # args is an a array of PyArg
        self.args = []
        if args is not None:
            # I want optional args at the back, and False < True
            self.args = sorted(args, key=attrgetter('optional'))

        self.init = PyInitFunc(self.__class__, self.args, \
                               parent=self.parent, level=1)
        self.dictify = PyDictifyFunc(self.__class__, self.args, \
                                     parent=self.parent, level=1)

    #---------------------------------------------------------------------------

    def __str__(self):
        """Return the source code for this class's declaration."""
        s = super().__str__(self)
        s += self.gen_dictify()
        s += self.gen_str()
        return s

    #---------------------------------------------------------------------------

    # Here we define gen_dictify as a method of the PyClass subclass, instead
    # of defining
    def gen_dictify(self):
        """Return the source code for this class's dictify() function.
        """
        s = f"""
def dictify(self):
    {quot3}Return a json-encodable object representing a {self.name}.{quot3}
    obj = {{}}
    for k, v in self.__dict__.items():
        if not (v is None or v == [] or v == {{}}):
            obj[k] = v
"""
        # If some of the arguments are python objects rather than simple types,
        # arrays, dictionaries, or combinations thereof, then they must also be
        # transformed into json-encodable objects
        
        # Look for collections whose items have a classname
        mutargs =  [a for a in self.args if a.mutable \
                    if a.classname is not None]

        if len(mutargs) > 0:
            s += """\
        # Json-encode the python objects inside collections, and add them if
        # they're not empty.

"""
            for ma in mutargs:
                s += f"""\
        if self.{ma.name} is not None:
            obj['{ma.name}'] = [x.dictify() for x in self.{ma.name}]
"""
        s += """
        return obj
"""
        return s
        
    #---------------------------------------------------------------------------

    def gen_str(self):
        """Return the source code for this class's __str__ function."""
        s = f"""
    def __str__(self):
        return json.dumps(self.dictify(), indent=4)
"""
        return s

#-------------------------------------------------------------------------------

class PyDictifyFunc(PyFunction):
    def __init__(self, klass, args, parent=None, level=None):
        # 
        super().__init__('dictify', args, level=level)
        self.parent = parent

    def __str__(self):
        """For indentation purposes, assume the code is toplevel. The rest will be
        taken care of later, if needed.

        """
        s = ''
        # Generate the function signature 
        s += f"""
def {self.name}(self):
{ind}d = 
"""
        # Is it a derived class?
        if self.parent is None:
            s += '{}\n'
        else:
            s += 'super().dictify()\n'

        # Set members
        if len(self.args) == 0:
            s += f'{ind}pass\n'
        else:
            for a in self.args:
                # Cardinality single or many (actually, list or not?)
                if card_many:
                    s += f'{ind}if len(self.{a.name}) > 0:\n'
                    s += f"{ind*2}d['{a.name}'] = "
                    if json_serializable:
                        s += f'self.{a.name}\n'
                    else:
                        s += f'[x.dictify() for x in self.{a.name}]\n'
                else:
                    # Cardinality single
                    s += f'{ind}if self.{a.name} is not None:\n'
                    s += f"{ind*2}d['{a.name}'] = self.{a.name}"
                    if not json_serializable:
                        s += '.dictify()'
                    s += '\n'
        return s

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
