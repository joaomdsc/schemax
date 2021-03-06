# w3c.py - convert W3C recommendations in HTML format to a Word file

"""Open issues:

Draw a box around the example

FIXME in an inline element, tail should be returned to the parent element for
styling

Links to document headings don't need a bookmark, there's a specific category
named "Numbered item". Note that currently we're only numbering 3 levels,
that's in the definition of the table of contents, in empty.docx.

Maybe, when we get info back from self.refs, we ned to know more abouot the
type of reference: to a heading or not ?

Separate sections in word document for header, body, back

Create table of contents in the code (even if it needs manual updating)

"""

import os
import re
import sys
import lxml.etree as et
from lxml import objectify

from msword import Docx, MsCellPara

dark_red = 'C00000'

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
    # <head> element whose text we want to use in the link (p and note don't).
    xpath_expr = './/*[self::div1 or self::div2 or self::div3 or self::div4' \
        ' or self::p or self::schemaComp or self::constraintnote' \
        ' or self::note or self::propdef or self::item]'

    # In the 'refs' dictionary, we store a (tag, text) couple, where tag is the
    # element tag of the target, 
    targets = nd.xpath(xpath_expr)
    for k in targets:
        if 'id' in k.attrib:
            id_ = k.attrib['id']

            link_text = \
                id_ if k.tag in ['p', 'note', 'item'] else \
                k.attrib.get('name') if k.tag == 'propdef' else \
                ''.join(k.find('.//head').itertext())
            
            refs[id_] = (k.tag, link_text)

    # Bibrefs
    bibrefs = {}
    targets = nd.xpath('.//blist')
    for k in targets:
        for b in k:
            id_ = b.attrib['id']
            key = b.attrib['key']
            bibrefs[id_] = key

    # for id_, key in bibrefs.items():
    #     print(f'{id_}: "{key}"')

    return refs, bibrefs

#-------------------------------------------------------------------------------

