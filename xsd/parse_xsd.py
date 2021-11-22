# parse_xsd.py - parse an XML Schema file (assumed to be valid)

import sys
import json
import lxml.etree as et
from lxml import objectify

lbl_sz = 12

#-------------------------------------------------------------------------------

def tag(nd):
    return et.QName(nd).localname

#-------------------------------------------------------------------------------

class XsdAppinfo:
    """Specifies information to be used by applications within an annotation
    element.

    Content: ({any})*

    """
    def __init__(self, source=None, content=None):
        self.source = source
        self.content = content

    @classmethod
    def build(cls, nd):
        # Attributes
        source = nd.attrib['source'] if 'source' in nd.attrib else None
        
        # Sub-elements
        content = nd.text.strip()

        return cls(source, content)

#-------------------------------------------------------------------------------

class XsdDocumentation:
    """Specifies information to be used by applications within an annotation
    element.

    Content: ({any})*

    """
    def __init__(self, source=None, lang=None, content=None):
        self.source = source
        self.lang = lang
        self.content = content

    @classmethod
    def build(cls, nd):
        # Attributes
        source = nd.attrib['source'] if 'source' in nd.attrib else None
        lang = nd.attrib['lang'] if 'lang' in nd.attrib else None
        
        # Sub-elements
        content = nd.text.strip()

        return cls(source, lang, content)

#-------------------------------------------------------------------------------

class XsdAnnotation:
    """Defines an annotation.

    Content: (appinfo | documentation)*
    """
    def __init__(self, id_=None, appinfos=None, docs=None):
        self.id_ = id_

        self.appinfos = []
        if appinfos is not None:
            self.appinfos = appinfos

        self.docs = []
        if docs is not None:
            self.docs = docs

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        
        # Sub-elements
        appinfos = []
        docs = []
        for k in nd:
            if tag(k) == 'appinfo':
                appinfos.append(XsdAppinfo.build(k))
            elif tag(k) == 'documentation':
                docs.append(XsdDocumentation.build(k))

        return cls(id_, appinfos, docs)

#-------------------------------------------------------------------------------

class XsdList:
    """Defines a collection of a single simpleType definition.

    Content: (annotation?, (simpleType?))

    """
    def __init__(self, id_=None, itemType=None, annotation=None, simple=None):
        self.id_ = id_
        self.itemType = itemType
        self.annotation = annotation
        self.simple = simple

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        itemType = nd.attrib['itemType'] if 'itemType' in nd.attrib else None

        # Elements
        annotation = None
        simple = None
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'simpleType':
                simple = XsdSimpleType.build(k)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:list'
                raise RuntimeError(m)

        return cls(id_=id_, itemType=itemType, annotation=annotation, simple=simple)

#-------------------------------------------------------------------------------

class XsdRestrictionST:
    """Defines constraints on a simpleType definition.

    Content: (annotation?, (simpleType?, (minExclusive | minInclusive |
    maxExclusive | maxInclusive | totalDigits |fractionDigits | length |
    minLength | maxLength | enumeration | whiteSpace | pattern)*))

    """
    def __init__(self, id_=None, base=None, annotation=None):
        self.id_ = id_
        self.base = base
        self.annotation = annotation

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        annotation = None
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) in ['fractionDigits', 'enumeration', 'length',
                            'maxExclusive', 'maxInclusive', 'maxLength',
                            'minExclusive', 'minInclusive', 'minLength',
                            'pattern', 'simpleType', 'totalDigits',
                            'whiteSpace']:
                m = f'Support for tag "{tag(k)}" not implemented'
                print(m, file=sys.stderr)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:restriction' \
                    ' (simpleType)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, annotation=annotation)

#-------------------------------------------------------------------------------

class XsdUnion:
    """Defines a collection of multiple simpleType definitions.

    Content: (annotation?, (simpleType*))

    """
    def __init__(self, id_=None, memberTypes=None, annotation=None, simple=None):
        self.id_ = id_
        self.memberTypes = memberTypes
        self.annotation = annotation
        self.simple = simple

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        memberTypes = nd.attrib['memberTypes'] if 'memberTypes' in nd.attrib \
            else None

        # Elements
        annotation = None
        simple = None
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'simpleType':
                simple = XsdSimpleType.build(k)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:union'
                raise RuntimeError(m)

        return cls(id_=id_, memberTypes=memberTypes, annotation=annotation, simple=simple)

