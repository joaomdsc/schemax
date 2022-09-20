# test.py

from pyclass import PyArg, PyClass

#-------------------------------------------------------------------------------

def test():
    doc = 'The Abc class represents some real-world object.'
    args = [
        PyArg('x', None, optional=False),
        PyArg('y', None, optional=False),
        PyArg('pars', list, optional=False),
        PyArg('col', None),
        PyArg('tokens', list),
        PyArg('mapping', dict),
    ]
    kl = PyClass('Abc', doc, args)

    print(kl)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    test()