class XmlDocument:

    #---------------------------------------------------------------------------

    def do_constraintnote(self, nd):
        """There are four types of constraint notes ("type" attribute):

        cos: "Schema Component Constraint"
        cvc: "Validation Rule"
        sic: "Schema Information Set Contribution"
        src: "Schema Representation Constraint"

        The "id" attribute is a hyperlink reference (used with <specref>).

        """
        id_ = nd.attrib.get('id')
        type_ = nd.attrib.get('type')
        
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'head':
                pass
            elif k.tag == 'p':
                self.do_p(k)
            elif k.tag == 'proplist':
                self.do_proplist(k)
            elif k.tag == 'olist':
                self.do_olist(k)
            elif k.tag == 'note':
                self.do_note(k)
            elif k.tag == 'glist':
                self.do_glist(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <constraintnote> element'
                raise RuntimeError(m)
            

    #---------------------------------------------------------------------------

    def do_item(self, nd):
        """List item."""
        # Attributes
        id_ = nd.attrib.get('id')

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'note':
                self.do_note(k)
            elif k.tag == 'olist':
                self.do_olist(k)
            elif k.tag == 'p':
                self.do_p(k)
            elif k.tag == 'restrictCases':
                m = f'Support for tag "{k.tag}" not implemented'
                print(m, file=sys.stderr)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <item> element'
                raise RuntimeError(m)

    def do_olist(self, nd):
        """Ordered (?) list."""
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'item':
                self.do_item(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <olist> element'
                raise RuntimeError(m)

    def do_ulist(self, nd):
        """Unordered (?) list."""
        # Attributes: diff == add/chg: keep it, del: ignore it
        diff = nd.attrib.get('diff')
        if diff is not None and diff not in ['chg', 'add', 'del']:
            m = f'Unexpected diff attribute value "{diff}" in a <ulist> element'
            raise RuntimeError(m)

        # Text before any eventual sub-element
        if diff != 'del':
            # Process any eventual sub-elements
            for k in nd:
                if k.tag == 'item':
                    self.do_item(k)
                else:
                    m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                        ' <ulist> element'
                    raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_label(self, nd):
        # This needs a paragraph
        p = self.docx.new_paragraph()
        
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' ')).lstrip()
            if len(s) > 0:
                p.add_text_run(s, bold=True, font='Consolas', sz=9)

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'eltref':
                self.do_eltref(k, p)
            # elif k.tag == 'emph':
            #     self.do_simple_simple('emph', k, p)
            elif k.tag == 'emph':
                self.do_emph(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'propref':
                self.do_propref(k, p)
            elif k.tag == 'xpropref':
                self.do_xpropref(k, p)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <label> element'
                raise RuntimeError(m)

        # No tail

    def do_def(self, nd):
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'olist':
                self.do_olist(k)
            elif k.tag == 'p':
                self.do_p(k)
            elif k.tag == 'proplist':
                self.do_proplist(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <def> element'
                raise RuntimeError(m)

        # No tail

    def do_gitem(self, nd):
        """Glossary (?) list."""
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'label':
                self.do_label(k)
            elif k.tag == 'def':
                self.do_def(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <gitem> element'
                raise RuntimeError(m)

    def do_glist(self, nd):
        """Glossary (?) list."""
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'gitem':
                self.do_gitem(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <glist> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_propmap(self, nd):
        """Property - Representation mapping."""
        # Attributes
        name = nd.attrib.get('name')
        
        tag, link_text = self.refs[name]

        p = self.docx.new_paragraph()
        p.add_text_run(f'{{{link_text}}}\t')
        
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' '))
            if len(s) > 0:
                p.add_text_run(s)
        
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'phrase':
                self.do_phrase(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'termref':
                self.do_termref(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'specref':
                self.do_specref(k, p)
            elif k.tag == 'eltref':
                self.do_eltref(k, p)
            elif k.tag == 'propref':
                self.do_propref(k, p)
            elif k.tag in ['xspecref', 'xtermref']:
                self.do_xspecref(k, p)  # not a typo
            elif k.tag == 'xpropref':
                self.do_xpropref(k, p)
            elif k.tag == 'glist':
                self.do_glist(k)
            elif k.tag == 'olist':
                self.do_olist(k)
            elif k.tag == 'code':
                self.do_code(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag in ['local', 'pt']:
                self.do_simple_simple(k.tag, k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <propmap> element'
                raise RuntimeError(m)

    def do_reprcomp(self, nd):
        """List of properties for a schema component."""
        # Attributes
        ref = nd.attrib.get('ref')  # this references a <div>, like <specref>
        abstract = nd.attrib.get('abstract')

        # Output the 'abstract' as a link to the definition section
        p = self.docx.new_paragraph()
        p.add_internal_link(ref, abstract)
        p.add_text_run(' Schema Component', bold=True)
        
        # Titles above the mapping section 
        p = self.docx.new_paragraph()
        p.add_text_run('Property\tRepresentation', bold=True)

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'propmap':
                self.do_propmap(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <reprcomp> element'
                raise RuntimeError(m)
    
    def do_eltref(self, nd, p, style=None):
        # Attributes
        ref = nd.attrib.get('ref')
        
        # Args below are: bookmark_name, link_text
        p.add_internal_link(ref, f'<{ref}>')

        if nd.tail is not None:
            s = coalesce(nd.tail)
            if len(s) > 0:
                p.add_text_run(s, style='W3cEmphasis')

    def do_reprelt(self, nd):
        """XML Representation: element."""
        # Attributes
        eltname = nd.attrib.get('eltname')
        type_ = nd.attrib.get('type_')

        # Title
        p = self.docx.new_paragraph()
        p.add_text_run('XML Representation Summary', bold=True, color=dark_red)
        p.add_text_run(': ', bold=True)
        p.add_text_run(eltname)
        p.add_text_run(' Element Information Item', bold=True)
        
        # Get the XML representation for this, from eltname and type
        p = self.docx.new_paragraph()
        p.pending_bookmark = eltname
        p.add_text_run(' ')

    def do_reprdef(self, nd):
        """XML Representation.

        """
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'reprelt':
                self.do_reprelt(k)
            elif k.tag == 'reprcomp':
                self.do_reprcomp(k)
            elif k.tag == 'p':
                self.do_p(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <reprdef> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------
    
    def do_propref(self, nd, p):
        # Attributes
        ref = nd.attrib.get('ref')
        tag, link_text = self.refs[ref]
        
        # Args below are: bookmark_name, link_text
        p.add_internal_link(ref, f'{{{link_text}}}')

        if nd.tail is not None:
            s = coalesce(nd.tail)
            if len(s) > 0:
                p.add_text_run(s)

    def do_propdef(self, nd):
        """Property definition"""
        # Attributes
        id_ = nd.attrib.get('id')
        name = nd.attrib.get('name')

        # This needs a paragraph
        p = self.docx.new_paragraph()
        if id_ is not None:
            p.pending_bookmark = id_
        p.add_text_run(f'{{{name}}} ')

        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' ')).lstrip()
            if len(s) > 0:
                p.add_text_run(s)
        
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'termref':
                self.do_termref(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'specref':
                self.do_specref(k, p)
            elif k.tag == 'bibref':
                self.do_bibref(k, p)
            elif k.tag == 'propref':
                self.do_propref(k, p)
            elif k.tag in ['xtermref']:
                self.do_xspecref(k, p)  # not a typo
            elif k.tag == 'code':
                self.do_code(k, p)
            elif k.tag == 'xpropref':
                self.do_xpropref(k, p)
            elif k.tag == 'eltref':
                self.do_eltref(k, p)
            elif k.tag == 'phrase':
                self.do_phrase(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag in ['pt', 'local']:
                self.do_simple_simple('pt', k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'glist':
                self.do_glist(k)
            elif k.tag == 'olist':
                self.do_olist(k)
            elif k.tag == 'clauseref':
                self.do_clauseref(k, p)
            elif k.tag == 'proplist':
                self.do_proplist(k)
            elif k.tag in ['iiName']:
                m = f'Support for tag "{k.tag}" not implemented'
                print(m, file=sys.stderr)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <propdef> element'
                raise RuntimeError(m)

    def do_proplist(self, nd):
        """List of properties for a schema component."""
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'propdef':
                self.do_propdef(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <proplist> element'
                raise RuntimeError(m)

    def do_compdef(self, nd):
        """Component definition.

        The definition of each kind of schema component consists of a list of
        its properties and their contents, followed by descriptions of the
        semantics of the properties

        A compdef is a block element. It includes a <proplist> child element.

        """
        # Attributes
        name = nd.attrib.get('name')
        ref = nd.attrib.get('ref')

        # ref matches some <div id> and makes the compdef act as a specref
        p = self.docx.new_paragraph()
        p.add_text_run('Schema Component', bold=True, color=dark_red)
        p.add_text_run(': ', bold=True)
        p.add_internal_link(ref, name)

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'proplist':
                self.do_proplist(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <compdef> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------
    
    def do_termref(self, nd, p, style=None):
        # Attributes
        ref = nd.attrib['def']

        # Text before any eventual sub-element.
        if nd.text is not None:
            text = coalesce(nd.text.lstrip())
            p.add_internal_link(ref, text)
    
    def do_termdef(self, nd, p):
        """The <termdef> element is used to define special terms.

        Parents: div (?), p, phrase.
        Child: term

        This function processes a <termdef> element as it appears in the norml
        text flow.

        """
        # FIXME termdefs require a specific style in the output document. On
        # the web site they appear in red.

        # Attributes
        id_ = nd.attrib['id']
        term = nd.attrib.get('term')
        role = nd.attrib.get('role')

        # We want a bookmark here. FIXME: this can only support one pending
        # bookmark at a time.
        p.pending_bookmark = id_

        # This is specific to termdefs
        p.add_text_run('[Definition:] ', style='W3cDefinition')

        # Text before any eventual sub-element
        if nd.text is not None:
            # FIXME: there isn't always text before the 1st subelement
            s = nd.text
            s = coalesce(s.replace('\n', ' ')).lstrip()
            if len(s) > 0:
                # I would've wanted to use the 'term' as the bookmark text
                p.add_text_run(s, style='W3cDefinition')

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'termref':
                self.do_termref(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s, style='W3cDefinition')
            elif k.tag == 'bibref':
                self.do_bibref(k, p, style='W3cDefinition')
            elif k.tag == 'phrase':
                self.do_phrase(k, p, style='W3cDefinition')
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s, style='W3cDefinition')
            elif k.tag == 'specref':
                self.do_specref(k, p, style='W3cDefinition')
            elif k.tag == 'eltref':
                self.do_eltref(k, p, style='W3cDefinition')
            elif k.tag in ['xspecref', 'xtermref']:
                self.do_xspecref(k, p)  # not a typo
            elif k.tag == 'xpropref':
                self.do_xpropref(k, p)
            elif k.tag == 'propref':
                self.do_propref(k, p)
            elif k.tag == 'clauseref':
                self.do_clauseref(k, p)
            elif k.tag in ['term', 'local', 'pt', 'quote']:
                self.do_simple_simple(k.tag, k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s, style='W3cDefinition')
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <termdef> element'
                raise RuntimeError(m)

        # FIXME termdef's tail should be handled by its parent
        if nd.tail is not None:
            s = coalesce(nd.tail)
            if len(s) > 0:
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_eg(self, nd):
        # One paragraph for everyting
        p = self.docx.new_paragraph(style='Code')

        if nd.text is not None:
            p.add_text_run(nd.text.strip(), font='Consolas', sz=9)

    #---------------------------------------------------------------------------

    def do_xspecref(self, nd, p):
        url = nd.attrib['href']
        s = nd.text.strip()
        s = coalesce(s.replace('\n', ' '))
        p.add_hyperlink(s, url)

        if nd.tail is not None:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

    def do_xpropref(self, nd, p):
        # FIXME should enclose in square brackets , and not print tail
        # Either href or role
        if 'href' in nd.attrib:
            self.do_xspecref(nd, p)
            
        role = nd.attrib.get('role')
        
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' '))
            if len(s) > 0:
                p.add_text_run(s)

        if nd.tail is not None:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_loc(self, nd, p, bold=None, style=None):
        url = nd.attrib['href']
        s = nd.text.strip()
        s = coalesce(s.replace('\n', ' '))
        p.add_hyperlink(s, url)
        
        if len(nd) > 0:
            k = nd[0]
            m = f'Line {k.sourceline}: unexpected tag "{k.tag}"' \
                ' inside a <loc> element'
            raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_specref(self, nd, p, style=None):
        """The <specref> element links to a location inside the same document.
        
        The "ref" attribute holds a string value that is used to match with the
        link target. There are three aspects to processing these links:

        1) a first pass collects all targets in the self.refs dictionary, for
        those cases where the link text requres information from the target
        itself.

        2) when a target is processed in the normal course of a run, to be
        output, an MS Word bookmark needs to be created at that point in the
        document, to implement a live link inside the Word document (details
        will vary according to the tag).

        3) when a <specref> element is found, a hyperlink needs to be inserted
        in the word document (below).

        """
        # The text for the <specref>, at this point in the document, does not
        # include a link text. For that, there are several strategies:
        #
        #   - in some cases (like <div>), we'll want to use something that
        #     comes from the target (such as the heading text)
        #
        #   - in other cases (like <p>), we'll just use whatever we have at
        #   - hand, namely the ref itsef.
        #
        # In the first case, we need to parse the target first, and store
        # whatever it is we want to use as link text iwth ref, for latter use.

        # We don't need the first pass to be able to create a hyperlink from
        # the <specref> to the target. The 'ref' is the bookmark name, hence
        # sufficient for MS Word to find the target. We only need it if we want
        # some part of the target to make it into the link text.

        ref = nd.attrib['ref']
        tag, link_text = self.refs[ref]
        
        # Args below are: bookmark_name, link_text
        p.add_internal_link(ref, link_text)

        if nd.tail is not None:
            s = coalesce(nd.tail)
            if len(s) > 0:
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_clauseref(self, nd, p, style=None):
        ref = nd.attrib['ref']
        tag, link_text = self.refs[ref]
        
        # Args below are: bookmark_name, link_text
        p.add_internal_link(ref, link_text)

        if nd.tail is not None:
            s = coalesce(nd.tail)
            if len(s) > 0:
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_phrase(self, nd, p, style=None):
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
                    p.add_text_run(s, style=style)

            # Elements under <phrase>: loc, xspecref, code, 

            # Process any eventual sub-elements
            for k in nd:
                if k.tag == 'loc':
                    self.do_loc(k, p)
                    if k.tail is not None:
                        s = coalesce(k.tail)
                        if len(s) > 0:
                            p.add_text_run(s, style=style)
                elif k.tag in ['xspecref', 'xtermref']:
                    self.do_xspecref(k, p)  # not a typo
                elif k.tag == 'xpropref':
                    self.do_xpropref(k, p)
                elif k.tag == 'termdef':
                    self.do_termdef(k, p)
                elif k.tag == 'termref':
                    self.do_termref(k, p, style=style)
                    if k.tail is not None:
                        s = coalesce(k.tail)
                        if len(s) > 0:
                            p.add_text_run(s, style=style)
                elif k.tag == 'eltref':
                    self.do_eltref(k, p, style=style)
                elif k.tag == 'propref':
                    self.do_propref(k, p)
                elif k.tag == 'specref':
                    self.do_specref(k, p)
                elif k.tag == 'clauseref':
                    self.do_clauseref(k, p)
                elif k.tag == 'code':
                    self.do_code(k, p)
                    if k.tail is not None:
                        s = coalesce(k.tail)
                        if len(s) > 0:
                            p.add_text_run(s, style=style)
                elif k.tag in ['term', 'pt', 'local']:
                    self.do_simple_simple(k.tag, k, p)
                    if k.tail is not None:
                        s = coalesce(k.tail)
                        if len(s) > 0:
                            p.add_text_run(s, style=style)
                else:
                    m = f'Line {k.sourceline}: unexpected tag "{k.tag}"' \
                        ' inside a <phrase> element'
                    raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_simple_simple(self, tag, nd, p):
        """Inline elements, simple type, simple content.

        Inline tags are code, local, pt, term, quote, and maybe others. emph
        should also be inline, but currently it can have a <phrase>
        sub-element. Either the <phrase> elements should be removed in a
        pre-processing phase, or <emph> has to be treated as complex or mixed
        content.

        We assume that these tags have a text node, with no leading or trailing
        whitespace. If there is any text in the 'tail', it must be handled in
        the parent node, here it's just ignored.

        """

        # Map tags to styles
        style = \
            'W3cCode' if tag == 'code' else \
            'W3cTermDef' if tag == 'term' else \
            'W3cNormalBoldChar' if tag == 'local' else \
            'W3cEmphasis' if tag == 'emph' else \
            'W3cNormalChar'

        # FIXME term requires a specific style, derived fomr 'termdef' style

        # FIXME pt sometimes is italic 
            
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' '))
            
            if len(s) > 0:
                if tag == 'quote':
                    s = f'"{s}"'
                p.add_text_run(s, style=style)

        # Process any eventual sub-elements
        if len(nd) > 0:
            if nd[0].tag == 'phrase':
                print(f'Line {nd[0].sourceline}: {tag} / phrase')
            else:
                m = f'Line {nd.sourceline}: unexpected tag "{nd[0].tag}"' \
                    f' inside a <{tag}> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_emph(self, nd, p):
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' '))
            if len(s) > 0:
                p.add_text_run(s, style='W3cEmphasis')

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'loc':
                self.do_loc(k, p, style='W3cEmphasis')
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s, style='W3cEmphasis')
            elif k.tag == 'phrase':
                self.do_phrase(k, p, style='W3cEmphasis')
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s, style='W3cEmphasis')
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <emph> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_code(self, nd, p):
        # Text before any eventual sub-element
        if nd.text is not None:
            s = nd.text
            s = coalesce(s.replace('\n', ' '))
            if len(s) > 0:
                p.add_text_run(s, style='W3cCode')

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'loc':
                self.do_loc(k, p, style='W3cCode')
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s, style='W3cCode')
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <code> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------
            
    def do_div_head(self, nd, level, id_=None):
        """A <head> element holds the title text for a divN section.

        Insert the element's text as the section heading in MS Word.

        The add_heading() function will also create an MS Word bookmark
        attached to the heading, using the text as a bookmark name.

        """
        text = nd.text if nd.text is not None else '<empty>'
        self.docx.add_heading(level, text, bookmark_name=id_)

    #---------------------------------------------------------------------------
            
    def do_bibref(self, nd, p, flag=False, style=None):
        ref = nd.attrib['ref']
        key = self.bibrefs[ref]

        p.add_internal_link(ref, f'[{key}]')

        # if flag:
        #     print(f'bibref: nbr kids={len(nd)}')
        
        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'phrase':
                self.do_phrase(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'xpropref':
                print(f'bibref/xpropref: text={k.text}')
                print(f'bibref/xpropref: tail={k.tail if k.tail is not None else ""}')
                # self.do_xspecref(k, p)  # not a typo
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <bibref> element'
                raise RuntimeError(m)

        if nd.tail is not None:
            s = nd.tail
            s = coalesce(s)
            if len(s) > 0:
                # if flag:
                #     print(f'p:bibref: {s}')
                p.add_text_run(s)

    #---------------------------------------------------------------------------

    def do_p(self, nd, flag=False):
        # Attributes
        id_ = nd.attrib.get('id')

        # if flag:
        #     print(f'p: nbr kids={len(nd)}', end='')
        #     if len(nd) > 0:
        #         print(f': tag[0]={nd[0].tag}', end='')
        #         if len(nd) > 1:
        #             print(f', tag[1]={nd[1].tag}', end='')
        #     print()

        # One paragraph for everyting (passed onto child elements). This
        # doesn't create any text run yet.

        # FIXME ulist creates its own paragraphs
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

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'phrase':
                self.do_phrase(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        # print(f'Line {k.sourceline}: p.phrase.tail="{s}"')
                        p.add_text_run(s)
            elif k.tag in ['xspecref', 'xtermref']:
                self.do_xspecref(k, p)  # not a typo
            elif k.tag == 'xpropref':
                # print(f'p/xpropref: text={k.text}')
                # print(f'p/xpropref: tail={k.tail if k.tail is not None else ""}')
                self.do_xpropref(k, p)
            elif k.tag == 'loc':
                self.do_loc(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'specref':
                self.do_specref(k, p)
            elif k.tag == 'bibref':
                self.do_bibref(k, p, flag=flag)
            elif k.tag == 'termdef':
                self.do_termdef(k, p)
            elif k.tag == 'termref':
                self.do_termref(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'propref':
                self.do_propref(k, p)
            elif k.tag == 'eltref':
                self.do_eltref(k, p)
            elif k.tag == 'glist':
                self.do_glist(k)
            elif k.tag == 'olist':
                self.do_olist(k)
            elif k.tag == 'ulist':
                # ulist is a block, it includes/creates its own paragraphs, and
                # they will not go into the same paragrpah as the tail.
                self.do_ulist(k)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'note':
                self.do_note(k)
            elif k.tag == 'emph':
                self.do_emph(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'code':
                self.do_code(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag in ['term', 'local', 'pt', 'quote']:
                self.do_simple_simple(k.tag, k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'clauseref':
                self.do_clauseref(k, p)
            elif k.tag in ['scrap', 'nt', 'iiName']:
                m = f'Support for tag "{k.tag}" not implemented'
                print(m, file=sys.stderr)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <p> element'
                raise RuntimeError(m)

        if nd.tail is not None:
            s = coalesce(nd.tail)
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

        # Process any eventual sub-elements
        for k in nd:
            if k.tag == 'table':
                self.do_cell_table(k, p)
            elif k.tag == 'loc':
                self.do_loc(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'phrase':
                self.do_phrase(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
            elif k.tag == 'xspecref':
                self.do_xspecref(k, p)
            elif k.tag == 'code':
                self.do_code(k, p)
                if k.tail is not None:
                    s = coalesce(k.tail)
                    if len(s) > 0:
                        p.add_text_run(s)
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
                # self.do_simple_simple('emph', k, p)
                self.do_emph(k, p)
            elif k.tag == 'loc':
                self.do_loc(k, p)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <blist> element'
                raise RuntimeError(m)

            # Process sub-element's tail
            if k.tail is not None:
                s = coalesce(k.tail)
                if len(s) > 0:
                    p.add_text_run(s)

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
        id_ = nd.attrib.get('id')
        level = int(nd.tag[3])  # 1, 2, 3 or 4

        repr_ = flag = False
        for k in nd:
            if k.tag == 'head':
                self.do_div_head(k, level, id_=id_)
            elif k.tag == 'blist':
                self.do_blist(k)
            elif k.tag == 'p':
                if repr_:
                    p_cnt += 1
                    if p_cnt == 2:
                        flag = True
                self.do_p(k, flag=flag)
                if flag:
                    repr_ = flag = False
            elif k.tag == 'note':
                self.do_note(k)
            elif k.tag == 'table':
                self.do_table(k)
                self.curr_table += 1
            elif k.tag == 'orglist':
                self.do_orglist(k)
            elif k.tag in ['div1', 'div2', 'div3', 'div4']:
                self.do_div(k)
            elif k.tag == 'compdef':
                self.do_compdef(k)
            elif k.tag == 'reprdef':
                self.do_reprdef(k)
                repr_ = True
                p_cnt = 0
            elif k.tag == 'proplist':
                self.do_proplist(k)
            elif k.tag == 'glist':
                self.do_glist(k)
            elif k.tag == 'olist':
                self.do_olist(k)
            elif k.tag == 'ulist':
                self.do_ulist(k)
            elif k.tag == 'constraintnote':
                self.do_constraintnote(k)
                # If <ulist> has a tail inside a <div>, we ignore it (<div> has
                # a complex content model, not mixed)
            elif k.tag in ['eg', 'schemaComp', 'graphic', 'imagemap', 'ednote',
                           'slist']:
                pass
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <div> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_status(self, nd):
        self.docx.add_title('Status of this Document')

        # Elements under <status>: note, p

        # Process any eventual sub-elements
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

        # Process any eventual sub-elements
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
            if k.tag in ['div1', 'div2', 'div3', 'div4']:
                self.do_div(k)
            else:
                m = f'Line {k.sourceline}: unexpected tag "{k.tag}" inside a' \
                    ' <spec> element'
                raise RuntimeError(m)

    #---------------------------------------------------------------------------

    def do_back(self, nd):
        """<back> holds acknowledgements and appendixes."""
        for k in nd:
            if k.tag in ['div1', 'div2', 'div3', 'div4']:
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

    def do_elem_tag(self, nd):
        """self.tag_cnt is a dict with tag keys, values are dicts of sub-tags"""

        if nd.tag in self.tag_cnt:
            self.tag_cnt[nd.tag]['_count'] += 1
        else:
            self.tag_cnt[nd.tag] = { '_count': 1 }
        d = self.tag_cnt[nd.tag]
        
        for k in nd:
            if nd.tag == 'head':
                if k.tag == 'code':
                    print(f'head/code: line={k.sourceline}')
                elif k.tag == 'phrase':
                    print(f'head/phrase: line={k.sourceline}')
                elif k.tag == 'pt':
                    print(f'head/pt: line={k.sourceline}')
            if k.tag in d:
                d[k.tag] += 1
            else:
                d[k.tag] = 1
            self.do_elem_tag(k)

    def count_tags(self):
        self.tag_cnt = {}
        self.do_elem_tag(self.root)
        for tag, d in sorted(self.tag_cnt.items()):
            print(f'{tag}:')
            for k, v in sorted(d.items()):
                print(f'    {k}: {v}')
        print()

        print(f'Total tag nbr = {len(self.tag_cnt)}')
        for k in sorted(self.tag_cnt.keys()):
            print(f'    {k}')
       
    #---------------------------------------------------------------------------
    
    def __init__(self, filepath):
        self.filepath = filepath
        
        # Parse XML file, ignoring comments
        p = et.XMLParser(remove_comments=True)
        self.root = objectify.parse(filepath, parser=p).getroot()

        # # Counting tags
        # self.count_tags()

        self.refs, self.bibrefs = get_refs(self.root)
        # for k, (k_tag, s) in self.refs.items():
        #     print(f'{k}: [{k_tag}] {s}')
        # print('-'*80)

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