#-------------------------------------------------------------------------------

class XsdSimpleType:
    """Defines a simple type, which determines the constraints on and information
    about the values of attributes or elements with text-only content.

    Content: (annotation?, (restriction | list | union))

    """
    def __init__(self, id_=None, name=None, final=None, annotation=None, elems=None):
        self.id_ = id_
        self.name = name
        self.final = final
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        final = nd.attrib['final'] if 'final' in nd.attrib else None

        label = 'SimpleType'
        print(f'{label}{" "*(lbl_sz-len(label))}: name={name}')

        # Elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'list':
                elems.append(XsdList.build(k))
            elif tag(k) == 'restriction':
                elems.append(XsdRestrictionST.build(k))
            elif tag(k) == 'union':
                elems.append(XsdUnion.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:simpleType'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, final=final, annotation=annotation,
                   elems=elems)

#-------------------------------------------------------------------------------

class XsdRestrictionSC:
    """Defines constraints on a simpleContent definition.

    Content: (annotation?, (simpleType?, (minExclusive | minInclusive | 
    maxExclusive | maxInclusive | totalDigits |fractionDigits | length | 
    minLength | maxLength | enumeration | whiteSpace | pattern)*)?, 
    ((attribute | attributeGroup)*, anyAttribute?))

    """
    def __init__(self, id_=None, base=None, annotation=None):
        self.id_ = id_
        self.base = base
        self.annotation = annotation

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        annotation = None
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) in ['fractionDigits', 'enumeration', 'length',
                            'maxExclusive', 'maxInclusive', 'maxLength',
                            'minExclusive', 'minInclusive', 'minLength',
                            'pattern', 'simpleType', 'totalDigits',
                            'whiteSpace']:
                m = f'Support for tag "{tag(k)}" not implemented'
                print(m, file=sys.stderr)
            # FIXME attribute, attributeGroup, anyAttribute
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:restriction' \
                    ' (simpleContent)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, annotation=annotation)

#-------------------------------------------------------------------------------

class XsdExtensionSC:
    """Contains extensions on simpleContent. This extends a simple type or a
    complex type that has simple content by adding specified attribute(s),
    attribute group(s), or anyAttribute.

    Content: (annotation?, ((attribute | attributeGroup)*, anyAttribute?))

    """
    def __init__(self, id_=None, base=None, annotation=None, elems=None):
        self.id_ = id_
        self.base = base
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'attribute':
                elems.append(XsdAttribute.build(k))
            # FIXME attributeGroup, anyAttribute
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:extension' \
                    ' (simpleContent)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, annotation=annotation, elems=elems)

#-------------------------------------------------------------------------------

class XsdSimpleContent:
    """Contains extensions or restrictions on a complexType element with character
    data or a simpleType element as content and contains no elements.

    Content: (annotation?, (restriction | extension))

    """
    def __init__(self, id_=None, annotation=None, rest=None, ext=None):
        self.id_ = id_
        self.annotation = annotation
        self.rest = rest
        self.ext = ext

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None

        # Elements
        annotation = None
        rest = None
        ext = None
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'restriction':
                rest = XsdRestrictionSC.build(k)
            elif tag(k) == 'extension':
                ext = XsdExtensionSC.build(k)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:simpleContent'
                raise RuntimeError(m)

        return cls(id_=id_, annotation=annotation, rest=rest, ext=ext)

#-------------------------------------------------------------------------------

class XsdRestrictionCC:
    """Defines constraints on a complexContent definition.

    Content: (annotation?, (group | all | choice | sequence)?, ((attribute | 
    attributeGroup)*, anyAttribute?))

    """
    def __init__(self, id_=None, base=None, annotation=None):
        self.id_ = id_
        self.base = base
        self.annotation = annotation

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        annotation = None
        grp = None
        all_ = None
        chc = None
        seqs = None
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'group':
                grp = XsdGroup.build(k)
            elif tag(k) == 'all':
                all_ = XsdAll.build(k)
            elif tag(k) == 'choice':
                chc = XsdChoice.build(k)
            elif tag(k) == 'sequence':
                seqs.append(XsdSequence.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:restriction' \
                    ' (complexContent)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, annotation=annotation)

