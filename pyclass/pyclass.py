# pyclass.py - a python class

import sys
from keyword import iskeyword
import builtins

#-------------------------------------------------------------------------------

# Globals (indent stuff to go into a dedicated "code formatting" class)
indent_sz = 4
ind = ' '*indent_sz
quot3 = '"'*3

#-------------------------------------------------------------------------------

def indent_right(s):
    return '\n'.join([f'{ind}{line}' for line in s.splitlines()])

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
        # or anything else. This is needed to support mutable default arguments.
        self.type_ = type_
        
        self.optional = optional

#-------------------------------------------------------------------------------

class PyClass():
    """A python class, with an __init__ method."""
    
    def __init__(self, name, doc, args_req=None, args_opt=None, parent=None):
        """If not None, 'parent' is another instance of PyClass, representing this
        class's superclass.

        """
        self.name = pysafe(name)
        self.doc = doc
        self.parent = parent

        # args_req is an a array of PyArg. It holds the required arguments for
        # this class only, not including its ancestors.
        self.args_req = []
        if args_req is not None:
            self.args_req = args_req

        # args_opt is an a array of PyArg. It holds the optional arguments for
        # this class only, not including its ancestors.
        self.args_opt = []
        if args_opt is not None:
            self.args_opt = args_opt

        # Create the __init__ function for this class
        self.init = PyInitFunc(args_req=args_req, args_opt=args_opt,
                               parent=self.parent)

    def all_reqs(self):
        """All the required arguments, from the first ancestor down to self"""
        return self.args_req if self.parent is None \
            else self.parent.all_reqs() + self.args_req

    def all_opts(self):
        """All the optional arguments, from the first ancestor down to self"""
        return self.args_opt if self.parent is None \
            else self.parent.all_opts() + self.args_opt

    #---------------------------------------------------------------------------

    def __str__(self):
        """Return the source code for this class's declaration."""
        # FIXME shouldn't hardcode 79 here, a later processing stage might
        # indent everything if the class is not toplevel.
        s = f"""

#{'-'*79}

class {self.name}"""
        if self.parent is not None:
            s += f'({self.parent.name})'
        s += ':\n'
        if self.doc is not None:
            s += """\
{ind}{quot3}{self.doc}{quot3}
"""
        # Function source code has been generated assuming the function was
        # toplevel. Now we're inside a class that's toplevel, so the code needs
        # to be indented right, once.
        s += indent_right(str(self.init))
        
        return s

#-------------------------------------------------------------------------------

class PyFunction:
    def __init__(self, name, args_req=None, args_opt=None):
        """A python function"""
        self.name = name

        self.args_req = []
        if args_req is not None:
            self.args_req = args_req

        self.args_opt = []
        if args_opt is not None:
            self.args_opt = args_opt

    def gen_signature(self):
        """Generate the function declaration and arguments."""
        s = ''
        
        # Function name declaration
        s += f'def {self.name}('

        # Function args/parameters
        param_names = [f'{a.name}' for a in self.args_req] + \
            [f'{a.name}=None' for a in self.args_opt]
        s += ', '.join(param_names)
        s += '):\n'

        return s

#-------------------------------------------------------------------------------

class PyInitFunc(PyFunction):
    """An __init__ method in a python class.

    The arguments to an __init__ method (in its signature) include self, as
    well as the ancestors' arguments, if any (both required and optional).

    Calling the superclass's __init__ uses only the ancestor's arguments, not
    self's.

    Assigning member variables, on the other hand, is done only on self's
    variables, not the ancestors.

    """
    def __init__(self, args_req=None, args_opt=None, parent=None):
        """args_(req|opt) include only self's argumnets, not the ancestor's."""

        # Get *all* the arguments, self + ancestors, for the superclass
        all_reqs = [PyArg('self', None)]
        if parent is not None:
            all_reqs += parent.all_reqs()
        all_reqs += args_req
            
        all_opts = []
        if parent is not None:
            all_opts += parent.all_opts()
        all_opts += args_opt

        # The superclass's members include both self and ancestor arguments
        super().__init__('__init__', args_req=all_reqs, args_opt=all_opts)
        
        # Subclass includes only self's arguments, not the ancestor's (we
        # override the superclass's variables) FIXME this does not *hide* the
        # superclass's variables, it replaces them
        self.own_args_req = args_req
        self.own_args_opt = args_opt
        self.parent = parent

    def __str__(self):
        """Code is generated assuming the function is toplevel."""
        s = ''
        
        # Generate the function signature 
        s += self.gen_signature()

        # If it's a derived class, call superclass's __init__
        if self.parent is not None:
            s += f'{ind}super().__init__('
            # Here we need to include only the ancestor's parameters, required
            # first, followed by optional. Initially on a single line.
            param_names = [f'{a.name}' for a in self.parent.all_reqs()] + \
                [f'{a.name}={a.name}' for a in self.parent.all_opts()]
            s += ', '.join(param_names)
            s += ')\n'

        # Set member values (self only, no ancestors)
        for a in self.own_args_req:
            s += f'{ind}self.{a.name} = {a.name}\n'
            
        for a in self.own_args_opt:
            if a.type_ in [dict, list]:
                # But we need to distinguish mutable or not
                s += '\n'
                s += f'{ind}self.{a.name} = ' \
                    f'{"[]" if a.type_ == list else "{}"}\n'
                s += f'{ind}if {a.name} is not None:\n'
                s += f'{ind*2}self.{a.name} = {a.name}\n'
            else:
                s += f'{ind}self.{a.name} = {a.name}\n'

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

import json"""

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
        
    def write(self, filepath):
        """Write the source code to this module into a file."""
        with open(f'{self.name}.py', 'w', encoding='utf-8') as f:
            f.write(str(self))

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
