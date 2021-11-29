# w3c.py - convert W3C recommendations in HTML format to a Word file

import os
import re
import sys
import lxml.etree as et
from lxml import objectify

from docx_common import add_char_run, add_pinyin_run, add_text_run, add_html_run
from docx_common import new_paragraph, add_text_paragraph, add_heading, black
from docx_common import add_page_break, add_internal_link, add_hyperlink

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

def coalesce(s):
    """Coalesce multiple whitespace characters into a single space char."""
    return re.sub(r'\s+', ' ', s)

#-------------------------------------------------------------------------------

def do_eg(nd, doc, refs):
    # One paragraph for everyting
    p = new_paragraph(doc, style='Code')

    if nd.text is not None:
        add_text_run(p, nd.text.strip(), font='Consolas', sz=9)

# -----------------------------------------------------------------------------

def do_emph(nd, p, bold=None, italic=None, strike=None):
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
                s = coalesce(s)
        if len(nd) == 0:
            s = s.rstrip()
        if len(s) > 0:
            add_text_run(p, s, bold=bold, italic=italic, strike=strike)

    # Elements under <emph>: phrase, 
    
    # Process any eventual sub-elements.
    for k in nd:
        if k.tag == 'phrase':
            do_phrase(k, p)
        else:
            m = f'Unexpected tag "{k.tag}" inside an <emph> element'
            raise RuntimeError(m)

        if k.tail:
            # Note k.tail only gets stripped on the right side, not the
            # left. On the left side we coalesce, assuming there was something
            # else before us.
            s = k.tail.rstrip()
            s = coalesce(s)
            if len(s) > 0:
                add_text_run(p, s, bold=bold, italic=italic, strike=strike)

#-------------------------------------------------------------------------------

def do_xspecref(nd, p):
    print(f'do_xspecref: tag={nd.tag}, srcline={nd.sourceline}')
    url = nd.attrib['href']
    text = nd.text.strip()
    add_hyperlink(p, text, url)

#-------------------------------------------------------------------------------

def do_loc(nd, p):
    url = nd.attrib['href']
    text = nd.text.strip()
    add_hyperlink(p, text, url)

#-------------------------------------------------------------------------------

def do_specref(nd, p, refs):
    ref = nd.attrib['ref']
    text = refs[ref]
    add_internal_link(p, text, text)

#-------------------------------------------------------------------------------

def do_phrase(nd, p):
    # diff == add/chg, keep it, del ignore it
    diff = nd.attrib['diff']
    if diff == 'del':
        return
    elif diff not in ['chg', 'add']:
        m = f'Unexpected diff attribute value "{diff}" in a <phrase> element'
        raise RuntimeError(m)

    # Elements under <phrase>: loc, xspecref, code, 
            
    # Process any eventual sub-elements.
    for k in nd:
        if k.tag == 'loc':
            do_loc(k, p)
        elif k.tag == 'xspecref':
            do_xspecref(k, p)
        elif k.tag == 'code':
            do_code(k, p)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <div> element'
            raise RuntimeError(m)

#-------------------------------------------------------------------------------

def do_code(nd, p):
    # Text before any eventual sub-element
    if nd.text is not None:
        s = nd.text.lstrip()
        if len(nd) == 0:
            s = coalesce(s)
        else:
            # There are sub-elements, don't just strip, coalesce whitespace
            s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

    # Elements under <code>: loc
            
    # Process any eventual sub-elements.
    for k in nd:
        if k.tag == 'loc':
            do_loc(k, p)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <code> element'
            raise RuntimeError(m)

#-------------------------------------------------------------------------------

def do_head(nd, doc, refs, level):
    head = nd.text.strip() if nd.text is not None else '<empty>'
    add_heading(doc, level, head)

#-------------------------------------------------------------------------------

def do_p(nd, doc, refs):
    # One paragraph for everyting (passed onto child elements)
    p = new_paragraph(doc)

    # Text before any eventual sub-element. Left-strip always, because HTML
    # authors usually add whitespace for legibility. Right-strip (for the same
    # reason) but only if there are no sub-elements, otherwise we might
    # concatenate two words together.
    if nd.text is not None:
        s = nd.text.lstrip()
        if len(nd) == 0:
            s = coalesce(s)
        else:
            # There are sub-elements, don't just strip, coalesce whitespace
            s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

    # Elements under <p>: phrase, xspecref, loc, specref, emph, code
            
    # Process any eventual sub-elements.
    for k in nd:
        s = k.text.strip() if k.text else ''
        if k.tag in ['phrase']:
            do_phrase(k, p)
        elif k.tag == 'xspecref':
            do_xspecref(k, p)
        elif k.tag == 'loc':
            do_loc(k, p)
        elif k.tag in ['specref']:
            do_specref(k, p, refs)
        elif k.tag == 'emph':
            do_emph(k, p, italic=True)
        elif k.tag == 'code':
            do_code(k, p)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <p> element'
            raise RuntimeError(m)
            
        if k.tail:
            # Note k.tail only gets stripped on the right side, not the
            # left. On the left side we coalesce, assuming there was something
            # else before us.
            s = k.tail.strip()
            s = coalesce(s)
            if len(s) > 0:
                add_text_run(p, s)

#-------------------------------------------------------------------------------

def do_note(nd, doc, refs):
    role = nd.attrib['role'].capitalize()

    p = new_paragraph(doc)
    add_text_run(p, role, font='Arial', sz=10, bold=True)

    for k in nd:
        if k.tag == 'p':
            do_p(k, doc, refs)
        elif k.tag == 'eg':
            do_eg(k, doc, refs)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <note> element'
            raise RuntimeError(m)

#-------------------------------------------------------------------------------

def do_table(nd, doc, refs):
    pass

# -----------------------------------------------------------------------------

def do_div(nd, doc, refs):
    level = int(nd.tag[3])  # 1, 2, 3 or 4

    for k in nd:
        if k.tag == 'head':
            do_head(k, doc, refs, level)
        elif k.tag == 'p':
            do_p(k, doc, refs)
        elif k.tag == 'note':
            do_note(k, doc, refs)
        elif k.tag == 'table':
            do_table(k, doc, refs)
        elif k.tag in ['div1', 'div2', 'div3']:
            do_div(k, doc, refs)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <div> element'
            raise RuntimeError(m)

# -----------------------------------------------------------------------------

def do_header(nd, doc, refs):
    """<header> includes <status> and <abstract>."""
    pass

# -----------------------------------------------------------------------------

def do_body(nd, doc, refs):
    """<body> holds the document content."""
    for k in nd:
        if k.tag in ['div1', 'div2', 'div3']:
            do_div(k, doc, refs)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <spec> element'
            raise RuntimeError(m)

# -----------------------------------------------------------------------------

def do_back(nd, doc, refs):
    pass

# -----------------------------------------------------------------------------

def do_spec(nd, doc, refs):
    """<spec> is the toplevel element in the XML tree."""
    for k in nd:
        if k.tag == 'header':
            do_header(k, doc, refs)
        elif k.tag == 'body':
            do_body(k, doc, refs)
        elif k.tag == 'back':
            do_back(k, doc, refs)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <spec> element'
            raise RuntimeError(m)

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
    # for k, v in specrefs.items():
    #     print(f'{k}: {v}')

    # Write out the contents as Word
    doc = Document('empty.docx')

    # Set normal margins
    s = doc.sections[0]
    s.left_margin = Inches(0.59)
    s.right_margin = Inches(0.59)
    s.top_margin = Inches(0.59)
    s.bottom_margin = Inches(0.59)

    # Get the document contents
    do_spec(root, doc, specrefs)
          
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
