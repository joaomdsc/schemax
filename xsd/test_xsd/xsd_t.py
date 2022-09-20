# xsd_t.py

import unittest
import lxml.etree as et

def validate(xsd_filepath, xml_filepath):
    # Construct the XMLSchema validator
    xsd = et.XMLSchema(et.parse(xsd_filepath))

    # Validate an instance document
    return xsd.validate(et.parse(xml_filepath))

#-------------------------------------------------------------------------------

class AllTest(unittest.TestCase):

    def test_all_000_empty(self):
        self.assertFalse(validate('all.xsd', 'all_00.xml'))

    def test_all_001_ordered(self):
        self.assertTrue(validate('all.xsd', 'all_01.xml'))

    def test_all_002_disordered(self):
        self.assertTrue(validate('all.xsd', 'all_02.xml'))

    def test_all_003_one_missing(self):
        self.assertFalse(validate('all.xsd', 'all_03.xml'))

    def test_all_004_one_duplicated(self):
        self.assertFalse(validate('all.xsd', 'all_04.xml'))

#-------------------------------------------------------------------------------

class ChoiceTest(unittest.TestCase):

    def test_choice_000_empty(self):
        self.assertFalse(validate('choice.xsd', 'choice_00.xml'))

    def test_choice_001_one_child(self):
        self.assertTrue(validate('choice.xsd', 'choice_01.xml'))

    def test_choice_002_two_children(self):
        self.assertFalse(validate('choice.xsd', 'choice_02.xml'))

    # Valid complex choices
    def test_choice_003_valid_complex(self):
        self.assertTrue(validate('choice.xsd', 'choice02_01.xml'))

    def test_choice_004_valid_complex(self):
        self.assertTrue(validate('choice.xsd', 'choice02_02.xml'))

    def test_choice_005_valid_complex(self):
        self.assertTrue(validate('choice.xsd', 'choice02_03.xml'))

    def test_choice_006_valid_complex(self):
        self.assertTrue(validate('choice.xsd', 'choice02_04.xml'))

    def test_choice_007_valid_complex(self):
        self.assertTrue(validate('choice.xsd', 'choice02_05.xml'))

    def test_choice_008_valid_complex(self):
        self.assertTrue(validate('choice.xsd', 'choice02_06.xml'))

    # Invalid complex choices
    def test_choice_009_invalid_complex(self):
        self.assertFalse(validate('choice.xsd', 'choice02_07.xml'))

    def test_choice_010_invalid_complex(self):
        self.assertFalse(validate('choice.xsd', 'choice02_08.xml'))

    def test_choice_011_invalid_complex(self):
        self.assertFalse(validate('choice.xsd', 'choice02_09.xml'))

    def test_choice_012_invalid_complex(self):
        self.assertFalse(validate('choice.xsd', 'choice02_10.xml'))

    def test_choice_013_invalid_complex(self):
        self.assertFalse(validate('choice.xsd', 'choice02_11.xml'))

#-------------------------------------------------------------------------------

class SequenceTest(unittest.TestCase):

    def test_seq_000_empty(self):
        self.assertFalse(validate('sequence.xsd', 'seq_00.xml'))

    def test_seq_001_ordered(self):
        self.assertTrue(validate('sequence.xsd', 'seq_01.xml'))

    def test_seq_002_disordered(self):
        self.assertFalse(validate('sequence.xsd', 'seq_02.xml'))

    def test_seq_003_missing(self):
        self.assertFalse(validate('sequence.xsd', 'seq_03.xml'))

    def test_seq_004_too_many(self):
        self.assertFalse(validate('sequence.xsd', 'seq_04.xml'))

    def test_seq_005_unexpected(self):
        self.assertFalse(validate('sequence.xsd', 'seq_05.xml'))

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main(verbosity=2)