#-------------------------------------------------------------------------------

class XsdExtensionCC:
    """Contains extensions on complexContent.

    Content: (annotation?, ((group | all | choice | sequence)?, ((attribute |
 attributeGroup)*, anyAttribute?)))

    """
    def __init__(self, id_=None, base=None, annotation=None):
        self.id_ = id_
        self.base = base
        self.annotation = annotation

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'group':
                elems.append(XsdGroup.build(k))
            elif tag(k) == 'all':
                elems.append(XsdAll.build(k))
            elif tag(k) == 'choice':
                elems.append(XsdChoice.build(k))
            elif tag(k) == 'sequence':
                elems.append(XsdSequence.build(k))
            elif tag(k) == 'attribute':
                elems.append(XsdAttribute.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:extension' \
                    ' (complexContent)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, annotation=annotation)

#-------------------------------------------------------------------------------

class XsdComplexContent:
    """Contains extensions or restrictions on a complex type that contains mixed
    content or elements only.

    Content: (annotation?,  (restriction | extension))

    """
    def __init__(self, id_=None, mixed=None, annotation=None, rest=None,
                 ext=None):
        self.id_ = id_
        self.mixed = mixed
        self.annotation = annotation
        self.rest = rest
        self.ext = ext

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        mixed = nd.attrib['mixed'] if 'mixed' in nd.attrib else None

        # Elements
        annotation = None
        rest = None
        ext = None
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'restriction':
                rest = XsdRestrictionCC.build(k)
            elif tag(k) == 'extension':
                ext = XsdExtensionCC.build(k)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:complexContent'
                raise RuntimeError(m)

        return cls(id_=id_, mixed=mixed, annotation=annotation, rest=rest,
                   ext=ext)

#-------------------------------------------------------------------------------

class XsdSequence:
    """Requires the elements in the group to appear in the specified sequence
    within the containing element.

    Content: (annotation?, (element | group | choice | sequence | any)*)

    """
    def __init__(self, id_=None, minOccurs=None, maxOccurs=None,
                 annotation=None, elems=None):
        self.id_ = id_
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    # See <xs:complexType name="fx_surface_common"> in collada

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None

        # Elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'group':
                elems.append(XsdGroup.build(k))
            elif tag(k) == 'choice':
                elems.append(XsdChoice.build(k))
            elif tag(k) == 'any':
                elems.append(XsdAny.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:sequence'
                raise RuntimeError(m)

        return cls(id_=id_, minOccurs=minOccurs, maxOccurs=maxOccurs,
                   annotation=annotation, elems=elems)

#-------------------------------------------------------------------------------

class XsdAttribute:
    """Declares an attribute.

    Content: (annotation?, (simpleType?))

    """
    def __init__(self, id_=None, name=None, ref=None, type_=None, default=None,
                 fixed=None, form=None, use=None, annotation=None, elems=None):
        self.id_ = id_
        self.name = name
        self.ref = ref
        self.type_ = type_
        self.default = default
        self.fixed = fixed
        self.form = form
        self.use = use
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        ref = nd.attrib['ref'] if 'ref' in nd.attrib else None
        type_ = nd.attrib['type_'] if 'type_' in nd.attrib else None
        default = nd.attrib['default'] if 'default' in nd.attrib else None
        fixed = nd.attrib['fixed'] if 'fixed' in nd.attrib else None
        form = nd.attrib['form'] if 'form' in nd.attrib else None
        use = nd.attrib['use'] if 'use' in nd.attrib else None

        # Elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'simpleType':
                elems.append(XsdSimpleType.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:attribute'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, ref=ref, type_=type_, annotation=annotation,
                   elems=elems)

#-------------------------------------------------------------------------------

class XsdComplexType:
    """Defines a complex type, which determines the set of attributes and the
    content of an element.

    Content: (annotation?, (simpleContent | complexContent | ((group | all |
    choice | sequence)?, ((attribute | attributeGroup)*, anyAttribute?))))

    """
    def __init__(self, id_=None, name=None, abstract=None, block=None,
                 final=None, mixed=None, annotation=None, elems=None):
        self.id_ = id_
        self.name = name
        self.abstract = abstract
        self.block = block
        self.final = final
        self.mixed = mixed
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        abstract = nd.attrib['abstract'] if 'abstract' in nd.attrib else None
        block = nd.attrib['block'] if 'block' in nd.attrib else None
        final = nd.attrib['final'] if 'final' in nd.attrib else None
        mixed = nd.attrib['mixed'] if 'mixed' in nd.attrib else None

        label = 'ComplexType'
        s = f'{label}{" "*(lbl_sz-len(label))}:'
        s += f' name={name}' if name is not None else ' <local>'
        print(s)

        # Elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'simpleContent':
                elems.append(XsdSimpleContent.build(k))
            elif tag(k) == 'complexContent':
                elems.append(XsdComplexContent.build(k))
            elif tag(k) == 'group':
                elems.append(XsdGroup.build(k))
            elif tag(k) == 'all':
                elems.append(XsdAll.build(k))
            elif tag(k) == 'choice':
                elems.append(XsdChoice.build(k))
            elif tag(k) == 'sequence':
                elems.append(XsdSequence.build(k))
            elif tag(k) == 'attribute':
                elems.append(XsdAttribute.build(k))
            # FIXME attributeGroup, anyAttribute
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:complexType'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, abstract=abstract, block=block,
                   final=final, mixed=mixed, annotation=annotation, elems=elems)

