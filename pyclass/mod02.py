# mod02.py

import json

#-------------------------------------------------------------------------------

class GrandParent:
    def __init__(self, aa, bb, label=None, process=None):
        self.aa = aa
        self.bb = bb
        self.label = label
        self.process = process

    def dictify(self):
        """Return a json-encodable object representing a Abc."""
        obj = {}
        for k, v in self.__dict__.items():
            if not (v is None or v == [] or v == {}):
                obj[k] = v

        return obj

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

#-------------------------------------------------------------------------------

class Parent(GrandParent):
    def __init__(self, aa, bb, x, y, label=None, process=None, val=None,
                 cnt=None):
        super.__init__(aa, bb, label=label, process=process)
        self.x = x
        self.y = y
        self.val = val
        self.cnt = cnt

    def dictify(self):
        """Return a json-encodable object representing a Abc."""
        obj = super().dictify()
        for k, v in self.__dict__.items():
            if not (v is None or v == [] or v == {}):
                obj[k] = v

        return obj

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

#-------------------------------------------------------------------------------

class Child(Parent):
    def __init__(self, aa, bb, x, y, id_, name, label=None, process=None,
                 val=None cnt=None, tokens=None, sub_elems=None):
        super().__init__(aa, bb, x, y, label=label, process=process, val=val,
                         cnt=cnt)
        self.id_ = id_
        self.name = name

        self.tokens = []
        if tokens is not None:
            self.tokens = tokens

        self.sub_elems = []
        if sub_elems is not None:
            self.sub_elems = sub_elems

    def dictify(self):
        """Return a json-encodable object representing a Xyz."""
        obj = super().dictify()
        for k, v in self.__dict__.items():
            if not (v is None or v == [] or v == {}):
                obj[k] = v
        # Json-encode the python objects inside collections, and add them if
        # they're not empty.

        if self.sub_elems is not None:
            obj['sub_elems'] = [x.dictify() for x in self.sub_elems]

        return obj

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
