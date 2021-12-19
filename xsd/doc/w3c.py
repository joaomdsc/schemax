# w3c.py - convert W3C recommendations in HTML format to a Word file

import os
import re
import sys
import lxml.etree as et
from lxml import objectify

from msword import Docx, MsCellPara

#-------------------------------------------------------------------------------

def coalesce(s):
    """Coalesce multiple whitespace characters into a single space char."""
    return re.sub(r'\s+', ' ', s)

#-------------------------------------------------------------------------------

def get_tr_size(nd):
    nb_cols = 0
    for k in nd:
        if k.tag in ['th', 'td']:
            span = int(k.attrib['colspan']) if 'colspan' in k.attrib else 1
            if span > nb_cols:
                nb_cols = span
        else:
            m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                ' <tr> element'
            raise RuntimeError(m)

    return nb_cols

#-------------------------------------------------------------------------------

def get_tbody_size(nd):
    # nd is a <tbody> element
    nb_cols_max = 0
    rows = 0
    for k in nd:
        if k.tag == 'tr':
            nb_cols = get_tr_size(k)
            if nb_cols > nb_cols_max:
                nb_cols_max = nb_cols
            rows += 1
        else:
            m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                ' <tbody> element'
            raise RuntimeError(m)
    return rows, nb_cols_max

#-------------------------------------------------------------------------------

def get_table_sizes(nd):
    tables = nd.xpath('.//*[self::div1 or self::div2 or self::div3]/table/tbody')
    return [get_tbody_size(t) for t in tables]

#-------------------------------------------------------------------------------

def get_refs(nd):
    refs = {}

    # All the targets have an "id" attribute, divN and schemaComp have a child
    # <head> element whose text we want to use in the link.
    xpath_expr = './/*[self::div1 or self::div2 or self::div3 or self::div4' \
        ' or self::p or self::schemaComp or self::constraintnote' \
        ' or self::note]'

    targets = nd.xpath(xpath_expr)
    for k in targets:
        if 'id' in k.attrib:
            id_ = k.attrib['id']
            # FIXME The <head> element sometimes has sub-elements. See
            # id="no-xmlns".
            # FIXME <note> is a target as well (with no <head> child)
            s = id_ if k.tag in ['p', 'note'] else k.find('.//head').text
            refs[id_] = (k.tag, s)

    # Bibrefs
    bibrefs = {}
    targets = nd.xpath('.//blist')
    for bl in targets:
        for b in bl:
            id_ = b.attrib['id']
            key = b.attrib['key']
            s = b.text if b.text is not None else 'x'
            bibrefs[id_] = (key, coalesce(s).strip())

    # for key, text in bibrefs.values():
    #     print(f'{key}: {text}')

    # Termdefs and termrefs. Let's make a class for this kind of thing, with
    # (so far) three implementations.
    return refs, bibrefs

#-------------------------------------------------------------------------------

