
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
