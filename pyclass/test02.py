# test02.py - replicate mod02.py

from pyclass import PyArg, PyClass, PyModule

#-------------------------------------------------------------------------------

def grand_parent():
    args_req = [
        PyArg('aa', None),
        PyArg('bb', None),
    ]
    args_opt = [
        PyArg('label', None),
        PyArg('process', None),
    ]
    return PyClass('GrandParent', None, args_req=args_req, args_opt=args_opt)

#-------------------------------------------------------------------------------

def parent(gp):
    args_req = [
        PyArg('x', None),
        PyArg('y', None),
    ]
    args_opt = [
        PyArg('val', None),
        PyArg('cnt', None),
    ]
    return PyClass('Parent', None, args_req=args_req, args_opt=args_opt,
                   parent=gp)

#-------------------------------------------------------------------------------

def child(par):
    args_req = [
        PyArg('id_', None),
        PyArg('name', None),
    ]
    args_opt = [
        PyArg('tokens', dict),
        PyArg('sub_elems', list),
    ]
    return PyClass('Child', None, args_req=args_req, args_opt=args_opt,
                   parent=par)

#-------------------------------------------------------------------------------

def test():
    gp = grand_parent()
    par = parent(gp)
    c = child(par)

    m = PyModule('test_mod_02', [gp, par, c])
    print(m)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    test()