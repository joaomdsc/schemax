# parse_collada.py - parse an XML instance document (assumed to be valid)

"""\

Handwritten parsing code, as preparation for the code generation to be done in
parse_xsd.py.

"""

import sys
import json
import lxml.etree as et
from lxml import objectify

#-------------------------------------------------------------------------------

def tag(nd):
    return et.QName(nd).localname

#-------------------------------------------------------------------------------

class Unit():
    def __init__(self, meter=None, name=None):
        self.meter = meter
        self.name = name

    @classmethod
    def build(cls, nd):

        # unit is a complexType with 2 attributes
        # Get self's attributes
        meter = float(nd.attrib.get('meter'))
        name = nd.attrib.get('name')

        return cls(meter=meter, name=name)

    def dictify(self):
        obj = {}
        # Attributes
        if self.meter is not None:
            obj['meter'] = self.meter
        if self.name is not None:
            obj['name'] = self.name
        return obj

#-------------------------------------------------------------------------------

class Contributor():
    def __init__(self, author=None, authoring_tool=None, comments=None,
                 copyright_=None, source_data=None):
        self.author = author
        self.authoring_tool = authoring_tool
        self.comments = comments
        self.copyright_ = copyright_
        self.source_data = source_data
    
    @classmethod
    def build(cls, nd):
        # contributor is a complexType/sequence of 5 simpleType elements
        # Get self's sub-elements
        k = next((k for k in nd if tag(k) == 'author'), None)
        author = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'authoring_tool'), None)
        authoring_tool = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'comments'), None)
        comments = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'copyright_'), None)
        copyright_ = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'source_data'), None)
        source_data = k.text if k is not None else None

        return cls(author=author, authoring_tool=authoring_tool,
                   comments=comments, copyright_=copyright_,
                   source_data=source_data)

    def dictify(self):
        obj = {}
        # Sub-elements
        if self.author is not None:
            obj['author'] = self.author
        if self.authoring_tool is not None:
            obj['authoring_tool'] = self.authoring_tool
        if self.comments is not None:
            obj['comments'] = self.comments
        if self.copyright_ is not None:
            obj['copyright_'] = self.copyright_
        if self.source_data is not None:
            obj['source_data'] = self.source_data
        return obj

#-------------------------------------------------------------------------------

class Asset():
    def __init__(self, contributor=None, created=None, keywords=None, modified=None,
                 revision=None, subject=None, title=None, unit=None, up_axis=None):
        self.contributor = contributor
        self.created = created
        self.keywords = keywords
        self.modified = modified
        self.revision = revision
        self.subject = subject
        self.title = title
        self.unit = unit
        self.up_axis = up_axis
        
    @classmethod
    def build(cls, nd):
        # asset is a complexType/sequence of 9 elements (some simple, some complex)
        k = next((k for k in nd if tag(k) == 'contributor'), None)
        contributor = Contributor.build(k) if k is not None else None
        k = next((k for k in nd if tag(k) == 'created'), None)
        created = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'keywords'), None)
        keywords = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'modified'), None)
        modified = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'revision'), None)
        revision = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'subject'), None)
        subject = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'title'), None)
        title = k.text if k is not None else None
        k = next((k for k in nd if tag(k) == 'unit'), None)
        unit = Unit.build(k) if k is not None else None
        k = next((k for k in nd if tag(k) == 'up_axis'), None)
        up_axis = k.text if k is not None else None

        return cls(contributor=contributor, created=created, keywords=keywords,
                   modified=modified, revision=revision, subject=subject, title=title,
                   unit=unit, up_axis=up_axis)

    def dictify(self):
        obj = {}
        # Sub-elements
        if self.contributor is not None:
            obj['contributor'] = self.contributor.dictify()
        if self.created is not None:
            obj['created'] = self.created
        if self.keywords is not None:
            obj['keywords'] = self.keywords
        if self.modified is not None:
            obj['modified'] = self.modified
        if self.revision is not None:
            obj['revision'] = self.revision
        if self.subject is not None:
            obj['subject'] = self.subject
        if self.title is not None:
            obj['title'] = self.title
        if self.unit is not None:
            obj['unit'] = self.unit.dictify()
        if self.up_axis is not None:
            obj['up_axis'] = self.up_axis
        return obj

#-------------------------------------------------------------------------------

class LibraryCameras():
    
    @classmethod
    def build(cls, nd):
        return cls()

    def dictify(self):
        obj = {}
        return obj

#-------------------------------------------------------------------------------

class LibraryGeometries():
    
    @classmethod
    def build(cls, nd):
        return cls()

    def dictify(self):
        obj = {}
        return obj

#-------------------------------------------------------------------------------

class LibraryEffects():
    
    @classmethod
    def build(cls, nd):
        return cls()

    def dictify(self):
        obj = {}
        return obj

