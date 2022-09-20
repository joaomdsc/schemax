# canonicalize.py - 

import os
import sys
import lxml.etree as et
from lxml import objectify

#-------------------------------------------------------------------------------
    
def canonicalize(filepath):
    filepath = filepath

    # Parse XML file, ignoring comments
    p = et.XMLParser(remove_comments=True)
    root = objectify.parse(filepath, parser=p).getroot()

    # Overwrite, canonicalized
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(et.tostring(root, method='c14n2').decode())
    
#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xml filepath>')
        exit(-1)
    filepath = sys.argv[1]

    canonicalize(filepath)
