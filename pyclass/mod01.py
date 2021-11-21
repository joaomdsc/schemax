# mod01.py

import json

#-------------------------------------------------------------------------------

class Abc:
    """The Abc class represents some real-world object."""
    def __init__(self, x, y, col=None):
        self.x = x
        self.y = y
        self.col = col

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

class Xyz:
    """And now for a completely different class."""
    def __init__(self, id_, name, tokens=None, sub_elems=None):
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
        obj = {}
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
