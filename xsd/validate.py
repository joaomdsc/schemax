# validate.py -

import sys
import lxml.etree as et

def validate(xsd_filepath, xml_filepath):
    # Construct the XMLSchema validator
    doc = et.parse(xsd_filepath)
    xsd = et.XMLSchema(doc)

    # Validate an instance document
    doc = et.parse(xml_filepath)
    r = xsd.validate(doc)
    if not r:
        print(xsd.error_log.last_error)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <xsd filepath> <xml_filepath>')
        exit(-1)
    xsd_filepath = sys.argv[1]
    xml_filepath = sys.argv[2]

    validate(xsd_filepath, xml_filepath)