#-------------------------------------------------------------------------------

class LibraryLights():
    
    @classmethod
    def build(cls, nd):
        return cls()
        
    def dictify(self):
        obj = {}
        return obj

#-------------------------------------------------------------------------------

class LibraryMaterials():
    
    @classmethod
    def build(cls, nd):
        return cls()

    def dictify(self):
        obj = {}
        return obj

#-------------------------------------------------------------------------------

class LibraryVisualScenes():
    
    @classmethod
    def build(cls, nd):
        return cls()

    def dictify(self):
        obj = {}
        return obj

#-------------------------------------------------------------------------------

class Scene():
    pass

#-------------------------------------------------------------------------------

class Extra():
    pass

#-------------------------------------------------------------------------------

class COLLADA():
    def __init__(self, version=None, asset=None, library_cameras=None,
                 library_lights=None, library_effects=None, library_materials=None,
                 library_geometries=None, library_visual_scenes=None):
        self.version = version
        self.asset = asset
        self.library_cameras = library_cameras
        self.library_lights = library_lights
        self.library_effects = library_effects
        self.library_materials = library_materials
        self.library_geometries = library_geometries
        self.library_visual_scenes = library_visual_scenes
    
    @classmethod
    def build(cls, nd):
        """Parse a COLLADA element.

        The COLLADA element is a toplevel element in the collada schema. It has a
        local, anonymous complexType, which is a sequence.

        <xs:element name="COLLADA">
            <xs:complexType>
                <xs:sequence>
                    <xs:element ref="asset">
                    <xs:choice minOccurs="0" maxOccurs="unbounded">
                    <xs:element name="scene" minOccurs="0">
                    <xs:element ref="extra" minOccurs="0" maxOccurs="unbounded">

        """
        # Attributes
        version = nd.attrib['version']

        # Get self's sub-elements
        k = next((k for k in nd if tag(k) == 'asset'), None)
        asset = Asset.build(k) if k is not None else None

        # The "library_cameras" element appears inside an <xs:choice> with
        # maxOccurs unbounded, so the schema will accept any number of
        # "library_cameras" elements.
        nodes = [k for k in nd if tag(k) == 'library_cameras']
        library_cameras = [LibraryCameras.build(k) for k in nodes]

        # There are many more options inside this <choice> element, we've
        # implemented only a handful.
        
        nodes = [k for k in nd if tag(k) == 'library_lights']
        library_lights = [LibraryLights.build(k) for k in nodes]
        nodes = [k for k in nd if tag(k) == 'library_effects']
        library_effects = [LibraryEffects.build(k) for k in nodes]
        nodes = [k for k in nd if tag(k) == 'library_materials']
        library_materials = [LibraryMaterials.build(k) for k in nodes]
        nodes = [k for k in nd if tag(k) == 'library_geometries']
        library_geometries = [LibraryGeometries.build(k) for k in nodes]
        nodes = [k for k in nd if tag(k) == 'library_visual_scenes']
        library_visual_scenes = [LibraryVisualScenes.build(k) for k in nodes]

        return cls(version=version, asset=asset,
                   library_cameras=library_cameras,
                   library_lights=library_lights,
                   library_effects=library_effects,
                   library_materials=library_materials,
                   library_geometries=library_geometries,
                   library_visual_scenes=library_visual_scenes)

    def dictify(self):
        obj = {}
        if self.version is not None:
            obj['version'] = self.version
        if self.asset is not None:
            obj['asset'] = self.asset.dictify()
        if len(self.library_cameras) > 0:
            obj['library_cameras'] = [x.dictify() for x in self.library_cameras]
        if len(self.library_lights) > 0:
            obj['library_lights'] = [x.dictify() for x in self.library_lights]
        if len(self.library_effects) > 0:
            obj['library_effects'] = [x.dictify() for x in self.library_effects]
        if len(self.library_materials) > 0:
            obj['library_materials'] = [x.dictify() \
                                        for x in self.library_materials]
        if len(self.library_geometries) > 0:
            obj['library_geometries'] = [x.dictify() \
                                         for x in self.library_geometries]
        if len(self.library_visual_scenes) > 0:
            obj['library_visual_scenes'] = [x.dictify() \
                                            for x in self.library_visual_scenes]
        return obj

#-------------------------------------------------------------------------------

def parse_instance(filepath):
    # Ignore comments
    p = et.XMLParser(remove_comments=True)
    root = objectify.parse(filepath, parser=p).getroot()

    c = COLLADA.build(root)
    print(json.dumps(c.dictify(), indent=4))

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # Command line argument
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <xml filepath>')
        exit(-1)
    filepath = sys.argv[1]

    parse_instance(filepath)
