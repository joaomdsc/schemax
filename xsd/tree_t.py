# tree_t.py

import unittest
from x4b.tree import TreeSet

# -----------------------------------------------------------------------------

A = {
    'name': 'BaseElement',
    'attributes': [
        (33, 'id_'),
        (37, 'documentations'),
    ]
}
B = {
    'name': 'DataAssociation',
    'attributes': [
        (87, 'sourceRefs'),
        (90, 'targetRef'),
        (93, 'transformation'),
        (97, 'assignments'),
    ]
}
C = {
    'name': 'DataOutputAssociation',
    'attributes': [
        (9999, 'toto'),
    ]
}
D = {
    'name': 'hello',
    'attributes': [
        (1234, 'foobar'),
    ]
}
# Cbis is not the same object as C, but the contents are identical
Cbis = {
    'name': 'DataOutputAssociation',
    'attributes': [
        (9999, 'toto'),
    ]
}

class TreeT(unittest.TestCase):

    def test_000_empty(self):
        ts = TreeSet()
        self.assertEqual(False, ts.child_of('foo', 'bar'))
        self.assertEqual(False, ts.child_of('bar', 'foo'))
        self.assertEqual([], ts.ancestry('foo'))
        self.assertEqual([], ts.ancestry('bar'))

    # Simple string payload
    def test_001_single_edge(self):
        ts = TreeSet()
        ts.add_edge('A', 'B')
        self.assertEqual(True, ts.child_of('B', 'A'))
        self.assertEqual(False, ts.child_of('A', 'B'))
        self.assertEqual([], ts.ancestry('A'))
        self.assertEqual(['A'], ts.ancestry('B'))

    # Complex payload
    def test_002_single_edge_payload(self):
        ts = TreeSet()
        ts.add_edge(A, B)
        self.assertEqual(True, ts.child_of(B, A))
        self.assertEqual(False, ts.child_of(A, B))
        self.assertEqual([], ts.ancestry(A))
        self.assertEqual([A], ts.ancestry(B))
              
    def test_003_two_edges_chain(self):
        ts = TreeSet()
        ts.add_edge('A', 'B')
        ts.add_edge('B', 'C')
        self.assertEqual(True, ts.child_of('B', 'A'))
        self.assertEqual(True, ts.child_of('C', 'B'))
        self.assertEqual(False, ts.child_of('C', 'A'))
        self.assertEqual(False, ts.child_of('B', 'C'))
        self.assertEqual(False, ts.child_of('A', 'B'))
        self.assertEqual(False, ts.child_of('A', 'C'))
        self.assertEqual([], ts.ancestry('A'))
        self.assertEqual(['A'], ts.ancestry('B'))
        self.assertEqual(['A', 'B'], ts.ancestry('C'))
              
    def test_004_two_edges_chain_payload(self):
        ts = TreeSet()
        ts.add_edge(A, B)
        ts.add_edge(B, C)
        self.assertEqual(True, ts.child_of(B, A))
        self.assertEqual(True, ts.child_of(C, B))
        self.assertEqual(False, ts.child_of(C, A))
        self.assertEqual(False, ts.child_of(B, C))
        self.assertEqual(False, ts.child_of(A, B))
        self.assertEqual(False, ts.child_of(A, C))
        self.assertEqual([], ts.ancestry(A))
        self.assertEqual([A], ts.ancestry(B))
        self.assertEqual([A, B], ts.ancestry(C))
               
    def test_005_two_edges_triangle(self):
        ts = TreeSet()
        ts.add_edge('A', 'B')
        ts.add_edge('A', 'C')
        self.assertEqual(True, ts.child_of('B', 'A'))
        self.assertEqual(True, ts.child_of('C', 'A'))
        self.assertEqual(False, ts.child_of('A', 'C'))
        self.assertEqual(False, ts.child_of('A', 'B'))
        self.assertEqual(False, ts.child_of('B', 'C'))
        self.assertEqual(False, ts.child_of('C', 'B'))
        self.assertEqual([], ts.ancestry('A'))
        self.assertEqual(['A'], ts.ancestry('B'))
        self.assertEqual(['A'], ts.ancestry('C'))
               
    def test_006_two_edges_triangle(self):
        ts = TreeSet()
        ts.add_edge(A, B)
        ts.add_edge(A, C)
        self.assertEqual(True, ts.child_of(B, A))
        self.assertEqual(True, ts.child_of(C, A))
        self.assertEqual(False, ts.child_of(A, C))
        self.assertEqual(False, ts.child_of(A, B))
        self.assertEqual(False, ts.child_of(B, C))
        self.assertEqual(False, ts.child_of(C, B))
        self.assertEqual([], ts.ancestry(A))
        self.assertEqual([A], ts.ancestry(B))
        self.assertEqual([A], ts.ancestry(C))
               
    def test_007_three_edges(self):
        ts = TreeSet()
        ts.add_edge('A', 'B')
        ts.add_edge('A', 'C')
        ts.add_edge('A', 'D')
        self.assertEqual(True, ts.child_of('B', 'A'))
        self.assertEqual(True, ts.child_of('C', 'A'))
        self.assertEqual(True, ts.child_of('D', 'A'))
        
        self.assertEqual(False, ts.child_of('A', 'B'))
        self.assertEqual(False, ts.child_of('A', 'C'))
        self.assertEqual(False, ts.child_of('A', 'D'))
        
        self.assertEqual(False, ts.child_of('B', 'C'))
        self.assertEqual(False, ts.child_of('C', 'D'))
        self.assertEqual([], ts.ancestry('A'))
        self.assertEqual(['A'], ts.ancestry('B'))
        self.assertEqual(['A'], ts.ancestry('C'))
        self.assertEqual(['A'], ts.ancestry('D'))
               
    def test_008_disjoint_trees(self):
        ts = TreeSet()
        ts.add_edge('A', 'B')
        ts.add_edge('A', 'C')
        ts.add_edge('C', 'D')
        ts.add_edge('C', 'E')
        ts.add_edge('F', 'G')
        ts.add_edge('F', 'K')
        ts.add_edge('G', 'H')
        ts.add_edge('G', 'J')
        ts.add_edge('H', 'I')
        ts.add_edge('K', 'L')
        ts.add_edge('L', 'M')
        ts.add_edge('L', 'N')
        ts.add_edge('O', 'P')
        ts.add_edge('O', 'Q')
        ts.add_edge('O', 'U')
        ts.add_edge('O', 'V')
        ts.add_edge('O', 'W')
        ts.add_edge('Q', 'R')
        ts.add_edge('R', 'S')
        ts.add_edge('R', 'T')
        self.assertEqual([], ts.ancestry('A'))
        self.assertEqual(['A', 'C'], ts.ancestry('D'))
        self.assertEqual(['F', 'G', 'H'], ts.ancestry('I'))
        self.assertEqual(['F', 'K', 'L'], ts.ancestry('M'))
        self.assertEqual(['O', 'Q', 'R'], ts.ancestry('T'))

        nodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W']
        self.assertEqual(nodes, ts.traverse())

    def test_009_equality(self):
        ts = TreeSet()
        ts.add_edge(A, C)
        self.assertEqual(True, ts.child_of(C, A))
        self.assertEqual(True, ts.child_of(Cbis, A))

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main(verbosity=2)
