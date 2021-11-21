# pyclass.py - a python class

import sys
from keyword import iskeyword
import builtins
from operator import attrgetter

#-------------------------------------------------------------------------------

# Globals
heredoc = '"'*3

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

def gen_signature(name, args, level=0):
    """Generate the function declaration and arguments.

    Formal parameters (args) are given as a list of PyArg. The code breaks down
    the list so that the source code always remains within an 80-character
    limit.

    The 'level' argument represents the number of indentation levels at which
    this code should start (0 for a toplevel function, 1 for a class method,
    etc)

    """
    ind = ' '*4
    # Function name declaration
    line = f'{ind*level}def {name}('

    # No parameters
    if len(args) == 0:
        line += '):\n'
        return line

    # Assuming one parameter always fits
    elif len(args) == 1:
        a = args[0]
        line += f"{a.name}{'=None' if a.optional else ''}):\n"
        return line

    # Elements to be added
    a_iter = iter(
        [f"{a.name}{'=None' if a.optional else ''}" for a in args])

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
            line = f'{ind*(level+2)}{param}'
            param = next(a_iter)
            line += ','
    except StopIteration:
        s += line + '):\n'
    return s
    
#-------------------------------------------------------------------------------

class PyArg():
    """An argument to a python method.
    """
    def __init__(self, name, optional=True, mutable=False, array=False,
                 classname=None):
        self.name = pysafe(name)
        self.optional = optional
        self.mutable = mutable
        self.array = array  # If mutable: True if array, False if dictionary

        # Python class name for this PyArg, if it's an object, rather than a
        # simple type; or, if the PyArg is a mutable object (array or dict),
        # python class name for the collection's items.
        self.classname = classname

#-------------------------------------------------------------------------------

class PyClass():
    """A python class, with __init__, dictify, and __str__ ."""
    def __init__(self, name, doc, args):
        self.name = name
        self.doc = doc

        # args is an a array of PyArg
        self.args = []
        if args is not None:
            # I want optional args at the back, and False < True
            self.args = sorted(args, key=attrgetter('optional'))

    #---------------------------------------------------------------------------
    
    def gen_init(self):
        """Return the source code for the class's __init__ method."""
        ind = ' '*4
        s = ''

        args = ([PyArg('self', optional=False)] + self.args)
        s = gen_signature('__init__', args, level=1)
            
        # Set members
        for a in self.args:
            if a.mutable:
                s += '\n'
                s += f"{ind*2}self.{a.name} = {'[]' if a.array else '{}'}\n"
                s += f'{ind*2}if {a.name} is not None:\n'
                s += f'{ind*3}self.{a.name} = {a.name}\n'
            else:
                s += f'{ind*2}self.{a.name} = {a.name}\n'
        if len(self.args) == 0:
            s += f'{ind*2}pass\n'
            
        return s

    #---------------------------------------------------------------------------

    def gen_dictify(self):
        """Return the source code for this class's dictify() function.
        """
        s = f"""
    def dictify(self):
        {heredoc}Return a json-encodable object representing a {self.name}.{heredoc}
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
    {heredoc}{self.doc}{heredoc}
"""
        s += self.gen_init()
        s += self.gen_dictify()
        s += self.gen_str()
        return s

#-------------------------------------------------------------------------------

class PyMethod:
    def __init__(self, name, args=None):
        self.name = name

        self.args = []
        if args is not None:
            self.args = args

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
