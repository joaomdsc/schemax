# parse_xsd.py - parse an XML Schema file (assumed to be valid)

import os
import sys
import json
import requests
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

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.source is not None:
            obj['source'] = self.source
        if self.content is not None:
            obj['content'] = self.content
        return obj

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

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.source is not None:
            obj['source'] = self.source
        if self.lang is not None:
            obj['lang'] = self.lang
        if self.content is not None:
            obj['content'] = self.content
        return obj

#-------------------------------------------------------------------------------

class XsdAnnotation:
    """Defines an annotation.

    Content: (appinfo | documentation)*
    """
    def __init__(self, id_=None, elems=None):
        self.id_ = id_

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        
        # Sub-elements
        elems = []
        for k in nd:
            if tag(k) == 'appinfo':
                elems.append(XsdAppinfo.build(k))
            elif tag(k) == 'documentation':
                elems.append(XsdDocumentation.build(k))

        return cls(id_, elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdList:
    """Defines a collection of a single simpleType definition.

    Content: (annotation?, (simpleType?))

    """
    def __init__(self, id_=None, itemType=None, elems=None):
        self.id_ = id_
        self.itemType = itemType

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        itemType = nd.attrib['itemType'] if 'itemType' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'simpleType':
                elems.append(XsdSimpleType.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:list'
                raise RuntimeError(m)

        return cls(id_=id_, itemType=itemType, elems=elems)
        
    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.itemType is not None:
            obj['itemType'] = self.itemType
         # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdPattern:
    """Facet to define a regular expression pattern constraint.

    Content: (annotation?)

    """
    def __init__(self, id_=None, value=None, annotation=None):
        self.id_ = id_
        self.value = value

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        value = nd.attrib['value'] if 'value' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:pattern'
                raise RuntimeError(m)

        return cls(id_=id_, value=value)

#-------------------------------------------------------------------------------

class XsdEnumeration:
    """Facet to restrict a datatype to a finite set of values.

    Content: (annotation?)

    """
    def __init__(self, id_=None, value=None, elems=None):
        self.id_ = id_
        self.value = value

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        value = nd.attrib['value'] if 'value' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:enumeration'
                raise RuntimeError(m)

        return cls(id_=id_, value=value, elems=elems)

#-------------------------------------------------------------------------------

class XsdMaxExclusive:
    """Facet to define a maximum (exclusive) value.

    Content: (annotation?)

    """
    def __init__(self, id_=None, value=None, fixed=None, elems=None):
        self.id_ = id_
        self.value = value
        self.fixed = fixed

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        value = nd.attrib['value'] if 'value' in nd.attrib else None
        fixed = nd.attrib['fixed'] if 'fixed' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:maxExclusive'
                raise RuntimeError(m)

        return cls(id_=id_, value=value, fixed=fixed, elems=elems)

#-------------------------------------------------------------------------------

class XsdMaxInclusive:
    """Facet to define a maximum (inclusive) value.

    Content: (annotation?)

    """
    def __init__(self, id_=None, value=None, fixed=None, elems=None):
        self.id_ = id_
        self.value = value
        self.fixed = fixed

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        value = nd.attrib['value'] if 'value' in nd.attrib else None
        fixed = nd.attrib['fixed'] if 'fixed' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:maxInclusive'
                raise RuntimeError(m)

        return cls(id_=id_, value=value, fixed=fixed, elems=elems)

#-------------------------------------------------------------------------------

class XsdMaxLength:
    """Facet to define a maximum length.

    Content: (annotation?)

    """
    def __init__(self, id_=None, value=None, fixed=None, elems=None):
        self.id_ = id_
        self.value = value
        self.fixed = fixed

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        value = nd.attrib['value'] if 'value' in nd.attrib else None
        fixed = nd.attrib['fixed'] if 'fixed' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:maxLength'
                raise RuntimeError(m)

        return cls(id_=id_, value=value, fixed=fixed, elems=elems)

#-------------------------------------------------------------------------------

class XsdMinLength:
    """Facet to define a minimum length.

    Content: (annotation?)

    """
    def __init__(self, id_=None, value=None, fixed=None, elems=None):
        self.id_ = id_
        self.value = value
        self.fixed = fixed

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        value = nd.attrib['value'] if 'value' in nd.attrib else None
        fixed = nd.attrib['fixed'] if 'fixed' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:minLength'
                raise RuntimeError(m)

        return cls(id_=id_, value=value, fixed=fixed, elems=elems)

#-------------------------------------------------------------------------------

class XsdMinExclusive:
    """Facet to define a minimum (exclusive) value.

    Content: (annotation?)

    """
    def __init__(self, id_=None, value=None, fixed=None, elems=None):
        self.id_ = id_
        self.value = value
        self.fixed = fixed

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        value = nd.attrib['value'] if 'value' in nd.attrib else None
        fixed = nd.attrib['fixed'] if 'fixed' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:minExclusive'
                raise RuntimeError(m)

        return cls(id_=id_, value=value, fixed=fixed, elems=elems)

#-------------------------------------------------------------------------------

class XsdMinInclusive:
    """Facet to define a minimum (inclusive) value.

    Content: (annotation?)

    """
    def __init__(self, id_=None, value=None, fixed=None, elems=None):
        self.id_ = id_
        self.value = value
        self.fixed = fixed

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        value = nd.attrib['value'] if 'value' in nd.attrib else None
        fixed = nd.attrib['fixed'] if 'fixed' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:minInclusive'
                raise RuntimeError(m)

        return cls(id_=id_, value=value, fixed=fixed, elems=elems)

#-------------------------------------------------------------------------------

class XsdRestrictionST:
    """Defines constraints on a simpleType definition.

    Content: (annotation?, (simpleType?, (minExclusive | minInclusive |
    maxExclusive | maxInclusive | totalDigits |fractionDigits | length |
    minLength | maxLength | enumeration | whiteSpace | pattern)*))

    """
    def __init__(self, id_=None, base=None, elems=None):
        self.id_ = id_
        self.base = base
        self.elems = elems

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'enumeration':
                elems.append(XsdEnumeration.build(k))
            elif tag(k) == 'maxExclusive':
                elems.append(XsdMaxExclusive.build(k))
            elif tag(k) == 'maxInclusive':
                elems.append(XsdMaxInclusive.build(k))
            elif tag(k) == 'maxLength':
                elems.append(XsdMaxLength.build(k))
            elif tag(k) == 'minExclusive':
                elems.append(XsdMinExclusive.build(k))
            elif tag(k) == 'minInclusive':
                elems.append(XsdMinInclusive.build(k))
            elif tag(k) == 'minLength':
                elems.append(XsdMinLength.build(k))
            elif tag(k) == 'pattern':
                elems.append(XsdPattern.build(k))
            elif tag(k) in ['fractionDigits', 'length', 'simpleType',
                            'totalDigits', 'whiteSpace']:
                m = f'Support for tag "{tag(k)}" not implemented'
                print(m, file=sys.stderr)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:restriction' \
                    ' (simpleType)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, elems=elems)
        
    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.base is not None:
            obj['base'] = self.base           
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdUnion:
    """Defines a collection of multiple simpleType definitions.

    Content: (annotation?, (simpleType*))

    """
    def __init__(self, id_=None, memberTypes=None, elems=None):
        self.id_ = id_
        self.memberTypes = memberTypes

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        memberTypes = nd.attrib['memberTypes'] if 'memberTypes' in nd.attrib \
            else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'simpleType':
                elems.append(XsdSimpleType.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:union'
                raise RuntimeError(m)

        return cls(id_=id_, memberTypes=memberTypes,
                   elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.memberTypes is not None:
            obj['memberTypes'] = self.memberTypes
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdSimpleType:
    """Defines a simple type, which determines the constraints on and information
    about the values of attributes or elements with text-only content.

    Content: (annotation?, (restriction | list | union))

    """
    def __init__(self, id_=None, name=None, final=None, elems=None):
        self.id_ = id_
        self.name = name
        self.final = final

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
        # print(f'{label}{" "*(lbl_sz-len(label))}: name={name}')

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'list':
                elems.append(XsdList.build(k))
            elif tag(k) == 'restriction':
                elems.append(XsdRestrictionST.build(k))
            elif tag(k) == 'union':
                elems.append(XsdUnion.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:simpleType'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, final=final,
                   elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.name is not None:
            obj['name'] = self.name
        if self.final is not None:
            obj['final'] = self.final
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdRestrictionSC:
    """Defines constraints on a simpleContent definition.

    Content: (annotation?, (simpleType?, (minExclusive | minInclusive | 
    maxExclusive | maxInclusive | totalDigits |fractionDigits | length | 
    minLength | maxLength | enumeration | whiteSpace | pattern)*)?, 
    ((attribute | attributeGroup)*, anyAttribute?))

    """
    def __init__(self, id_=None, base=None, elems=None):
        self.id_ = id_
        self.base = base

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        elems= []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'enumeration':
                elems.append(XsdEnumeration.build(k))
            elif tag(k) == 'maxExclusive':
                elems.append(XsdMaxExclusive.build(k))
            elif tag(k) == 'maxInclusive':
                elems.append(XsdMaxInclusive.build(k))
            elif tag(k) == 'maxLength':
                elems.append(XsdMaxLength.build(k))
            elif tag(k) == 'minExclusive':
                elems.append(XsdMinExclusive.build(k))
            elif tag(k) == 'minInclusive':
                elems.append(XsdMinInclusive.build(k))
            elif tag(k) == 'minLength':
                elems.append(XsdMinLength.build(k))
            elif tag(k) == 'pattern':
                elems.append(XsdPattern.build(k))
            elif tag(k) == 'attribute':
                elems.append(XsdAttribute.build(k))
            elif tag(k) == 'attributeGroup':
                elems.append(XsdAttributeGroup.build(k))
            elif tag(k) == 'anyAttribute':
                elems.append(XsdAnyAttribute.build(k))
            elif tag(k) in ['fractionDigits', 'length', 'simpleType',
                            'totalDigits', 'whiteSpace']:
                m = f'Support for tag "{tag(k)}" not implemented'
                print(m, file=sys.stderr)
            # FIXME attribute, attributeGroup
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:restriction' \
                    ' (simpleContent)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, elems=elems)

#-------------------------------------------------------------------------------

class XsdExtensionSC:
    """Contains extensions on simpleContent. This extends a simple type or a
    complex type that has simple content by adding specified attribute(s),
    attribute group(s), or anyAttribute.

    Content: (annotation?, ((attribute | attributeGroup)*, anyAttribute?))

    """
    def __init__(self, id_=None, base=None, elems=None):
        self.id_ = id_
        self.base = base

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'attribute':
                elems.append(XsdAttribute.build(k))
            elif tag(k) == 'attributeGroup':
                elems.append(XsdAttributeGroup.build(k))
            elif tag(k) == 'anyAttribute':
                elems.append(XsdAnyAttribute.build(k))
            # FIXME attributeGroup, anyAttribute
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:extension' \
                    ' (simpleContent)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, elems=elems)
        
    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.base is not None:
            obj['base'] = self.base
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdSimpleContent:
    """Contains extensions or restrictions on a complexType element with character
    data or a simpleType element as content and contains no elements.

    Content: (annotation?, (restriction | extension))

    """
    def __init__(self, id_=None, elems=None):
        self.id_ = id_

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'restriction':
                elems.append(XsdRestrictionSC.build(k))
            elif tag(k) == 'extension':
                elems.append(XsdExtensionSC.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:simpleContent'
                raise RuntimeError(m)

        return cls(id_=id_, elems=elems)
        
    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdRestrictionCC:
    """Defines constraints on a complexContent definition.

    Content: (annotation?, (group | all | choice | sequence)?, ((attribute | 
    attributeGroup)*, anyAttribute?))

    """
    def __init__(self, id_=None, base=None, elems=None):
        self.id_ = id_
        self.base = base

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
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
            elif tag(k) == 'attributeGroup':
                elems.append(XsdAttributeGroup.build(k))
            elif tag(k) == 'anyAttribute':
                elems.append(XsdAnyAttribute.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:restriction' \
                    ' (complexContent)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, elems=elems)

#-------------------------------------------------------------------------------

class XsdExtensionCC:
    """Contains extensions on complexContent.

    Content: (annotation?, ((group | all | choice | sequence)?, ((attribute |
    attributeGroup)*, anyAttribute?)))

    """
    def __init__(self, id_=None, base=None, elems=None):
        self.id_ = id_
        self.base = base

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        base = nd.attrib['base'] if 'base' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
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
            elif tag(k) == 'attributeGroup':
                elems.append(XsdAttributeGroup.build(k))
            elif tag(k) == 'anyAttribute':
                elems.append(XsdAnyAttribute.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:extension' \
                    ' (complexContent)'
                raise RuntimeError(m)

        return cls(id_=id_, base=base, elems=elems)
        
    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.base is not None:
            obj['base'] = self.base
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdComplexContent:
    """Contains extensions or restrictions on a complex type that contains mixed
    content or elements only.

    Content: (annotation?,  (restriction | extension))

    """
    def __init__(self, id_=None, mixed=None, elems=None):
        self.id_ = id_
        self.mixed = mixed

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        mixed = nd.attrib['mixed'] if 'mixed' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'restriction':
                elems.append(XsdRestrictionCC.build(k))
            elif tag(k) == 'extension':
                elems.append(XsdExtensionCC.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:complexContent'
                raise RuntimeError(m)

        return cls(id_=id_, mixed=mixed, elems=elems)
        
    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.mixed is not None:
            obj['mixed'] = self.mixed
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdSequence:
    """Requires the elements in the group to appear in the specified sequence
    within the containing element.

    Content: (annotation?, (element | group | choice | sequence | any)*)

    """
    def __init__(self, id_=None, minOccurs=None, maxOccurs=None,
                 elems=None):
        self.id_ = id_
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs

        self.elems = []
        if elems is not None:
            self.elems = elems

    # See <xs:complexType name="fx_surface_common"> in collada

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        minOccurs = nd.attrib['minOccurs'] if 'minOccurs' in nd.attrib else None
        maxOccurs = nd.attrib['maxOccurs'] if 'maxOccurs' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
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
                   elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.minOccurs is not None:
            obj['minOccurs'] = self.minOccurs
        if self.maxOccurs is not None:
            obj['maxOccurs'] = self.maxOccurs
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdAttribute:
    """Declares an attribute.

    Content: (annotation?, (simpleType?))

    """
    def __init__(self, id_=None, name=None, ref=None, type_=None, default=None,
                 fixed=None, form=None, use=None, elems=None):
        self.id_ = id_
        self.name = name
        self.ref = ref
        self.type_ = type_
        self.default = default
        self.fixed = fixed
        self.form = form
        self.use = use

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
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'simpleType':
                elems.append(XsdSimpleType.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:attribute'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, ref=ref, type_=type_, default=default,
                   fixed=fixed, form=form, use=use, elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.name is not None:
            obj['name'] = self.name
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdAttributeGroup:
    """Groups a set of attribute declarations so that they can be incorporated as a
    group for complex type definitions.

    Content: (annotation?), ((attribute | attributeGroup)*, anyAttribute?))

    """
    def __init__(self, id_=None, name=None, ref=None, elems=None):
        self.id_ = id_
        self.name = name
        self.ref = ref

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        name = nd.attrib['name'] if 'name' in nd.attrib else None
        ref = nd.attrib['ref'] if 'ref' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'attribute':
                elems.append(XsdAttribute.build(k))
            elif tag(k) == 'attributeGroup':
                elems.append(XsdAttributeGroup.build(k))
            elif tag(k) == 'anyAttribute':
                elems.append(XsdAnyAttribute.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:attributeGroup'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, ref=ref, elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.name is not None:
            obj['name'] = self.name
        if self.ref is not None:
            obj['ref'] = self.ref
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdAnyAttribute:
    """Enables any attribute from the specified namespace(s) to appear in the
    containing complexType element or in the containing attributeGroup element.

    Content: (annotation?)

    Namespace:
    ----------
    ##any: Attributes from any namespace can be present.

    ##other: Attributes from any namespace that is not the target namespace of
    the parent element containing this anyAttribute element can be present.

    ##local: Attributes that are not qualified with a namespace can be present.

    ##targetNamespace: Attributes from the target namespace of the parent
    element containing this anyAttribute element can be present.

    List of {URI references, ##targetNamespace, ##local}: Attributes from a
    space-delimited list of the namespaces can be present. The list can contain
    the following: URI references of namespaces, ##targetNamespace, and
    ##local.

    processContents:
    ----------------

    strict: The XML processor must obtain the schema for the required
    namespaces and validate any attribute from those namespaces.

    lax: The XML processor attempts to obtain the schema for the
    required namespaces and validate any attribute from those
    namespaces; however, if the schema cannot be obtained, no errors
    will occur.

    skip: The XML processor does not attempt to validate any
    attributes from the specified namespaces.

    """
    def __init__(self, id_=None, namespace=None, processContents=None,
                 elems=None):
        self.id_ = id_
        self.namespace = namespace
        self.processContents = processContents

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        namespace = nd.attrib['namespace'] if 'namespace' in nd.attrib else None
        processContents = nd.attrib['processContents'] \
            if 'processContents' in nd.attrib else None

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:attribute'
                raise RuntimeError(m)

        return cls(id_=id_, namespace=namespace,
                   processContents=processContents, elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.namespace is not None:
            obj['namespace'] = self.namespace
        if self.processContents is not None:
            obj['processContents'] = self.processContents
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdComplexType:
    """Defines a complex type, which determines the set of attributes and the
    content of an element.

    Content: (annotation?, (simpleContent | complexContent | ((group | all |
    choice | sequence)?, ((attribute | attributeGroup)*, anyAttribute?))))

    """
    def __init__(self, id_=None, name=None, abstract=None, block=None,
                 final=None, mixed=None, elems=None):
        self.id_ = id_
        self.name = name
        self.abstract = abstract
        self.block = block
        self.final = final
        self.mixed = mixed

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

        attrs = []


        label = 'ComplexType'
        s = f'{label}{" "*(lbl_sz-len(label))}:'
        s += f' name={name}' if name is not None else ' <local>'
        # print(s)

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
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
            elif tag(k) == 'attributeGroup':
                elems.append(XsdAttributeGroup.build(k))
            elif tag(k) == 'anyAttribute':
                elems.append(XsdAnyAttribute.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:complexType'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, abstract=abstract, block=block,
                   final=final, mixed=mixed, elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.name is not None:
            obj['name'] = self.name
        if self.abstract is not None:
            obj['abstract'] = self.abstract
        if self.block is not None:
            obj['block'] = self.block
        if self.final is not None:
            obj['final'] = self.final
        if self.mixed is not None:
            obj['mixed'] = self.mixed
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdElement:
    """Declares an element.

    Content: (annotation?, ((simpleType | complexType)?, (unique | key |
    keyref)*))
    """
    def __init__(self, id_=None, name=None, ref=None, minOccurs=None,
                 maxOccurs=None, abstract=None, final=None, type_=None,
                 elems=None):
        self.id_ = id_
        self.name = name
        self.ref = ref
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.abstract = abstract
        self.final = final
        self.type_ = type_
        # FIXME: to be continued...

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
        abstract = nd.attrib['abstract'] if 'abstract' in nd.attrib else None
        final = nd.attrib['final'] if 'final' in nd.attrib else None
        type_ = nd.attrib['type'] if 'type' in nd.attrib else None

        label = 'Element'
        s = f'{label}{" "*(lbl_sz-len(label))}:'
        s += f' name={name}' if name is not None else f' ref={ref}' \
            if ref is not None else ' Oops!'
        # print(s)

        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'simpleType':
                elems.append(XsdSimpleType.build(k))
            elif tag(k) == 'complexType':
                elems.append(XsdComplexType.build(k))
            elif tag(k) in ['key', 'keyref', 'unique']:
                print(f'Support for tag "{tag(k)}" not implemented',
                      file=sys.stderr)
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:element'
                raise RuntimeError(m)

        return cls(id_=id_, name=name, ref=ref, minOccurs=minOccurs,
                   maxOccurs=maxOccurs, abstract=abstract, final=final,
                   type_=type_, elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.name is not None:
            obj['name'] = self.name
        if self.ref is not None:
            obj['ref'] = self.ref
        if self.minOccurs is not None:
            obj['minOccurs'] = self.minOccurs
        if self.maxOccurs is not None:
            obj['maxOccurs'] = self.maxOccurs
        if self.abstract is not None:
            obj['abstract'] = self.abstract
        if self.final is not None:
            obj['final'] = self.final
        if self.type_ is not None:
            obj['type_'] = self.type_
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdAll:
    """Allows the elements in the group to appear (or not appear) in any order in
    the containing element.

    Content: (annotation?, element*)

    """
    def __init__(self, elems=None):

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Sub-elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'element':
                elems.append(XsdElement.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:all'
                raise RuntimeError(m)

        return cls(id_=id_, elems=elems)

#-------------------------------------------------------------------------------

class XsdChoice:
    """Allows one and only one of the elements contained in the selected group to
    be present within the containing element.

    Content: (annotation?, (element | group | choice | sequence | any)*)

    """
    def __init__(self, id_=None, minOccurs=None, maxOccurs=None, elems=None):
        self.id_ = id_
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs

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
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
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
                   elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.minOccurs is not None:
            obj['minOccurs'] = self.minOccurs
        if self.maxOccurs is not None:
            obj['maxOccurs'] = self.maxOccurs
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdAny:
    """Enables any element from the specified namespace(s) to appear in the
    containing sequence or choice element.

    Content: (annotation?)

    """
    def __init__(self, id_=None, minOccurs=None, maxOccurs=None,
                 namespace=None, processContents=None, elems=None):
        self.id_ = id_
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.namespace = namespace
        self.processContents = processContents

        self.elems = []
        if elems is not None:
            self.elems = elems

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
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:any'
                raise RuntimeError(m)

        return cls(id_=id_, minOccurs=minOccurs, maxOccurs=maxOccurs,
                   namespace=namespace, processContents=processContents,
                   elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.minOccurs is not None:
            obj['minOccurs'] = self.minOccurs
        if self.maxOccurs is not None:
            obj['maxOccurs'] = self.maxOccurs
        if self.namespace is not None:
            obj['namespace'] = self.namespace
        if self.processContents is not None:
            obj['processContents'] = self.processContents
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdGroup:
    """Groups a set of element declarations so that they can be incorporated as a
    group into complex type definitions.

    Content: (annotation?, (all | choice | sequence))

    """
    def __init__(self, id_=None, name=None, ref=None, minOccurs=None,
                 maxOccurs=None, elems=None):
        self.id_ = id_
        self.name = name
        self.ref = ref
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs

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
        # print(f'{label}{" "*(lbl_sz-len(label))}: name={name}')
        
        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
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
                   maxOccurs=maxOccurs, elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.name is not None:
            obj['name'] = self.name
        if self.ref is not None:
            obj['ref'] = self.ref
        if self.minOccurs is not None:
            obj['minOccurs'] = self.minOccurs
        if self.maxOccurs is not None:
            obj['maxOccurs'] = self.maxOccurs
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

#-------------------------------------------------------------------------------

class XsdInclude:
    """Includes the specified schema document in the target namespace of the
    containing schema.

    Content: (annotation?)

    """
    def __init__(self, id_=None, schemaLocation=None, elems=None):
        self.id_ = id_
        self.schemaLocation = schemaLocation

        self.elems = []
        if elems is not None:
            self.elems = elems

    @classmethod
    def build(cls, nd):
        # Attributes
        id_ = nd.attrib['id'] if 'id' in nd.attrib else None
        schemaLocation = nd.attrib['schemaLocation'] \
            if 'schemaLocation' in nd.attrib else None
        
        # Elements
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            else:
                m = f'Unexpected tag "{tag(k)}" inside an xs:include'
                raise RuntimeError(m)

        return cls(id_=id_, schemaLocation=schemaLocation, elems=elems)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.schemaLocation is not None:
            obj['schemaLocation'] = self.schemaLocation
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

    def get_schema(self, dirpath):
        # Look for a schema file in the same directory where we found the
        # current one
        path = self.schemaLocation if dirpath is None \
            else os.path.join(dirpath, self.schemaLocation)
        if os.path.isfile(path):
            print(f'{self.__class__.__name__}: getting schema {self.schemaLocation} (from file)',
                  file=sys.stderr)
            return XMLSchema.from_file(path)
        else:
            # If it can't be read as a file, try to get it from the net
            r = requests.get(self.schemaLocation)
            if r.status_code >= 400:
                m = f'Couldn\'t download "{inc.schemaLocation}",' \
                    f' status={r.status_code}'
                raise RuntimeError(m)
            # Ignore comments
            p = et.XMLParser(remove_comments=True)
            root = objectify.fromstring(r.content.decode(), parser=p).getroot()
            print(f'Including schema {self.schemaLocation} (from url)',
                  file=sys.stderr)
            return XMLSchema.build(root, dirpath)

#-------------------------------------------------------------------------------

class XsdImport(XsdInclude):
    """Identifies a namespace whose schema components are referenced by the
    containing schema.

    Content: (annotation?)
    """
    def __init__(self, id_=None, namespace=None, schemaLocation=None,
                 elems=None):
        super().__init__(id_=id_, schemaLocation=schemaLocation, elems=elems)
        self.namespace = namespace

    @classmethod
    def build(cls, nd):
        x = XsdInclude.build(nd)
        
        # Attributes
        id_ = x.id_
        namespace = nd.attrib['namespace'] if 'namespace' in nd.attrib else None
        schemaLocation = x.schemaLocation
        elems = x.elems

        return cls(id_=id_, namespace=namespace, schemaLocation=schemaLocation,
                   elems=elems)

    def dictify(self):
        obj = super().dictify()
        # Attributes
        if self.namespace is not None:
            obj['namespace'] = self.namespace
        return obj
 
#-------------------------------------------------------------------------------

class XMLSchema:
    """Contains the definition of a schema.

    Content: ((include | import | redefine | annotation)*, (((simpleType |
    complexType | group | attributeGroup) | element | attribute | notation),
    annotation*)*)

    """
    def __init__(self, id_=None, attributeFormDefault=None, blockDefault=None,
                 elementFormDefault=None, finalDefault=None,
                 targetNamespace=None, version=None, lang=None, includes=None,
                 imports=None, elems=None, filepath=None):
        self.id_ = id_
        self.attributeFormDefault = attributeFormDefault
        self.blockDefault = blockDefault
        self.elementFormDefault = elementFormDefault
        self.finalDefault = finalDefault
        self.targetNamespace = targetNamespace
        self.version = version
        self.lang = lang
        self.filepath = filepath

        self.includes = []
        if includes is not None:
            self.includes = includes

        self.imports = []
        if imports is not None:
            self.imports = imports

        self.elems = []
        if elems is not None:
            self.elems = elems

        # Get included schemas
        inc_schemas = []
        for inc in includes:
            sch = inc.get_schema(self.dirpath)

        # Get imported schemas
        prev = [self.filepath]
        imp_schemas = []
        for imp in imports:
            sch = imp.get_schema(self.filepath)

    @classmethod
    def build(cls, nd, filepath):
        """nd is expected to be the root node of the XML tree obtained when parsing an
        XML Schema.

        """
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
        includes = []
        imports = []
        elems = []
        for k in nd:
            if tag(k) == 'annotation':
                elems.append(XsdAnnotation.build(k))
            elif tag(k) == 'include':
                x = XsdInclude.build(k)
                includes.append(x)
                elems.append(x)
            elif tag(k) == 'import':
                x = XsdImport.build(k)
                imports.append(x)
                elems.append(x)
            elif tag(k) == 'attribute':
                elems.append(XsdAttribute.build(k))
            elif tag(k) == 'attributeGroup':
                elems.append(XsdAttributeGroup.build(k))
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
                   version=version, lang=lang, includes=includes,
                   imports=imports, elems=elems, filepath=filepath)
        
    @classmethod
    def from_file(cls, filepath):
        """filepath is an XML file containing an XML Schema definition.

        """
        # Ignore comments
        p = et.XMLParser(remove_comments=True)
        root = objectify.parse(filepath, parser=p).getroot()
        return cls.build(root, filepath)

    def dictify(self):
        obj = { 'elem_type': self.__class__.__name__ }
        # Attributes
        if self.id_ is not None:
            obj['id'] = self.id_
        if self.attributeFormDefault is not None:
            obj['attributeFormDefault'] = self.attributeFormDefault
        if self.blockDefault is not None:
            obj['blockDefault'] = self.blockDefault
        if self.elementFormDefault is not None:
            obj['elementFormDefault'] = self.elementFormDefault
        if self.finalDefault is not None:
            obj['finalDefault'] = self.finalDefault
        if self.targetNamespace is not None:
            obj['targetNamespace'] = self.targetNamespace
        if self.version is not None:
            obj['version'] = self.version
        if self.lang is not None:
            obj['lang'] = self.lang
        # Sub-elements
        if len(self.elems) > 0:
            obj['elems'] = [e.dictify() for e in self.elems]
        return obj

    def __str__(self):
        return json.dumps(self.dictify(), indent=4)

    #---------------------------------------------------------------------------

    def assemble(self):
        """Assemble the different pieces together.

        We need dictionaries of everything that can be referenced: toplevel
        elements, types, groups, attributes, and attribute groups. These
        dictionaries must be merged from all the imported or included schemas.

        """

#-------------------------------------------------------------------------------

def parse_schema(filepath):
    xsd = XMLSchema.from_file(filepath)
    print(xsd)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xsd filepath>')
        exit(-1)
    filepath = sys.argv[1]

    parse_schema(filepath)
