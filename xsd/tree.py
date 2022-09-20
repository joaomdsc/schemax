# tree.py - generic tree class, supporting tree creation from edges

import json

#-------------------------------------------------------------------------------

class FoundException(Exception):
    def __init__(self, msg, obj):
        super().__init__(msg)
        self.obj = obj

#-------------------------------------------------------------------------------

class Node:
    def __init__(self, payload):
        self.payload = payload  # simple type or object
        self.kids = []

    def dictify(self):
        return {
            'payload': self.payload.dictify(),
            'kids': [x.dictify() for x in self.kids],
        }

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

    def show(self, level):
        ind = ' '*4
        s = f'{ind*level}{self.payload}\n'
        for k in self.kids:
            s += k.show(level+1)
        return s

    def is_parent(self, payload):
        # True if 'payload' is an immediate child of self
        for k in self.kids:
            if k.payload == payload:
                return True
        return False
        
    def find(self, payload):
        """Look for 'payload' in self's entire sub-tree"""
        if self.payload == payload:
            raise FoundException('Found node', self)
        for k in self.kids:
            k.find(payload)

    def ancestry(self, payload, ancestors):
        """Return the list of ancestors for the node with this 'payload'."""
        if self.payload == payload:
            raise FoundException('Found node', ancestors)
        for k in self.kids:
            k.ancestry(payload, ancestors + [self.payload])

    def traverse(self, arr):
        # FIXME implement a generator function
        arr.append(self.payload)
        for k in self.kids:
            arr = k.traverse(arr)
        return arr

    def parents(self, arr):
        if len(self.kids) > 0:
            arr.append(self.payload)
        for k in self.kids:
            arr = k.parents(arr)
        return arr

    def children(self, obj):
        if len(self.kids) > 0:
            # FIXME this only works for hashable payloads
            obj[self.payload] = [k.payload for k in self.kids]
        for k in self.kids:
            obj = k.children(obj)
        return obj
    
#-------------------------------------------------------------------------------

def find(root, payload):
    """Look for 'payload' in tree 'root'."""
    try:
        root.find(payload)
    except FoundException as e:
        return e.obj

#-------------------------------------------------------------------------------

class TreeSet:
    """A set of trees"""
    def __init__(self):
        self.trees = []

    def dictify(self):
        return [t.dictify() for t in self.trees]

    # def __str__(self):
    #     return json.dumps(self.dictify(), indent=4)

    def __str__(self):
        s = ''
        for t in self.trees:
            s += t.show(0)
        return s

    def add_edge(self, parent, child):
        # If this parent already exists, add child to it
        # print(f'"{parent}" => "{child}"')
        for t in self.trees:
            nd = find(t, parent)
            if nd is not None:
                # Found parent. If child is one of the roots in trees, move it,
                # else create a new Node
                for t in self.trees:
                    if t.payload == child:
                        nd.kids.append(t)
                        self.trees.remove(t)
                        return
                nd.kids.append(Node(child))
                return

        # Start a new tree
        nd = Node(parent)
        self.trees.append(nd)
        # If child is one a root in trees, move it, else create a new Node
        for t in self.trees:
            if t.payload == child:
                nd.kids.append(t)
                self.trees.remove(t)
                return
        nd.kids.append(Node(child))

    def child_of(self, child, parent):
        # First we need to find 'parent' (we assume it's there)
        for t in self.trees:
            nd = find(t, parent)
            if nd is not None:
                # Then we search the immediate children of the parent
                return nd.is_parent(child)
        return False

    def ancestry(self, payload):
        """Return the list of payload's ancestors (as a list of payloads)"""
        for t in self.trees:
            try:
                t.ancestry(payload, [])
            except FoundException as e:
                return e.obj
        return []

    def traverse(self):
        """Generate the list of nodes from a depth-first traversal."""
        # FIXME implement a generator function
        arr = []
        for t in self.trees:
            arr = t.traverse(arr)
        return arr

    def parents(self):
        """Generate the list of nodes that are parents.

        Parents are nodes that have len(kids) > 0."""
        arr = []
        for t in self.trees:
            arr = t.parents(arr)
        return arr

    def children(self):
        """Generate the dictionary of (head, members)."""
        obj = {}
        for t in self.trees:
            obj = t.children(obj)
        return obj

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
