# pyclass.py - a python class

import sys
from keyword import iskeyword
import builtins
from operator import attrgetter

#-------------------------------------------------------------------------------

# Globals
quot3 = '"'*3

#-------------------------------------------------------------------------------

builtins_list = dir(builtins)

def pysafe(s):
    # Leading dollar sign
    # FIXME everything but alphanumeric and underscore needs to be replaced
    s = f'DLR_{s[1:]}' if s[0] == '$' else s

    # Dashes
    s = s.replace('-', '_')

    # Python keywords or builtins
    return f'{s}_' if iskeyword(s) or s in builtins_list else s
    
#-------------------------------------------------------------------------------

class PyArg():
    """An argument to a python method.
    """
    def __init__(self, name, type_, optional=True):
        self.name = pysafe(name)

        # type_ is a python type. We'll distinguish dict, list, a python class,
        # or anything else. An instance of a python class is not immediately
        # dictifiable, we'll need to explicitly call dictify() on it.
        self.type_ = type_
        
        self.optional = optional

#-------------------------------------------------------------------------------

class PyClass():
    """A python class, with __init__, dictify, and __str__ .

    If not None, 'parent' is another instance of PyClass, representing this
    class's superclass.

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
        ind = ' '*4

        s = f"""
    def __str__(self):
        return json.dumps(self.dictify(), indent=4)
"""
        return s

    #---------------------------------------------------------------------------

    def __str__(self):
        """Return the source code for this class's declaration."""
        s = f"""
#{'-'*79}

class {self.name}:
    {quot3}{self.doc}{quot3}
"""
        s += self.gen_init()
        s += self.gen_dictify()
        s += self.gen_str()
        return s

#-------------------------------------------------------------------------------

class PyFunction:
    def __init__(self, name, args=None, level=0):
        """The 'level' argument represents the number of indentation levels at which
        the generated code should start (0 for a toplevel function, 1 for a
        class method, etc)

        """
        self.name = name

        self.args = []
        if args is not None:
            self.args = args

        self.level = level

    def gen_signature(self):
        """Generate the function declaration and arguments.

        Formal parameters (args) are given as a list of PyArg. The code breaks
        down the list so that the source code always remains within an
        80-character limit.

        """
        ind = ' '*4
        # Function name declaration
        line = f'{ind*self.level}def {self.name}('

        # No parameters
        if len(self.args) == 0:
            line += '):\n'
            return line

        # Assuming one parameter always fits
        elif len(self.args) == 1:
            a = self.args[0]
            line += f"{a.name}{'=None' if a.optional else ''}):\n"
            return line

        # Elements to be added. Here we need to distinguish required
        # vs. optional parameters. This assumes that self.args is in the right
        # order (required first, followed by optional).
        a_iter = iter(
            [f"{a.name}{'=None' if a.optional else ''}" for a in self.args])

        # Add arguments one by one, ensuring the code width remains below 80 cols
        s = ''
        try:
            line += f'{next(a_iter)},'
            param = next(a_iter)  # assuming len(self.args) > 0
            while True:
                while len(f'{line} {param},') < 80:
                    line += f' {param}'
                    param = next(a_iter)
                    line += ','
                s += line + '\n'
                line = f'{ind*(self.level+2)}{param}'
                param = next(a_iter)
                line += ','
        except StopIteration:
            s += line + '):\n'
        return s

#-------------------------------------------------------------------------------

class PyInitFunc(PyFunction):
    def __init__(self, klass, args, parent=None, level=None):
        super_args = [PyArg('self', klass, optional=False)] + args
        super().__init__('__init__', super_args, level=level)
        self.parent = parent

    def __str__(self):
        ind = ' '*4
        s = self.gen_signature()

        # Function body
        if self.parent is not None:
            s += f'{ind*(self.level+1)}super().__init__(self'
            # Here we need to include only the ancestor's parameters, required
            # first, followed by optional.
            req, opt = self.parent.all_param_names():
            super_args = req + opt
            for p in super_args:
                s += f', {p}'

        # Set members
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
        super_args = [PyArg('self', klass, optional=False)] + args
        super().__init__('__init__', super_args, level=level)
        self.parent = parent

    def __str__(self):
        ind = ' '*4
        s = self.gen_signature()

        # Function body
        if self.parent is not None:
            s += f'{ind*(self.level+1)}super().__init__(self'
            # Here we need to include only the ancestor's parameters, required
            # first, followed by optional.
            req, opt = self.parent.all_param_names():
            super_args = req + opt
            for p in super_args:
                s += f', {p}'

        # Set members
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

class PyModule:
    def __init__(self, name, klasses=None):
        self.name = name

        self.klasses = []
        if klasses is not None:
            self.klasses = klasses

        self.prologue = f"""\
# {self.name}.py

import json
"""

        self.epilogue = f"""
#{'-'*79}

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
"""

    def __str__(self):
        s = self.prologue
        for k in self.klasses:
            s += str(k)
        s += self.epilogue
        return s
        
    def write_file(self, filepath):
        """Write the source code to this module into a file."""
        with open(f'{self.name}.py', 'w', encoding='utf-8') as f:
            f.write(str(self))
    

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
