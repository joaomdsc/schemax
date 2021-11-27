# w3c.py - convert W3C recommendations in HTML format to a Word file

import sys
import lxml.etree as et
from lxml import objectify

from docx_common import add_char_run, add_pinyin_run, add_text_run, add_html_run
from docx_common import new_paragraph, add_text_paragraph, add_heading, black
from docx_common import add_page_break

# Writing out to Word .docx files
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT

# Colors
red = RGBColor(0xff, 0x0, 0x0)
success = RGBColor(0xde, 0xf1, 0xde)  # (222, 241, 222) dec
warning = RGBColor(0xfc, 0xef, 0xdc)  # (252, 239, 220) dec

# -----------------------------------------------------------------------------

def handle_para(nd, doc):
    s = ''

    if nd.text is not None:
        s += nd.text.lstrip()
    for k in nd:
        if k.text is not None:
            s += k.text.lstrip()
        if k.tail is not None:
            s += k.tail.rstrip()

    # Output a text paragraph to the document
    p = new_paragraph(doc)
    add_text_run(p, s)

# -----------------------------------------------------------------------------

def handle_div(nd, doc):
    level = int(nd.tag[3])  # 1, 2, 3 or 4
    id_ = nd.attrib['id'] if 'id' in nd.attrib else None

    print(f'<div{level} id="{id_}">')
    for k in nd:
        if k.tag == 'head':
            title = k.text.strip() if k.text is not None else '<empty'
            print(f'  title="{title}"')
            add_heading(doc, level, title)
        elif k.tag == 'p':
            handle_para(k, doc)
        elif k.tag.startswith('div'):
            handle_div(k, doc)

# -----------------------------------------------------------------------------

def to_docx(filepath):
    # Parse XML file, ignoring comments
    p = et.XMLParser(remove_comments=True)
    root = objectify.parse(filepath, parser=p).getroot()
    nd = root.find('.//body')
    print(nd.tag)

    # Write out the contents as Word
    doc = Document('empty.docx')

    # Get the document contents
    for k in nd:
        if not k.tag.startswith('div') or k.tag[3] not in ['1', '2', '3', '4']:
            continue
        handle_div(k, doc)

    # Set normal margins
    s = doc.sections[0]
    s.left_margin = Inches(0.59)
    s.right_margin = Inches(0.59)
    s.top_margin = Inches(0.59)
    s.bottom_margin = Inches(0.59)
          
    # Output a .docx file in the current directory
    outpath = 'xsd1_structures.docx'
    doc.save(outpath)
    
# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
    
if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xml filepath>')
        exit(-1)
    filepath = sys.argv[1]

    to_docx(filepath)
