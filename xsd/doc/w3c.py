# w3c.py - convert W3C recommendations in HTML format to a Word file

import os
import re
import sys
import lxml.etree as et
from lxml import objectify

from docx_common import add_char_run, add_pinyin_run, add_text_run, add_html_run
from docx_common import new_paragraph, add_text_paragraph, add_heading, black
from docx_common import add_page_break, add_link

# Writing out to Word .docx files
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT

# Colors
red = RGBColor(0xff, 0x0, 0x0)
success = RGBColor(0xde, 0xf1, 0xde)  # (222, 241, 222) dec
warning = RGBColor(0xfc, 0xef, 0xdc)  # (252, 239, 220) dec

#-------------------------------------------------------------------------------

def lcoalesce(s):
    """Coalesce multiple whitespace characters into a single space char."""
    # return re.sub(r'^\s+', ' ', s)
    return re.sub(r'\s+', ' ', s)

def rcoalesce(s):
    # return re.sub(r'\s+$', ' ', s)
    return re.sub(r'\s+', ' ', s)

# -----------------------------------------------------------------------------

def get_i_text(nd, p, bold=None, italic=None, strike=None):
    # Text before any eventual sub-element. See get_h2 for additional info.
    # This is an element inside a <strong>, <em>, or <del>
    if nd.text:
        s = nd.text
        if len(s) > 0:
            if s[0] not in ' \t\r\n':
                # We're assuming this is not at the beginning of a paragraph,
                # there's some other text *before*, and we want to separate
                # ourselves from it with at least one space.
                s = ' ' + s
            else:
                s = lcoalesce(s)
        if len(nd) == 0:
            s = s.rstrip()
        if len(s) > 0:
            add_text_run(p, s, bold=bold, italic=italic, strike=strike)

    # Process any eventual sub-elements.
    for k in nd:
        s = k.text.strip() if k.text else ''
        if k.tag == 'i' and len(s) > 0:
            add_text_run(p, s, bold=bold, italic=italic, strike=strike)
        if k.tail:
            # Note k.tail only gets stripped on the right side, not the
            # left. On the left side we lcoalesce, assuming there was something
            # else before us.
            s = k.tail.rstrip()
            s = lcoalesce(s)
            if len(s) > 0:
                add_text_run(p, s, bold=bold, italic=italic, strike=strike)

#-------------------------------------------------------------------------------

def handle_para(nd, doc, refs):
    # One paragraph for everyting
    p = new_paragraph(doc)

    # Text before any eventual sub-element. Left-strip always, because HTML
    # authors usually add whitespace for legibility. Right-strip (for the same
    # reason) but only if there are no sub-elements, otherwise we might
    # concatenate two words together.
    if nd.text is not None:
        s = nd.text.lstrip()
        if len(nd) == 0:
            s = rcoalesce(s)
        else:
            # There are sub-elements, don't just strip, coalesce whitespace
            s = rcoalesce(s)
        if len(s) > 0:
            add_text_run(p, s)
            
    # Process any eventual sub-elements.
    for k in nd:
        s = k.text.strip() if k.text else ''
        if k.tag in ['specref']:
            ref = k.attrib['ref']
            title = refs[ref]
            # add_text_run(p, refs[ref])
            add_link(p, title, title)
        elif k.tag == 'emph':
            get_i_text(k, p, italic=True)
        if k.tail:
            # Note k.tail only gets stripped on the right side, not the
            # left. On the left side we lcoalesce, assuming there was something
            # else before us.
            s = k.tail.rstrip()
            s = lcoalesce(s)
            if len(s) > 0:
                add_text_run(p, s)

# -----------------------------------------------------------------------------

def handle_div(nd, doc, refs):
    level = int(nd.tag[3])  # 1, 2, 3 or 4
    id_ = nd.attrib['id'] if 'id' in nd.attrib else None

    # print(f'<div{level} id="{id_}">')
    for k in nd:
        if k.tag == 'head':
            title = k.text.strip() if k.text is not None else '<empty'
            # print(f'  title="{title}"')
            add_heading(doc, level, title)
        elif k.tag == 'p':
            handle_para(k, doc, refs)
        elif k.tag.startswith('div'):
            handle_div(k, doc, refs)

# -----------------------------------------------------------------------------

def get_specrefs(nd, obj):
    id_ = None
    for k in nd:
        if k.tag == 'head':
            continue
        elif k.tag.startswith('div') or k.tag in ['schemaComp', 'constraintnote']:
            id_ = k.attrib['id'] if 'id' in k.attrib else None
            x = k.find('.//head')
            title = x.text.strip() if x.text is not None else '<empty>'
            obj[id_] = title
            obj = get_specrefs(k, obj)
        else:
            obj = get_specrefs(k, obj)

    return obj

# -----------------------------------------------------------------------------

def to_docx(filepath):
    # Parse XML file, ignoring comments
    p = et.XMLParser(remove_comments=True)
    root = objectify.parse(filepath, parser=p).getroot()
    print(root.tag)

    specrefs = get_specrefs(root, {})
    for k, v in specrefs.items():
        print(f'{k}: {v}')

    # Write out the contents as Word
    doc = Document('empty.docx')

    # Get the document contents
    nd = root.find('.//body')
    for k in nd:
        if not k.tag.startswith('div') or k.tag[3] not in ['1', '2', '3', '4']:
            continue
        handle_div(k, doc, specrefs)

    # Set normal margins
    s = doc.sections[0]
    s.left_margin = Inches(0.59)
    s.right_margin = Inches(0.59)
    s.top_margin = Inches(0.59)
    s.bottom_margin = Inches(0.59)
          
    # Output a .docx file in the current directory
    base, _ = os.path.splitext(filepath)
    outpath = f'{base}.docx'
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