#-------------------------------------------------------------------------------

class XsdElement:
    """Declares an element.

    Content: (annotation?, ((simpleType | complexType)?, (unique | key |
    keyref)*))
    """
    def __init__(self, id_=None, name=None, ref=None, minOccurs=None,
                 maxOccurs=None, abstract=None, final=None, type_=None,
                 annotation=None, elems=None):
        self.id_ = id_
        self.name = name
        self.ref = ref
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.abstract = abstract
        self.final = final
        self.type_ = type_
        self.annotation = annotation
        # FIXME: to be continued...

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        ref = nd.attrib['ref'] if 'ref' in nd.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in nd.attrib else None
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in nd.attrib else None
        abstract = nd.attrib['abstract'] if 'abstract' in nd.attrib else None
        final = nd.attrib['final'] if 'final' in nd.attrib else None
        type_ = nd.attrib['type'] if 'type' in nd.attrib else None

        label = 'Element'
        s = f'{label}{" "*(lbl_sz-len(label))}:'
        s += f' name={name}' if name is not None else f' ref={ref}' \
            if ref is not None else ' Oops!'
        print(s)

        # Elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'simpleType':
                elems.append(XsdSimpleType.build(k))
            elif tag(k) == 'complexType':
                elems.append(XsdComplexType.build(k))
            elif tag(k) in ['key', 'keyref', 'unique']:
                print(f'Support for tag "{tag(k)}" not implemented', file=sys.stderr)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:element'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, ref=ref, minOccurs=minOccurs,
                   maxOccurs=maxOccurs, abstract=abstract, final=final,
                   type_=type_, annotation=annotation, elems=elems)

#-------------------------------------------------------------------------------