class XmlDocument:

    def do_termref(self, nd, p, italic=None):
        # FIXME uncomment this after implementing the term defs/refs
        # ref = nd.attrib['def']
        # k_tag, text = self.refs[ref]
        # try:
        #     p.add_internal_link(text, text)
        # except Exception as e:
        #     print(f'Line {nd.sourceline}: {e}')

        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

    def do_term(self, nd, p, italic=None):
        # This needs a specific style in the output document
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' ')).strip()
            if len(s) > 0:
                p.add_text_run(s)
    
    def do_termdef(self, nd, p, italic=None):
        """The <termdef> element is used to define special terms.

        Parents: div (?), p, phrase.
        Child: term

        """
        # Attributes
        id_ = nd.attrib['id']
        term = nd.attrib.get('term')
        role = nd.attrib.get('role')

        # FIXME need to define  bookmark here
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' ')).strip()
            if len(s) > 0:
                p.add_text_run(s)

        # Process any eventual sub-elements.
        for k in nd:
            if k.tag == 'term':
                # This needs a specific style in the output document
                self.do_term(k, p)
            elif k.tag == 'termref':
                self.do_termref(k, p, italic=italic)
            elif k.tag == 'bibref':
                self.do_bibref(k, p)
            elif k.tag == 'phrase':
                self.do_phrase(k, p)
            elif k.tag == 'local':
                p.add_text_run(k.text)
            elif k.tag == 'pt':
                p.add_text_run(f'-{k.text}-')
            elif k.tag == 'clauseref':
                pass
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <termdef> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_eg(self, nd):
        # One paragraph for everyting
        p = self.docx.new_paragraph(style='Code')

        if nd.text is not None:
            p.add_text_run(nd.text.strip(), font='Consolas', sz=9)

    #---------------------------------------------------------------------------

    def do_emph(self, nd, p, italic=None):
        # Text before any eventual sub-element.
        if nd.text is not None:
            s = nd.text
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s, italic=italic)

        # Elements under <emph>: phrase, 

        # Process any eventual sub-elements.
        for k in nd:
            if k.tag == 'phrase':
                self.do_phrase(k, p, italic=italic)
            elif k.tag == 'loc':
                self.do_loc(k, p)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside an' \
                    ' <emph> element'
                raise RuntimeError(m)

        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_xspecref(self, nd, p):
        url = nd.attrib['href']
        s = nd.text.strip()
        s = coalesce(s.replace('\n', ' '))
        p.add_hyperlink(s, url)

        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_loc(self, nd, p, bold=None, font=None, sz=None):
        url = nd.attrib['href']
        s = nd.text.strip()
        s = coalesce(s.replace('\n', ' '))
        p.add_hyperlink(s, url, font=font, sz=sz)

        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s, font=font, sz=sz)

    #---------------------------------------------------------------------------

    def do_specref(self, nd, p):
        ref = nd.attrib['ref']
        k_tag, text = self.refs[ref]
        try:
            p.add_internal_link(text, text)
        except Exception as e:
            print(f'Line {nd.sourceline}: {e}')

        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_phrase(self, nd, p, italic=None):
        # Attributes: diff == add/chg: keep it, del: ignore it
        diff = nd.attrib['diff']
        if diff not in ['chg', 'add', 'del']:
            m = f'Unexpected diff attribute value "{diff}" in a <phrase> element'
            raise RuntimeError(m)

        # Text before any eventual sub-element
        if diff != 'del':
            if nd.text is not None:
                s = nd.text
                s = coalesce(s)
                if len(s) > 0:
                    p.add_text_run(s, italic=italic)

            # Elements under <phrase>: loc, xspecref, code, 

            # Process any eventual sub-elements.
            # FIXME should pass in italic=italic as well
            for k in nd:
                if k.tag == 'loc':
                    self.do_loc(k, p)
                elif k.tag == 'xspecref':
                    self.do_xspecref(k, p)
                elif k.tag == 'code':
                    self.do_code(k, p, italic=italic)
                elif k.tag == 'termdef':
                    self.do_termdef(k, p, italic=italic)
                elif k.tag == 'termref':
                    self.do_termref(k, p, italic=italic)
                elif k.tag == 'term':
                    self.do_term(k, p)
                elif k.tag in ['propref', 'pt']:
                    pass
                else:
                    m = f'Line {k.sourceline}: unexpected tag "{k.tag}"' \
                        ' inside a <phrase> element'
                    raise RuntimeError(m)

        # Always process tail, regardless of 'diff' value
        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s, italic=italic)

    #---------------------------------------------------------------------------

    def do_code(self, nd, p, italic=None):
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' ')).strip()
            if len(s) > 0:
                p.add_text_run(s, bold=True, font='Consolas', sz=9)

        # Elements under <code>: loc

        # Process any eventual sub-elements.
        for k in nd:
            if k.tag == 'loc':
                self.do_loc(k, p, font='Consolas', sz=9)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <code> element'
                raise RuntimeError(m)

        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                # Outside the <code> element, back to normal font
                p.add_text_run(s)
                p.add_text_run(s, italic=italic)

    #---------------------------------------------------------------------------
            
    def do_head(self, nd, level):
        head = nd.text if nd.text is not None else '<empty>'
        self.docx.add_heading(level, head)

    #---------------------------------------------------------------------------
            
    def do_bibref(self, nd, p):
        ref = nd.attrib['ref']
        key, text = self.bibrefs[ref]
        try:
            p.add_internal_link(ref, f'[{key}]')
        except Exception as e:
            print(f'Line {nd.sourceline}: {e}')
        
        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_p(self, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None

        # One paragraph for everyting (passed onto child elements). This
        # doesn't create any text run yet.
        p = self.docx.new_paragraph()
        if id_ is not None:
            p.pending_bookmark = id_

        # Text before any eventual sub-element.
        if nd.text is not None:
            s = nd.text.lstrip()
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

        # Elements under <p>: phrase, xspecref, loc, specref, emph, code

        # Process any eventual sub-elements.
        for k in nd:
            if k.tag == 'phrase':
                self.do_phrase(k, p)
            elif k.tag == 'xspecref':
                self.do_xspecref(k, p)
            elif k.tag == 'loc':
                self.do_loc(k, p)
            elif k.tag == 'specref':
                self.do_specref(k, p)
            elif k.tag == 'emph':
                self.do_emph(k, p, italic=True)
            elif k.tag == 'code':
                self.do_code(k, p)
            elif k.tag == 'bibref':
                self.do_bibref(k, p)
            elif k.tag == 'termdef':
                self.do_termdef(k, p)
            elif k.tag == 'termref':
                self.do_termref(k, p)
            elif k.tag in ['propref', 'term', 'eltref', 'xpropref', 'olist',
                           'xtermref', 'quote', 'ulist', 'note', 'clauseref',
                           'glist', 'local', 'pt']:
                pass
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <p> element'
                raise RuntimeError(m)

        if nd.tail:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)
        
    #---------------------------------------------------------------------------

    def do_note(self, nd):
        role = nd.attrib['role'].capitalize() if 'role' in nd.attrib else 'Note'

        p = self.docx.new_paragraph()
        p.add_text_run(role, font='Arial', sz=10, bold=True)

        for k in nd:
            if k.tag == 'p':
                self.do_p(k)
            elif k.tag == 'eg':
                self.do_eg(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <note> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_cell_table(self, nd, p):
        pass

    #---------------------------------------------------------------------------

    def do_cell(self, nd, cells, col_idx):
        """cells: all the cells in the row, col_idx: this cell's index"""

        # Attributes
        colspan = int(nd.attrib['colspan']) if 'colspan' in nd.attrib else 1

        cell = cells[col_idx]
        if colspan > 1:
            cell.merge(cells[col_idx + colspan - 1])
        
        # One paragraph for everyting (passed onto child elements)
        p = MsCellPara(cell)

        # Text before any eventual sub-element.
        if nd.text is not None:
            s = nd.text.lstrip()
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

        # Elements under <th>/<td>: table, loc, phrase, xspecref, code, specref
        # All these elements take a paragraph as parameter

        # Process any eventual sub-elements.
        for k in nd:
            if k.tag == 'table':
                self.do_cell_table(k, p)
            elif k.tag == 'loc':
                self.do_loc(k, p)
            elif k.tag == 'phrase':
                self.do_phrase(k, p)
            elif k.tag == 'xspecref':
                self.do_xspecref(k, p)
            elif k.tag == 'code':
                self.do_code(k, p)
            elif k.tag == 'specref':
                self.do_specref(k, p)
            elif k.tag == 'eg':
                # FIXME
                pass
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' cell element (<td>, <th>)'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_tr(self, nd, row):
        col_idx = 0
        for k in nd:
            if k.tag in ['th', 'td']:
                self.do_cell(k, row.cells, col_idx)
                col_idx += 1
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <tr> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_tbody(self, nd):
        # We have all the data, now create the table
        r, c = self.tbl_sz[self.curr_table]
        tbl = self.docx.new_table(r, c)
        # print(f'({r}, {c})')
        
        row_idx = 0
        for k in nd:
            if k.tag == 'tr':
                self.do_tr(k, tbl.get_row(row_idx))
                row_idx += 1
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <tbody> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_table(self, nd):
        for k in nd:
            if k.tag == 'tbody':
                self.do_tbody(k)
            elif k.tag == 'thead':
                # FIXME xsd2_dataypes.xml has this
                pass
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <table> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_orglist(self, nd):
        # Has attribute diff="add"
        for k in nd:
            if k.tag == 'member':
                name = k.find('.//name').text.strip()
                affil = k.find('.//affiliation').text.strip()
                self.docx.add_list_item(f'{name}, {affil}')

    #---------------------------------------------------------------------------

    def do_bibl(self, nd):
        # Attributes
        id_ = nd.attrib['id']
        key = nd.attrib.get('key')  # Don't need it here

        # # Paragraph bookmark (as for <p id="XYZ"> elements)
        p = self.docx.new_paragraph()
        if id_ is not None:
            p.pending_bookmark = id_
        p.add_text_run(key, bold=True)

        p = self.docx.new_paragraph()

        for k in nd:
            if k.tag == 'emph':
                # FIXME why am I not calling do_emph() here ?
                p.add_text_run(coalesce(k.text), italic=True)
                p.add_text_run(coalesce(k.tail))
            elif k.tag == 'loc':
                self.do_loc(k, p)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <blist> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_blist(self, nd):
        for k in nd:
            if k.tag == 'bibl':
                self.do_bibl(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <blist> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_div(self, nd):
        level = int(nd.tag[3])  # 1, 2, 3 or 4

        for k in nd:
            if k.tag == 'head':
                self.do_head(k, level)
            elif k.tag == 'blist':
                self.do_blist(k)
            elif k.tag == 'p':
                self.do_p(k)
            elif k.tag == 'note':
                self.do_note(k)
            elif k.tag == 'table':
                self.do_table(k)
                self.curr_table += 1
            elif k.tag == 'orglist':
                self.do_orglist(k)
            elif k.tag in ['div1', 'div2', 'div3', 'div4']:
                self.do_div(k)
            elif k.tag in ['compdef', 'reprdef', 'proplist', 'glist',
                           # 'termdef', 'ulist', 'eg', 'constraintnote',
                           'ulist', 'eg', 'constraintnote',
                           'schemaComp', 'olist', 'graphic', 'imagemap',
                           'ednote', 'slist']:
                pass
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <div> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_status(self, nd):
        self.docx.add_title('Status of this Document')

        # Elements under <status>: note, p

        # Process any eventual sub-elements.
        for k in nd:
            if k.tag == 'note':
                self.do_note(k)
            elif k.tag == 'p':
                self.do_p(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside an' \
                    ' <status> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_abstract(self, nd):
        # FIXME this is identical to status
        self.docx.add_title('Abstract')

        # Elements under <abstract>: p, 

        # Process any eventual sub-elements.
        for k in nd:
            if k.tag == 'p':
                self.do_p(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside an' \
                    ' <abstract> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_header(self, nd):
        """<header> includes <status> and <abstract>."""
        for k in nd:
            if k.tag == 'status':
                self.do_status(k)
            elif k.tag == 'abstract':
                self.do_abstract(k)
            elif k.tag in ['title', 'version', 'w3c-designation',
                           'w3c-doctype', 'pubdate', 'publoc', 'altlocs',
                           'latestloc', 'prevlocs', 'authlist', 'errataloc',
                           'preverrataloc', 'translationloc', 'pubstmt',
                           'sourcedesc', 'langusage', 'revisiondesc']:
                m = f'Support for tag "{k.tag}" not implemented'
                print(m, file=sys.stderr)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <header> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_body(self, nd):
        """<body> holds the document content."""
        for k in nd:
            if k.tag in ['div1', 'div2', 'div3']:
                self.do_div(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <spec> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_back(self, nd):
        """<back> holds acknowledgements and appendixes."""
        for k in nd:
            if k.tag in ['div1', 'div2', 'div3']:
                self.do_div(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    '<back> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_spec(self, nd):
        """<spec> is the toplevel element in the XML tree."""
        for k in nd:
            if k.tag == 'header':
                self.do_header(k)
            elif k.tag == 'body':
                self.do_body(k)
            elif k.tag == 'back':
                self.do_back(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <spec> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------
    
    def __init__(self, filepath):
        self.filepath = filepath
        
        # Parse XML file, ignoring comments
        p = et.XMLParser(remove_comments=True)
        self.root = objectify.parse(filepath, parser=p).getroot()

        self.refs, self.bibrefs = get_refs(self.root)
        # for k, (k_tag, s) in self.refs.items():
        #     print(f'{k}: [{k_tag}] {s}')

        self.tbl_sz = get_table_sizes(self.root)
        # for k, (key, s) in self.bibrefs.items():
        #     print(f'{k}: [{key}] {s}')

        # Start a Docx instance
        self.docx = Docx()

        # Get the document contents
        self.curr_table = 0
        self.do_spec(self.root)

    def write(self):
        # Output a .docx file in the current directory
        base, _ = os.path.splitext(self.filepath)
        outpath = f'{base}.docx'
        self.docx.write(outpath)
    
#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xml filepath>')
        exit(-1)
    filepath = sys.argv[1]

    d = XmlDocument(filepath)
    d.write()
