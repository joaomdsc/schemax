# xsd_tree.py - show all grammar productions from a schema

import os
import sys
import json
import requests
import lxml.etree as et
from lxml import objectify

ind = ' '*4

#-------------------------------------------------------------------------------

def tag(nd):
    return et.QName(nd).localname

#-------------------------------------------------------------------------------

def do_node(nd, path):
    """path is the list of parent nodes"""
    level = len(path)  # indentation level
    
    print(f'{ind*level}{tag(nd)}')
    for k in nd:
        do_node(k, path + [tag(nd)])

#-------------------------------------------------------------------------------

def xsd_tree(filepath):
    # Ignore comments
    p = et.XMLParser(remove_comments=True)
    root = objectify.parse(filepath, parser=p).getroot()

    do_node(root, [])

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xsd filepath>')
        exit(-1)
    filepath = sys.argv[1]

    xsd_tree(filepath)