class XsdAll:
    """Allows the elements in the group to appear (or not appear) in any order in
    the containing element.

    Content: (annotation?, element*)

    """
    def __init__(self, annotation=None, elems=None):
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Sub-elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'element':
                elems.append(XsdElement.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:all'
                raise RuntimeError(m)

        return cls(id_=id_, annotation=annotation, elems=elems)

#-------------------------------------------------------------------------------

class XsdChoice:
    """Allows one and only one of the elements contained in the selected group to
    be present within the containing element.

    Content: (annotation?, (element | group | choice | sequence | any)*)

    """
    def __init__(self, id_=None, minOccurs=None, maxOccurs=None,
                 annotation=None, elems=None):
        self.id_ = id_
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in nd.attrib else None
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in nd.attrib else None

        # Sub-elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'element':
                elems.append(XsdElement.build(k))
            elif tag(k) == 'group':
                elems.append(XsdGroup.build(k))
            elif tag(k) == 'choice':
                elems.append(XsdChoice.build(k))
            elif tag(k) == 'sequence':
                elems.append(XsdSequence.build(k))
            elif tag(k) == 'any':
                elems.append(XsdAny.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:choice'
                raise RuntimeError(m)

        return cls(id_=id_, minOccurs=minOccurs, maxOccurs=maxOccurs,
                   annotation=annotation, elems=elems)

#-------------------------------------------------------------------------------

class XsdAny:
    """Enables any element from the specified namespace(s) to appear in the
    containing sequence or choice element.

    Content: (annotation?)

    """
    def __init__(self, id_=None, minOccurs=None, maxOccurs=None,
                 namespace=None, processContents=None, annotation=None):
        self.id_ = id_
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.annotation = annotation
        self.namespace = namespace
        self.processContents = processContents

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in nd.attrib else None
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in nd.attrib else None
        namespace = nd.attrib['namespace'] if 'namespace' in nd.attrib else None
        processContents = nd.attrib['processContents'] \
            if 'processContents' in nd.attrib else None

        # Sub-elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:any'
                raise RuntimeError(m)

        return cls(id_=id_, minOccurs=minOccurs, maxOccurs=maxOccurs,
                   namespace=namespace, processContents=processContents,
                   annotation=annotation)

#-------------------------------------------------------------------------------

class XsdSequence:
    """Requires the elements in the group to appear in the specified sequence
    within the containing element.

    Content: (annotation?, (element | group | choice | sequence | any)*)

    """
    def __init__(self, id_=None, minOccurs=None, maxOccurs=None,
                 annotation=None, elems=None):
        self.id_ = id_
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in nd.attrib else None
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in nd.attrib else None

        # Sub-elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'element':
                elems.append(XsdElement.build(k))
            elif tag(k) == 'group':
                elems.append(XsdGroup.build(k))
            elif tag(k) == 'choice':
                elems.append(XsdChoice.build(k))
            elif tag(k) == 'sequence':
                elems.append(XsdSequence.build(k))
            elif tag(k) == 'any':
                elems.append(XsdAny.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:sequence'
                raise RuntimeError(m)


        return cls(id_=id_, minOccurs=minOccurs, maxOccurs=maxOccurs,
                   annotation=annotation, elems=elems)

#-------------------------------------------------------------------------------

class XsdGroup:
    """This class represents an XSD group."""
    def __init__(self, id_=None, name=None, ref=None, minOccurs=None, maxOccurs=None,
                 annotation=None, elems=None):
        self.id_ = id_
        self.name = name
        self.ref = ref
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.annotation = annotation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        ref = nd.attrib['ref'] if 'ref' in nd.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in nd.attrib else None
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in nd.attrib else None

        label = 'Group'
        print(f'{label}{" "*(lbl_sz-len(label))}: name={name}')
        
        # Elements
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'all':
                elems.append(XsdAll.build(k))
            elif tag(k) == 'choice':
                elems.append(XsdChoice.build(k))
            elif tag(k) == 'sequence':
                elems.append(XsdSequence.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:group'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, ref=ref, minOccurs=minOccurs,
                   maxOccurs=maxOccurs, annotation=annotation, elems=elems)

#-------------------------------------------------------------------------------

class XsdImport:
    """Identifies a namespace whose schema components are referenced by the
    containing schema.

    Content: (annotation?)
    """
    def __init__(self, id_=None, namespace=None, schemaLocation=None,
                 annotation=None):
        self.id_ = id_
        self.namespace = namespace
        self.schemaLocation = schemaLocation

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        namespace = nd.attrib['namespace'] if 'namespace' in nd.attrib else None
        schemaLocation = nd.attrib['schemaLocation'] if 'schemaLocation' in nd.attrib else None
        
        # Elements
        annotation = None
        for k in nd:
            if tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:import'
                raise RuntimeError(m)

        return cls(id_=id_, namespace=namespace, schemaLocation=schemaLocation,
                   annotation=annotation)

#-------------------------------------------------------------------------------

class XMLSchema:
    """Contains the definition of a schema.

    Content: ((include | import | redefine | annotation)*, (((simpleType |
    complexType | group | attributeGroup) | element | attribute | notation),
    annotation*)*)

    """
    def __init__(self, id_=None, attributeFormDefault=None, blockDefault=None,
                 elementFormDefault=None, finalDefault=None,
                 targetNamespace=None, version=None, lang=None, import_=None,
                 annotation=None):
        self.id_ = id_
        self.attributeFormDefault = attributeFormDefault
        self.blockDefault = blockDefault
        self.elementFormDefault = elementFormDefault
        self.finalDefault = finalDefault
        self.targetNamespace = targetNamespace
        self.version = version
        self.lang = lang
        self.import_ = import_
        self.annotation = annotation
        
        self.attrs = {}
        self.elems = {}
        self.groups = {}
        self.other = {}

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        attributeFormDefault = nd.attrib['attributeFormDefault'] if 'attributeFormDefault' in nd.attrib else None
        blockDefault = nd.attrib['blockDefault'] if 'blockDefault' in nd.attrib else None
        elementFormDefault = nd.attrib['elementFormDefault'] if 'elementFormDefault' in nd.attrib else None
        finalDefault = nd.attrib['finalDefault'] if 'finalDefault' in nd.attrib else None
        targetNamespace = nd.attrib['targetNamespace'] if 'targetNamespace' in nd.attrib else None
        version = nd.attrib['version'] if 'version' in nd.attrib else None
        lang = nd.attrib['lang'] if 'lang' in nd.attrib else None
        
        # Elements
        import_ = None
        annotation = None
        elems = []
        for k in nd:
            if tag(k) == 'import':
                import_ = XsdImport.build(k)
            elif tag(k) == 'annotation':
                annotation = XsdAnnotation.build(k)
            elif tag(k) == 'attribute':
                elems.append(XsdAttribute.build(k))
            elif tag(k) == 'element':
                elems.append(XsdElement.build(k))
            elif tag(k) == 'group':
                elems.append(XsdGroup.build(k))
            elif tag(k) == 'simpleType':
                elems.append(XsdSimpleType.build(k))
            elif tag(k) == 'complexType':
                elems.append(XsdComplexType.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:schema'
                raise RuntimeError(m)

        return cls(id_=id_, attributeFormDefault=attributeFormDefault,
                   blockDefault=blockDefault,
                   elementFormDefault=elementFormDefault,
                   finalDefault=finalDefault, targetNamespace=targetNamespace,
                   version=version, lang=lang, annotation=annotation,
                   import_=import_)
            
    def parse_node(self, nd):
        klasses = {
            'appinfo': XsdAppinfo,
            'documentation': XsdDocumentation,
            'annotation': XsdAnnotation,
            'list': XsdList,
            # 'restriction': XsdRestriction,
            'union': XsdUnion,
            'simpleType': XsdSimpleType,
            'complexType': XsdComplextype,
            'element': XsdElement,
            'all': XsdAll,
            'choice': XsdChoice,
            'sequence': XsdSequence,
            'group': XsdGroup,
            'extension': XsdExtension,
        }
        if tag(nd) in klasses:
            return klasses[tag(nd)].build(k)
        elif tag(nd) == 'restriction':
            # FIXME: three possibilities: simpleType, simpleContent, complexContent
            pass
        elif tag(nd) == 'extension':
            # FIXME: two possibilities: simpleContent, complexContent
            pass
        else:
            m = f'Unexpected tag "{tag(k)}"'
            raise RuntimeError(m)
        
    def dictify(self):
        return {
            'types': {k: v.dictify() for k, v in self.types.items()},
            'elems': {k: v.dictify() for k, v in self.elems.items()},
        }

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

#-------------------------------------------------------------------------------

def parse_schema(filepath):
    # Ignore comments
    p = et.XMLParser(remove_comments=True)
    root = objectify.parse(filepath, parser=p).getroot()

    xsd = XMLSchema.build(root)
    return xsd

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xsd filepath>')
        exit(-1)
    filepath = sys.argv[1]

    xsd = parse_schema(filepath)
    # print(xsd)
