# w3c.py - convert W3C recommendations in HTML format to a Word file

import os
import re
import sys
import lxml.etree as et
from lxml import objectify

from docx_common import black
from docx_common import add_text_run, new_paragraph, add_heading
from docx_common import add_internal_link, add_hyperlink

# Writing out to Word .docx files
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT

#-------------------------------------------------------------------------------

def coalesce(s):
    """Coalesce multiple whitespace characters into a single space char."""
    return re.sub(r'\s+', ' ', s)

#-------------------------------------------------------------------------------

def do_eg(nd, doc, refs):
    # One paragraph for everyting
    p = new_paragraph(doc, style='Code')

    if nd.text is not None:
        add_text_run(p, nd.text, font='Consolas', sz=9)

# -----------------------------------------------------------------------------

def do_emph(nd, p, italic=None):
    # Text before any eventual sub-element.
    if nd.text is not None:
        s = nd.text
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s, italic=italic)

    # Elements under <emph>: phrase, 
    
    # Process any eventual sub-elements.
    for k in nd:
        if k.tag == 'phrase':
            do_phrase(k, p)
        else:
            m = f'Unexpected tag "{k.tag}" inside an <emph> element'
            raise RuntimeError(m)

    if nd.tail:
        s = nd.tail
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s, italic=italic)

#-------------------------------------------------------------------------------

def do_xspecref(nd, p):
    url = nd.attrib['href']
    text = nd.text.strip()
    add_hyperlink(p, text, url)
            
    if nd.tail:
        s = nd.tail
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

#-------------------------------------------------------------------------------

def do_loc(nd, p, prev_no_space=False):
    url = nd.attrib['href']
    # FIXME there are newlines inside this nd.text
    s = nd.text.strip()
    if prev_no_space:
        s = ' ' + s
    add_hyperlink(p, s, url)
            
    if nd.tail:
        s = nd.tail
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

#-------------------------------------------------------------------------------

def do_specref(nd, p, refs):
    ref = nd.attrib['ref']
    text = refs[ref]
    add_internal_link(p, text, text)
            
    if nd.tail:
        s = nd.tail
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

#-------------------------------------------------------------------------------

def do_phrase(nd, p):
    # Attributes: diff == add/chg: keep it, del: ignore it
    diff = nd.attrib['diff']
    if diff not in ['chg', 'add', 'del']:
        m = f'Unexpected diff attribute value "{diff}" in a <phrase> element'
        raise RuntimeError(m)

    # Text before any eventual sub-element
    if nd.text is not None:
        s = nd.text
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

    # Elements under <phrase>: loc, xspecref, code, 
            
    # Process any eventual sub-elements.
    if diff != 'del':
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

    # Always process tail, regardless of 'diff' value
    if nd.tail:
        s = nd.tail
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

#-------------------------------------------------------------------------------

def do_code(nd, p):
    # Text before any eventual sub-element
    if nd.text is not None:
        s = nd.text
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
            
    if nd.tail:
        s = nd.tail
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

#-------------------------------------------------------------------------------

def do_head(nd, doc, refs, level):
    head = nd.text if nd.text is not None else '<empty>'
    add_heading(doc, level, head)

#-------------------------------------------------------------------------------

def do_p(nd, doc, refs):
    # One paragraph for everyting (passed onto child elements)
    p = new_paragraph(doc)

    # Text before any eventual sub-element.
    if nd.text is not None:
        s = nd.text.lstrip()
        s = coalesce(s)
        if len(s) > 0:
            add_text_run(p, s)

    # Elements under <p>: phrase, xspecref, loc, specref, emph, code
            
    # Process any eventual sub-elements.
    for k in nd:
        if k.tag == 'phrase':
            do_phrase(k, p)
        elif k.tag == 'xspecref':
            do_xspecref(k, p)
        elif k.tag == 'loc':
            do_loc(k, p)
        elif k.tag == 'specref':
            do_specref(k, p, refs)
        elif k.tag == 'emph':
            do_emph(k, p, italic=True)
        elif k.tag == 'code':
            do_code(k, p)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <p> element'
            raise RuntimeError(m)
            
    if nd.tail:
        s = nd.tail
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

def do_cell(nd, doc, refs):
    colspan = int(nd.attrib['colspan']) if 'colspan' in nd.attrib else 1
    return colspan, nd.text

#-------------------------------------------------------------------------------

def do_tr(nd, doc, refs):
    nb_cols = 0
    row = []
    for k in nd:
        if k.tag in ['th', 'td']:
            span, text = do_cell(k, doc, refs)
            colspan = 0
            if span > colspan:
                colspan = span
            row.append((colspan, text))
            if colspan > nb_cols:
                nb_cols = colspan
        else:
            m = f'Unexpected tag "{k.tag}" inside a <tbody> element'
            raise RuntimeError(m)

    return nb_cols, row

#-------------------------------------------------------------------------------

def do_tbody(nd, doc, refs):
    nb_cols_max = 0
    rows = []
    for k in nd:
        if k.tag == 'tr':
            nb_cols, row = do_tr(k, doc, refs)
            if nb_cols > nb_cols_max:
                nb_cols_max = nb_cols
            rows.append(row)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <tbody> element'
            raise RuntimeError(m)

    # We have all the data ,now create the table
    tbl = doc.add_table(len(rows), nb_cols_max)
    tbl.style = 'Table Grid'
    for i, row in enumerate(rows):
        r = tbl.rows[i]
        for j, (colspan, text) in enumerate(row):
            r.cells[j].text = text if text is not None else ''
            if colspan > 1:
                r.cells[j].merge(r.cells[j+colspan-1])
                
#-------------------------------------------------------------------------------

def do_table(nd, doc, refs):
    id_ = nd.attrib['id']
    for k in nd:
        if k.tag == 'tbody':
            do_tbody(k, doc, refs)
        else:
            m = f'Unexpected tag "{k.tag}" inside a <table> element'
            raise RuntimeError(m)

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
            title = x.text if x.text is not None else '<empty>'
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

    specrefs = get_specrefs(root, {})
    # for k, v in specrefs.items():
    #     print(f'{k}: {v}')

    # Write out the contents as Word
    doc = Document('empty.docx')

    # tbl = doc.add_table(1, 2)
    # row = tbl.rows[0]
    # c = row.cells[0]
    # c.text = 'hello'
    # c = row.cells[1]
    # c.text = 'world!'
    
    # row = tbl.add_row()
    # c = row.cells[0]
    # c.text = 'adeus'
    # c = row.cells[1]
    # c.text = 'mundo cruel'
    
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
