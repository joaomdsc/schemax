# pyclass_xsd.py - a python class generated from an Xml Schema

"""\ Classes generated from an Xml Schema have a few specific characteristics:
they never have dictionary properties (those would be complexTypes), they have
lists, of which we know the item type (elements with maxOccurs greater than 1),
and we want to json-serialize them, so we want to implement dictify().

"""

import sys
from keyword import iskeyword
import builtins
from operator import attrgetter

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

    def param_names(self):
        """Names of self's own parameters to init(), required and optional"""
        return {
            'required': [p.name for p in self.args if not p.optional],
            'optional': [p.name for p in self.args if p.optional],
        }

    def all_param_names():
        """Parameters to init() from self and all of its ancestors"""
        # Get the list of classes that contribute parameters to init, i.e. self
        # plus all its ancestors, if any.

        # FIXME my params + parent.all_param_names(). We never need ancestry,
        # just recall the function recursively.
        klasses = [self, self.parent] + self.parent.ancestry() \
            if self.parent is not None else [self]

        # I've lost the distinction between self and ancestors
        req = []
        opt = []
        for c in klasses:
            p = c.param_names()
            req.extend(p['required'])
            opt.extend(p['optional'])

        return req, opt

    #---------------------------------------------------------------------------

    def __str__(self):
        """Return the source code for this class's declaration."""
        s = super().__str__(self)
        s += self.gen_dictify()
        s += self.gen_str()
        return s

    #---------------------------------------------------------------------------

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

class PyInitFunc(PyFunction):
    def __init__(self, klass, args, parent=None, level=None):
        super_args = [PyArg('self', klass, optional=False)] + args
        super().__init__('__init__', super_args, level=level)
        self.parent = parent

    def __str__(self):
        # Generate the function signature 
        s = self.gen_signature()

        # If it's a derived class, call superclass's __init__
        if self.parent is not None:
            s += f'{ind*(self.level+1)}super().__init__(self'
            # Here we need to include only the ancestor's parameters, required
            # first, followed by optional. Initially on a single line.
            req, opt = self.parent.all_param_names():
            for p in req:
                s += f', {p}'
            for p in opt:
                s += f', {p}={p}'
            s += '\n'

        # Mutables: when generating from XML Schema, list is the only possible
        # mutable, in fact mutable == card_many == list.

        # Set member values
        for a in self.args[1:]:
            # Here we need to include only self's parameters 
            if a.type_ in [dict, list]:
                # But we need to distinguish mutable or not
                s += '\n'
                s += f'{ind*2}self.{a.name} = {"[]" if a.type_ == list \
                    else "{}"}\n'
                s += f'{ind*2}if {a.name} is not None:\n'
                s += f'{ind*3}self.{a.name} = {a.name}\n'
            else:
                s += f'{ind*2}self.{a.name} = {a.name}\n'
        if len(self.args) == 0:
            s += f'{ind*2}pass\n'

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
