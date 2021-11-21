# pyclass_t.py

import unittest
from pyclass import gen_signature, PyArg, PyClass, PyModule

# -----------------------------------------------------------------------------

class SignatureTest(unittest.TestCase):

    def test01(self):
        """No arguments"""
        s = 'def func():\n'
        self.assertEqual(s, gen_signature('func', []))

    def test02(self):
        """One mandatory argument"""
        s = 'def func(abc):\n'
        self.assertEqual(s, gen_signature('func', [PyArg('abc', optional=False)]))

    def test03(self):
        """One optional argument"""
        s = 'def func(abc=None):\n'
        self.assertEqual(s, gen_signature('func', [PyArg('abc')]))

    def test04(self):
        """Two arguments, optional and/or mandatory"""
        s = 'def func(abc=None, xyz=None):\n'
        args = [PyArg('abc'), PyArg('xyz')]
        self.assertEqual(s, gen_signature('func', args))
        s = 'def func(abc, xyz=None):\n'
        args = [PyArg('abc', optional=False), PyArg('xyz')]
        self.assertEqual(s, gen_signature('func', args))
        s = 'def func(abc=None, xyz):\n'
        args = [PyArg('abc'), PyArg('xyz', optional=False)]
        self.assertEqual(s, gen_signature('func', args))
        s = 'def func(abc, xyz):\n'
        args = [PyArg('abc', optional=False), PyArg('xyz', optional=False)]
        self.assertEqual(s, gen_signature('func', args))

    def test05(self):
        """Two very long arguments"""
        name1 = 'a'*30
        name2 = 'b'*30
        s = f"""def func({name1}=None,
        {name2}=None):\n"""
        args = [PyArg(name1), PyArg(name2)]
        self.assertEqual(s, gen_signature('func', args))

    def test06(self):
        """An init function with long arguments"""
        name1 = 'a'*30
        name2 = 'b'*30
        s = f"""def __init__(self, {name1}=None,
        {name2}=None, **kwargs):\n"""
        args = [
            PyArg('self', optional=False),
            PyArg(name1), PyArg(name2),
            PyArg('**kwargs', optional=False)]
        self.assertEqual(s, gen_signature('__init__', args))
        
# -----------------------------------------------------------------------------

class PyClassTest(unittest.TestCase):

    def test01(self):
        """Simple python class"""
        with open('test01.py') as f:
            s = f.read()
        doc = 'The Abc class represents some real-world object.'
        args = [
            PyArg('x', optional=False),
            PyArg('y', optional=False),
            PyArg('col')]
        kl = PyClass('Abc', doc, args)
        
        self.assertEqual(s, str(kl))

    def test02(self):
        """Simple python module"""
        with open('mod01.py') as f:
            s = f.read()

        # Abc class
        doc = 'The Abc class represents some real-world object.'
        args = [
            PyArg('x', optional=False),
            PyArg('y', optional=False),
            PyArg('col')]
        kl1 = PyClass('Abc', doc, args)

        # Xyz class
        doc = 'And now for a completely different class.'
        args = [
            PyArg('id_', optional=False),
            PyArg('name', optional=False),
            PyArg('tokens', mutable=True, array=True),
            PyArg('sub_elems', mutable=True, array=True, classname='Process'),
        ]
        kl2 = PyClass('Xyz', doc, args)

        mod = PyModule('mod01', klasses=[kl1, kl2])
        
        self.assertEqual(s, str(mod))
        
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main(verbosity=2)
