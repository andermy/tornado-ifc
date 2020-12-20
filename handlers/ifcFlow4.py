import ifcopenshell

import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, point
from scipy.spatial.transform import Rotation as R

class IfcFile:
    def __init__(self, path, version=None):
        self.version = None
        self.url = path
        self.ifc = ifcopenshell.open(path)
        self.version = version
        self.projects = []
        self.sites = []
        self.buildings = []
        self.storeys = []
        self.spaces = []
        self.products = []
        self.materials = []
        self.systems = []
        self.pset = []
        self.groups = []
        self.productTypes = []
        self.shapes = []
        print("Adding elements")
        self.add_ifc_data()
        print("Adding geometry")
        self.add_ifc_shapes()
        print("Adding relations")
        self.add_relations()

    def define_version(self, version):
        self.version = version

    def add_ifc_data(self):
        self.iterate_ifc_elements(self.ifc.by_type("IfcProject"), "IfcProject")
        self.iterate_ifc_elements(self.ifc.by_type("IfcSite"), "IfcSite")
        self.iterate_ifc_elements(self.ifc.by_type("IfcBuilding"), "IfcBuilding")
        self.iterate_ifc_elements(self.ifc.by_type("IfcBuildingStorey"), "IfcBuildingStorey")
        self.iterate_ifc_elements(self.ifc.by_type("IfcSpace"), "IfcSpace")
        self.iterate_ifc_elements(self.ifc.by_type("IfcProduct"), "IfcProduct")
        self.iterate_ifc_elements(self.ifc.by_type("IfcMaterial"), "IfcMaterial")
        self.iterate_ifc_elements(self.ifc.by_type("IfcSystem"), "IfcSystem")
        self.iterate_ifc_elements(self.ifc.by_type("IfcGroup"), "IfcGroup")

    # Iterates and creates geometry/ shapes for each storey, space and product (IfcBuildingStorey, IfcSpace and IfcProduct)
    def add_ifc_shapes(self):
        elements = self.storeys + self.spaces + self.products
        for e in elements:
            ifc_element = self.ifc.by_id(e.id)
            if ifc_element is not None:
                if ifc_element.Representation is not None:
                    try:
                        shape_element = self.add_element(ifc_element.Representation.Representations[0], "IfcShapeRepresentation", ifc_element.ObjectPlacement.RelativePlacement)
                        e.add_shape(shape_element)
                    except:
                        print("Print missing shape: " + str(e.id))
                        #pass
    
    # Creates an element from an ifcElement and updates IfcFile object subelements.
    def add_element(self, ifcElement, ifcType, objectplacement=None):
        try:
            element = None
            if self.get_object_by_id(ifcElement.id()) is None:
                if ifcType == "IfcProject":
                    element = IfcProject(ifcElement)
                    self.projects.append(element)
                elif ifcType == "IfcSite":
                    element = IfcSite(ifcElement)
                    self.sites.append(element)
                elif ifcType == "IfcBuilding":
                    element = IfcBuilding(ifcElement)
                    self.buildings.append(element)
                elif ifcType == "IfcBuildingStorey":
                    element = IfcStorey(ifcElement)
                    self.storeys.append(element)
                elif ifcType == "IfcSpace":
                    element = IfcSpace(ifcElement)
                    self.spaces.append(element)
                elif ifcType == "IfcProduct":
                    element = IfcProduct(ifcElement)
                    self.products.append(element)
                elif ifcType == "IfcMaterial":
                    element = IfcMaterial(ifcElement)
                    self.materials.append(element)
                elif ifcType == "IfcSystem":
                    element = IfcSystem(ifcElement)
                    self.systems.append(element)
                elif ifcType == "IfcGroup":
                    element = IfcGroup(ifcElement)
                    self.groups.append(element)
                elif ifcType == "IfcPropertySingleValue":
                    element = IfcSingleProperty(ifcElement)
                    self.pset.append(element)
                elif ifcType == "IfcProductType":
                    element = IfcProductType(ifcElement)
                    self.productTypes.append(element)
                elif ifcType == "IfcShapeRepresentation":
                    element = IfcShapeRepresentation(objectplacement, ifcElement)
                    self.shapes.append(element)
        except:
            print(ifcElement)
        return element
    # Takes an array of elements and forwards each object to add_object from ifcopenshell.by_type query
    def iterate_ifc_elements(self, ifcElements, ifcType):
        
        for s in ifcElements:
            self.add_element(s, ifcType)
    
    def get_elements_dict(self):
        e_dict = {}
        elements = []
        for project in self.projects:
            elements.append(project.to_dict())
        e_dict['projects'] = elements
        elements = []
        for site in self.sites:
            elements.append(site.to_dict())
        e_dict['sites'] = elements
        elements = []
        for building in self.buildings:
            elements.append(building.to_dict())
        e_dict['buildings'] = elements
        elements = []
        for storey in self.storeys:
            elements.append(storey.to_dict())
        e_dict['storeys'] = elements
        elements = []
        for product in self.products:
            elements.append(product.to_dict())
        e_dict['products'] = elements
        elements = []
        for space in self.spaces:
            elements.append(space.to_dict())
        e_dict['spaces'] = elements
        for material in self.materials:
            elements.append(material.to_dict())
        e_dict['material'] = elements
        for productType in self.productTypes:
            elements.append(productType.to_dict())
        e_dict['productTypes'] = elements
        for pset in self.pset:
            elements.append(pset.to_dict())
        e_dict['pset'] = elements
        for shape in self.shapes:
            elements.append(shape.to_dict())
        e_dict['shapes'] = elements
        return e_dict

    
    # Identifies object by ifc id() and returns relevant object from all subclasses of IfcFile.
    def get_object_by_id(self, prop):
        l = []

        elements = self.projects + self.sites + self.buildings + self.storeys + self.spaces + self.products + self.materials + self.systems + self.groups + self.productTypes
        for x in elements:
            if x.id == prop:
                l.append(x)
        if len(l) == 1:
            return l[0]
        elif len(l) == 0:
            return None
        else:
            return l
    # Subfunction for mapping relative objects. Called by mainobject at init.
    def add_relations(self):
        print("Adding Pset")
        for rel_element in self.ifc.by_type("IfcRelDefinesByProperties"):
            for ifcelement in rel_element.RelatedObjects:
                try:
                    element = self.get_object_by_id(ifcelement.id())
                    if element is None:
                        element = self.add_element(ifcelement, "IfcGroup")
                    for ifc_pset in rel_element.RelatingPropertyDefinition.HasProperties:
                        pset = self.get_object_by_id(ifc_pset.id())
                        if pset is None:
                            pset = self.add_element(ifc_pset, "IfcPropertySingleValue")
                            #pset = IfcSingleProperty(ifc_pset)
                        element.add_pset(pset)
                except:
                    #print(rel_element)
                    print(ifc_pset)
        print("Adding materials")
        for rel_element in self.ifc.by_type("IfcRelAssociatesMaterial"):
            material = self.get_object_by_id(rel_element.RelatingMaterial.id())
            for ifcelement in rel_element.RelatedObjects:
                try:
                    element = self.get_object_by_id(ifcelement.id())
                    if element is None:
                        element = self.add_element(ifcelement, "IfcProductType")
                    element.add_material(material)
                except:
                    print(ifcelement)
        print("Adding groups and systems")
        for rel_element in self.ifc.by_type("IfcRelAssignsToGroup"):
            group = self.get_object_by_id(rel_element.id())
            if group is None:
                group = self.add_element(rel_element, "IfcGroup")
            for ifcelement in rel_element.RelatedObjects:
                try:
                    element = self.get_object_by_id(ifcelement.id())
                    element.add_group(group)
                    if rel_element[6] is not None:
                        try:
                            system = self.get_object_by_id(rel_element[6].id())
                            if system.ptype == "IfcSystem":
                                element.add_system(system)
                        except:
                            print(rel_element[6])
                except:
                    print(ifcelement)
        print("Adding space, storey and building relations")
        for rel_element in self.ifc.by_type("IfcRelContainedInSpatialStructure"):
            relatedStructure = self.get_object_by_id(rel_element.RelatingStructure.id())
            for ifcelement in rel_element.RelatedElements:
                try:
                    element = self.get_object_by_id(ifcelement.id())
                    if rel_element.RelatingStructure.is_a() == "IfcBuilding":
                        element.add_building(relatedStructure)
                    if rel_element.RelatingStructure.is_a() == "IfcBuildingStorey":
                        element.add_storey(relatedStructure)
                    if rel_element.RelatingStructure.is_a() == "IfcSpace":
                        element.add_space(relatedStructure)
                except:
                    print(ifcelement)
        print("adding building, site and space relations")
        for rel_element in self.ifc.by_type("IfcRelAggregates"):
            for ifcelement in rel_element.RelatedObjects:
                try:
                    element = self.get_object_by_id(ifcelement.id())
                    if element is None:
                        element = self.add_element(ifcelement, ifcelement.is_a())
                    rel_ifc_object = rel_element.RelatingObject
                    rel_object = self.get_object_by_id(rel_ifc_object.id())
                    if rel_object is None:
                        rel_object = self.add_element(rel_ifc_object, ifcelement.is_a())
                    if ifcelement.is_a() == "IfcSite":
                        element.add_project(rel_object)
                    elif ifcelement.is_a() == "IfcBuilding":
                        element.add_site(rel_object)
                    elif ifcelement.is_a() == "IfcBuildingStorey":
                        element.add_building(rel_object)
                    elif ifcelement.is_a() == "IfcSpace":
                        element.add_storey(rel_object)
                except:
                    print(rel_ifc_object)
        print("Adding product types")
        for rel_element in self.ifc.by_type("IfcRelDefinesByType"):
            for ifcelement in rel_element.RelatedObjects:
                try:
                    element = self.get_object_by_id(ifcelement.id())
                    if element is None:
                        element = self.add_element(ifcelement, "IfcProduct")
                    rel_ifc_object = rel_element.RelatingType
                    rel_object = self.get_object_by_id(rel_ifc_object.id())
                    if rel_object is None:
                        rel_object = self.add_element(rel_ifc_object, "IfcProductType")
                    if ifcelement.is_a() == "IfcProduct":
                        element.add_product_type(rel_object)
                except:
                    print(rel_ifc_object)

    # Several subfunctions for mapping pandas dataframes from relative objects.
    def get_pandas_df_storeys(self):
        df = []
        for storey in self.storeys:
            df.append([storey.building.site.name, storey.building.name, storey.name, storey.longName, storey.z])
        
        columns = ['Site', 'Building', 'Storey name', 'Storey Longname', 'Storey elevation']

        return pd.DataFrame(df, columns=columns)

    def get_pandas_df_spaces(self):
        df = []
        for space in self.spaces:
            df.append([space.storey.name, space.storey.z, space.name, space.longName, space.z])
        
        columns = ['Storey', 'storey elevation', 'Space', 'Space longname', 'Space elevation']

        return pd.DataFrame(df, columns=columns)
    
    def get_pandas_df_products(self):
        df = []
        for product in self.products:
            if product.space is not None:
                if product.storey is not None:
                   df.append([product.storey.name, product.space.name, product.name, product.z])
        
        columns = ['Storey', 'Space', 'Product', 'Product elevation']

        return pd.DataFrame(df, columns=columns)
    
    def get_pandas_df_systems(self):
        df = []
        for product in self.products:
            if product.system is not None:
                df.append([product.system.name, product.name])
        
        columns = ['System', 'Product']

        return pd.DataFrame(df, columns=columns)

    def get_pandas_df_product_pset(self, ptype):
        df = []
        if ptype == "IfcProduct":
            elements = self.products
        elif ptype == "IfcBuildingStorey":
            elements = self.storeys
        elif ptype == "IfcSpace":
            elements = self.spaces
        elif ptype == "IfcBuilding":
            elements = self.buildings
        elif ptype == "IfcSite":
            elements = self.sites
        elif ptype == "IfcProject":
            elements = self.projects
        elif ptype == "IfcSystem":
            elements = self.systems
        elif ptype == "IfcMaterial":
            elements = self.materials
        elif ptype == "IfcGroup":
            elements = self.groups

        for product in elements:
            for prop in product.pset:
                df.append([product.name, prop.value_type, prop.value, prop.unit])
            
        columns = ['Element', 'Value type', 'Value', 'Unit']

        df = pd.DataFrame(df, columns=columns)
        strike_pivot = df.pivot_table(columns="Value type", values="Value", aggfunc=np.count_nonzero)
        strike_cols = strike_pivot.columns

        return df, strike_cols


class IfcProject(object):
    def __init__(self, element):
        self.id = element.id()
        self.guid = element.GlobalId
        self.ptype = element.is_a()
        self.name = element.Name
        self.longName = element.LongName
        self.description = element.Description
        self.phase = element.Phase
        self.lengthUnit = element.UnitsInContext.Units[0].Name
        self.lengthPrefix = element.UnitsInContext.Units[0].Prefix
        self.xDir = element.RepresentationContexts[0].TrueNorth.DirectionRatios[0]
        self.yDir = element.RepresentationContexts[0].TrueNorth.DirectionRatios[1]
        self.pset = []
    
    def add_pset(self, pset):
        self.pset.append(pset)

    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        p_dict['longName'] = self.longName
        p_dict['description'] = self.description
        p_dict['phase'] = self.phase
        p_dict['xDir'] = self.xDir
        p_dict['yDir'] = self.yDir
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset

        return p_dict
        

class IfcSite(object):
    def __init__(self, element):
        self.id = element.id()
        self.guid = element.GlobalId
        self.ptype = element.is_a()
        self.name = element.Name
        self.description = element.Description
        self.refLatitude = element.RefLatitude
        self.refLongitude = element.RefLongitude
        self.refElevation = element.RefElevation
        self.LandTitleNumber = element.LandTitleNumber
        self.SiteAddress = element.SiteAddress
        self.pset = []
        self.project = []
    
    def add_pset(self, pset):
        self.pset.append(pset)
    
    def add_project(self, project):
        self.project.append(project)
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        p_dict['description'] = self.description
        p_dict['refLatitude'] = self.refLatitude
        p_dict['refLongitude'] = self.refLongitude
        p_dict['refElevation'] = self.refElevation
        p_dict['LandTitleNumber'] = self.LandTitleNumber
        p_dict['SiteAddress'] = self.SiteAddress
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset
        projects = []
        for p in self.project:
            projects.append(p.id)
        p_dict['project'] = projects
        return p_dict

class IfcBuilding(object):
    def __init__(self, element):
        self.id = element.id()
        self.guid = element.GlobalId
        self.ptype = element.is_a()
        self.name = element.Name
        self.description = element.Description
        self.longName = element.LongName
        self.x = element.ObjectPlacement.RelativePlacement.Location.Coordinates[0]
        self.y = element.ObjectPlacement.RelativePlacement.Location.Coordinates[1]
        self.z = element.ObjectPlacement.RelativePlacement.Location.Coordinates[2]
        self.site = []
        self.pset = []
        self.shape = []
    
    def add_pset(self, pset):
        self.pset.append(pset)

    def add_site(self, site):
        self.site.append(site)
    
    def add_shape(self, shape):
        self.shape.append(shape)

    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        p_dict['description'] = self.description
        p_dict['longName'] = self.longName
        p_dict['x'] = self.x
        p_dict['y'] = self.y
        p_dict['z'] = self.z
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset
        site = []
        for p in self.site:
            site.append(p.id)
        p_dict['site'] = site
        shape = []
        for p in self.shape:
            shape.append(p.id)
        p_dict['shape'] = shape

        return p_dict

class IfcStorey:
    def __init__(self, element):
        self.id = element.id()
        self.guid = element.GlobalId
        self.ptype = element.is_a()
        self.name = element.Name
        self.description = element.Description
        self.longName = element.LongName
        self.x = element.ObjectPlacement.RelativePlacement.Location.Coordinates[0]
        self.y = element.ObjectPlacement.RelativePlacement.Location.Coordinates[1]
        self.z = element.ObjectPlacement.RelativePlacement.Location.Coordinates[2]
        self.building = []
        self.pset = []
        self.shape = []
    
    def add_pset(self, pset):
        self.pset.append(pset)
    
    def add_building(self, building):
        self.building.append(building)
    
    def add_shape(self, shape):
        self.shape.append(shape)
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        p_dict['description'] = self.description
        p_dict['longName'] = self.longName
        p_dict['x'] = self.x
        p_dict['y'] = self.y
        p_dict['z'] = self.z
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset
        building = []
        for p in self.building:
            building.append(p.id)
        p_dict['building'] = building
        shape = []
        for p in self.shape:
            shape.append(p.id)
        p_dict['shape'] = shape

        return p_dict

class IfcSpace:
    def __init__(self, element):
        self.id = element.id()
        self.guid = element.GlobalId
        self.ptype = element.is_a()
        self.name = element.Name
        self.description = element.Description
        self.longName = element.LongName
        self.x = element.ObjectPlacement.RelativePlacement.Location.Coordinates[0]
        self.y = element.ObjectPlacement.RelativePlacement.Location.Coordinates[1]
        self.z = element.ObjectPlacement.RelativePlacement.Location.Coordinates[2]
        self.pset = []
        self.group = []
        self.building = []
        self.storey = []
        self.shape = []
    
    def add_pset(self, pset):
        self.pset.append(pset)

    def add_group(self, group):
        self.group.append(group)
    
    def add_building(self, building):
        self.building.append(building)
    
    def add_storey(self, storey):
        self.storey.append(storey)
    
    def add_shape(self, shape):
        self.shape.append(shape)
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        p_dict['description'] = self.description
        p_dict['longName'] = self.longName
        p_dict['x'] = self.x
        p_dict['y'] = self.y
        p_dict['z'] = self.z
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset
        group = []
        for g in self.group:
            group.append(g.id)
        p_dict['group'] = group
        building = []
        for p in self.building:
            building.append(p.id)
        p_dict['building'] = building
        storey = []
        for p in self.storey:
            storey.append(p.id)
        p_dict['storey'] = storey
        shape = []
        for p in self.shape:
            shape.append(p.id)
        p_dict['shape'] = shape

        return p_dict

class IfcProduct:
    def __init__(self, element):
        self.id = element.id()
        self.guid = element.GlobalId
        self.ptype = element.is_a()
        self.name = element.Name
        self.description = element.Description
        self.x = element.ObjectPlacement.RelativePlacement.Location.Coordinates[0]
        self.y = element.ObjectPlacement.RelativePlacement.Location.Coordinates[1]
        self.z = element.ObjectPlacement.RelativePlacement.Location.Coordinates[2]
        self.pset = []
        self.group = []
        self.material = []
        self.building = []
        self.storey = []
        self.shape = []
        self.space = []
        self.system = []
        self.producType = []
    
    def add_pset(self, pset):
        self.pset.append(pset)
    
    def add_material(self, material):
        self.material.append(material)
    
    def add_building(self, building):
        self.building.append(building)
    
    def add_storey(self, storey):
        self.storey.append(storey)
    
    def add_group(self, group):
        self.group.append(group)
    
    def add_space(self, space):
        self.space.append(space)
    
    def add_shape(self, shape):
        self.shape.append(shape)
    
    def add_system(self, system):
        self.system.append(system)

    def add_product_type(self, productType):
        self.producType.append(productType)
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        p_dict['description'] = self.description
        p_dict['x'] = self.x
        p_dict['y'] = self.y
        p_dict['z'] = self.z
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset
        group = []
        for g in self.group:
            group.append(g.id)
        p_dict['group'] = group
        building = []
        for p in self.building:
            building.append(p.id)
        p_dict['building'] = building
        storey = []
        for p in self.storey:
            storey.append(p.id)
        p_dict['storey'] = storey
        shape = []
        for p in self.shape:
            shape.append(p.id)
        p_dict['shape'] = shape
        space = []
        for p in self.space:
            space.append(p.id)
        p_dict['space'] = space
        material = []
        for p in self.material:
            material.append(p.id)
        p_dict['material'] = material
        system = []
        for p in self.system:
            system.append(p.id)
        p_dict['system'] = system
        productType = []
        for p in self.producType:
            productType.append(p.id)
        p_dict['productType'] = productType

        return p_dict

class IfcMaterial:
    def __init__(self, element):
        self.id = element.id()
        self.ptype = element.is_a()
        self.name = element.Name
        self.pset = []
    
    def add_pset(self, pset):
        self.pset.append(pset)
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset

        return p_dict

class IfcSystem:
    def __init__(self, element):
        self.id = element.id()
        self.guid = element.GlobalId
        self.ptype = element.is_a()
        self.name = element.Name
        self.description = element.Description
        self.pset = []
    
    def add_pset(self, pset):
        self.pset.append(pset)
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        p_dict['description'] = self.description
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset

class IfcSingleProperty:
    def __init__(self, element):
        self.id = element.id()
        self.ptype = element.is_a()
        if element.NominalValue is not None:
            self.value_type = element.NominalValue.is_a()
            self.value = element.NominalValue[0]
        else:
            self.value_type = None
            self.value = None
        
        if element.Unit is not None:
            self.unit = element.Unit
        else: self.unit = None
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['ptype'] = self.ptype
        p_dict['value_type'] = self.value_type
        p_dict['value'] = self.value
        p_dict['unit'] = self.unit

        return p_dict

class IfcGroup:
    def __init__(self, element):
        self.id = element.id()
        self.ptype = element.is_a()
        self.name = element.Name
        self.pset = []
    
    def add_pset(self, pset):
        self.pset.append(pset)
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset

        return p_dict

class IfcProductType:
    def __init__(self, element):
        self.id = element.id()
        self.guid = element.GlobalId
        self.ptype = element.is_a()
        self.name = element.Name
        self.predefined = element.PredefinedType
        try:
            self.tag = element.tag
        except:
            self.tag = None
        self.pset = []
        self.material = []
        self.shape = []
    
    def add_pset(self, pset):
        self.pset.append(pset)
    
    def add_material(self, material):
        self.material.append(material)
    
    def add_shape(self, shape):
        self.shape.append(shape)
    
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['guid'] = self.guid
        p_dict['ptype'] = self.ptype
        p_dict['name'] = self.name
        p_dict['predefinedType'] = self.predefined
        p_dict['tag'] = self.tag
        pset = []
        for p in self.pset:
            pset.append(p.id)
        p_dict['pset'] = pset
        shape = []
        for p in self.shape:
            shape.append(p.id)
        p_dict['shape'] = shape
        material = []
        for p in self.material:
            material.append(p.id)
        p_dict['material'] = material

        return p_dict
        

# Shape representation handling
class IfcShapeRepresentation:
    def __init__(self, objectplacement, element):
        self.id = element.id()
        self.identifier = element.RepresentationIdentifier
        self.RepresentationType = element.RepresentationType
        self.position = None
        self.zAxis = None
        self.xyAxis = None
        self.shape = None
        try:
            self.position = objectplacement.Location.Coordinates
            self.zAxis = objectplacement.Axis.DirectionRatios
            if self.zAxis[0] != 0:
                if self.zAxis[1] != 0:
                    print("not only z")
                    print(self.zAxis)
                    print(self.xyAxis)
            self.xyAxis = objectplacement.RefDirection.DirectionRatios
            if element.RepresentationType == "Brep":
                self.shape = IfcFacedBrep(element.Items[0])
            elif element.RepresentationType == "MappedRepresentation":
                self.shape = IfcMappedItem(element.Items[0])
            elif element.RepresentationType == "SurfaceModel":
                self.shape = IfcFaceBasedSurfaceModel(element.Items)
            elif element.RepresentationType == "SweptSolid":
                self.shape = IfcExtrudedAreaSolid(element.Items[0])
                #print(len(element.Items))
            elif element.RepresentationType == "GeometricCurveSet":
                self.shape = IfcGeometricCurveSet(element.Items)
            elif element.RepresentationType == "CSG":
                self.shape = None
                print("CSG")
            elif element.RepresentationType == "Clipping":
                self.shape = None
                print("Clipping")
            else:
                print(element.id())
                print(element.RepresentationType)
                print("df")
        except:
            print(element.id())
    def to_dict(self):
        p_dict = {}
        p_dict['id'] = self.id
        p_dict['identifier'] = self.identifier
        p_dict['RepresentationType'] = self.RepresentationType

        return p_dict
    
    def get_points(self):
        if self.RepresentationType == "GeometricCurveSet":
            return self.shape.footprint()
        else:
            shape_corners = self.shape.get_points()
            corners = []
            for point in shape_corners:
                x = point[0] * (self.xyAxis[0] - self.xyAxis[1]) + self.position[0]   
                y = point[1] * (self.xyAxis[1] + self.xyAxis[0]) + self.position[1]
                z = point[2] * self.zAxis + self.position[2]
                corners.append([x,y,z])
            return corners

    def footprint(self):

        corners = []
        pts = np.array(self.get_points())
        pts = pts[:,:2]
        polygon = Polygon(pts)
        for c in list(polygon.exterior.coords):
            corners.append(c)
        return corners

class IfcMappedItem:
    def __init__(self, element):
        self.id = element.id()
        self.identifier = element.MappingSource.MappedRepresentation.RepresentationIdentifier
        self.RepresentationType = element.MappingSource.MappedRepresentation.RepresentationType
        self.mappingTransformation = IfcCartesianTransformationOperator(element.MappingTarget)
        self.shape = None
        if element.MappingSource.MappedRepresentation.RepresentationType == "Brep":
            self.shape = IfcFacedBrep(element.MappingSource.MappedRepresentation.Items[0])
        elif element.MappingSource.MappedRepresentation.RepresentationType == "SurfaceModel":
            self.shape = IfcFaceBasedSurfaceModel(element.MappingSource.MappedRepresentation.Items)
        elif element.MappingSource.MappedRepresentation.RepresentationType == "SweptSolid":
            self.shape = IfcExtrudedAreaSolid(element.MappingSource.MappedRepresentation.Items[0])
            l = len(element.MappingSource.MappedRepresentation.Items)
            if l > 1:
                print(l)
        elif element.MappingSource.MappedRepresentation.RepresentationType == "GeometricCurveSet":
            self.shape = IfcGeometricCurveSet(element.MappingSource.MappedRepresentation.Items)
        elif element.MappingSource.MappedRepresentation.RepresentationType == "CSG":
            self.shape = None
            print("CSG")
        elif element.MappingSource.MappedRepresentation.RepresentationType == "Clipping":
            self.shape = None
            print("Clipping")
        else:
            print("Mapped item: ")
            print(element.id())
            print(element.RepresentationType)
        
    def get_points(self):
        return self.shape.get_points()
            
# Types of shape
class IfcExtrudedAreaSolid:
    def __init__(self, element):
        self.x = element.Position.Location.Coordinates[0]
        self.y = element.Position.Location.Coordinates[1]
        self.z = element.Position.Location.Coordinates[2]
        self.dirX = element.ExtrudedDirection.DirectionRatios[0]
        self.dirY = element.ExtrudedDirection.DirectionRatios[1]
        self.dirZ = element.ExtrudedDirection.DirectionRatios[2]
        print([self.dirX, self.dirY, self.dirZ])
        self.depth = element.Depth
        try:
            if element.SweptArea.is_a() == "IfcCircleProfileDef":
                self.sweptArea = IfcCircleProfileDef(element.SweptArea)
            elif element.SweptArea.is_a() == "IfcSweptAreaSolid":
                self.sweptArea = IfcSweptAreaSolid(element.SweptArea)
            elif element.SweptArea.is_a() == "IfcRectangleProfileDef":
                self.sweptArea = IfcSweptAreaSolid(element.SweptArea)
            elif element.SweptArea.is_a() == "IfcArbitraryClosedProfileDef":
                self.sweptArea = IfcArbitraryClosedProfileDef(element.SweptArea)
            elif element.SweptArea.is_a() == "IfcArbitraryProfileDefWithVoids":
                self.sweptArea = IfcArbitraryClosedProfileDef(element.SweptArea)
            elif element.SweptArea.is_a() == "IfcRectangleHollowProfileDef":
                self.sweptArea = IfcSweptAreaSolid(element.SweptArea)
            elif element.SweptArea.is_a() == "IfcCircleHollowProfileDef":
                self.sweptArea = IfcCircleProfileDef(element.SweptArea)
            else:
                print(element.SweptArea)
        except:
            print(element)
        
    def get_points(self):
        center, area = self.sweptArea.footprint()
        corners = []
        for point in area:
            corr = [self.x-center.x, self.y-center.y, self.z-center.z]
            corners.append([point[0]+corr[0], point[1]+corr[1], corr[2]])
            corners.append([point[0]+corr[0], point[1]+corr[1], corr[2]+self.depth])
        
        return corners



class IfcFacedBrep:
    def __init__(self, element):
        self.brep = self.add_curve_array(element.Outer[0])
    
    def add_curve_array(self, faces):
        curve = []
        for face in faces:
            for bound in face.Bounds:
                for point in bound.Bound.Polygon:
                    curve.append([point.Coordinates[0], point.Coordinates[1], point.Coordinates[2]])
        return curve
    
    def get_points(self):
        
        return self.brep

class IfcFaceBasedSurfaceModel:
    def __init__(self, elements):
        self.brep = self.add_curve_array(elements)
    
    def add_curve_array(self, items):
        curve = []
        for item in items:
            if item.is_a() == "IfcFacetedBrep":
                for face in item.Outer.CfsFaces:
                    for bound in face.Bounds:
                        for point in bound.Bound.Polygon:
                            curve.append([point.Coordinates[0], point.Coordinates[1], point.Coordinates[2]])
            elif item.is_a() == "IfcShellBasedSurfaceModel":
                for shell in item.SbsmBoundary:
                    for face in shell.CfsFaces:
                        for bound in face.Bounds:
                            for point in bound.Bound.Polygon:
                                curve.append([point.Coordinates[0], point.Coordinates[1], point.Coordinates[2]])
            else:
                for faceSet in item.FbsmFaces:
                    for face in faceSet.CfsFaces:
                        for bound in face.Bounds:
                            for point in bound.Bound.Polygon:
                                curve.append([point.Coordinates[0], point.Coordinates[1], point.Coordinates[2]])
        return curve
    
    def get_points(self):
        
        return self.brep

class IfcGeometricCurveSet:
    def __init__(self, elements):
        self.curve = self.add_curve(elements)
    
    def add_curve(self, items):
        curve = []
        for item in items:
            for polyline in item.Elements:
                for point in polyline.Points:
                    curve.append([point.Coordinates[0], point.Coordinates[1]])
        return curve
    
    def footprint(self):
        corners = []
        pts = np.array(self.brep)
        pts = pts[:,:2]
        polygon = Polygon(pts)
        for c in list(polygon.exterior.coords):
            corners.append(c)
        return corners


# shape classes
class IfcSweptAreaSolid:
    def __init__(self, element):
        self.id = element.id()
        self.x = element.Position.Location.Coordinates[0]
        self.y = element.Position.Location.Coordinates[1]
        self.xDim = element.XDim
        self.yDim = element.YDim
        try:
            self.wallThickness = element.WallThickness
        except:
            self.wallThickness = None
        try:
            self.outerFilletRadius = element.OuterFilletRadius
        except:
            self.outerFilletRadius = None
        try:
            self.innerFilletRadius = element.InnerFilletRadius
        except:
            self.innerFilletRadius = None


    def footprint(self):
        return np.array([
            [self.x - self.xDim/2, self.y - self.yDim/2],
            [self.x + self.xDim/2, self.y - self.yDim/2],
            [self.x - self.xDim/2, self.y + self.yDim/2],
            [self.x + self.xDim/2, self.y + self.yDim/2],
        ])


class IfcCircleProfileDef:
    def __init__(self, element):
        self.id = element.id()
        self.x = element.Position.Location.Coordinates[0]
        self.y = element.Position.Location.Coordinates[1]
        self.radius = element.Radius
        self.trim1 = 0
        self.trim2 = np.pi * 2
        try:
            self.thickness = element.WallThickness
        except:
            self.thickness = None
    
    def footprint(self):
        parts = 12
        points = []
        for angle in np.linspace(self.trim1, self.trim2, parts):
            points.append([self.x + np.cos(angle)*self.radius, self.y + np.sin(angle)*self.radius])

        return points
            

class IfcTrimmedCurve:
    def __init__(self, element):
        self.id = element.id()
        self.basisCurve = IfcCircleProfileDef(element.BasisCurve)
        self.trim1 = element.Trim1[0][0]
        self.trim2 = element.Trim2[0][0]
    
    def footprint(self):
        parts = 12
        points = []
        for angle in np.linspace(self.trim1, self.trim2, parts):
            points.append([self.basisCurve.x + np.cos(angle)*self.basisCurve.radius, self.basisCurve.y + np.sin(angle)*self.basisCurve.radius])

        return points

class IfcArbitraryClosedProfileDef:
    def __init__(self, element):
        self.outerCurve = self.add_outer_curve_array(element.OuterCurve)
        if element.is_a() == "IfcArbitraryProfileDefWithVoids":
            self.innerCurves = self.add_inner_curves_array(element.InnerCurves)
        else:
            self.innerCurves = []
    
    def add_inner_curves_array(self, inner_curves):
        curves = []
        if isinstance(inner_curves, tuple):
            for inner_curve in inner_curves:
                if inner_curve.is_a() == "IfcCompositeCurve":
                    if isinstance(inner_curve, tuple):
                        for curve in inner_curve:
                            for segment in curve.Segments:
                                for parent in segment.ParentCurve:
                                    if parent.is_a() == "IfcCircle":
                                        curves.append(IfcCircleProfileDef(parent))
                                    elif parent.is_a() == "IfcTrimmedCurve":
                                        curves.append(IfcTrimmedCurve(parent))
                                    else:
                                        print(parent)
                    elif isinstance(inner_curve, ifcopenshell.entity_instance):
                        for segment in inner_curve.Segments:
                            if isinstance(segment.ParentCurve, tuple):
                                for parent in segment.ParentCurve:
                                    if parent.is_a() == "IfcCircle":
                                        curves.append(IfcCircleProfileDef(parent))
                                    elif parent.is_a() == "IfcTrimmedCurve":
                                        curves.append(IfcTrimmedCurve(parent))
                                    else:
                                        print(parent)
                            elif segment.ParentCurve.is_a() == "IfcPolyline":
                                for point in segment.ParentCurve.Points:
                                    curves.append([point.Coordinates[0], point.Coordinates[1]])
                elif inner_curve.is_a() == "IfcPolyline":
                    for point in inner_curve.Points:
                        curves.append([point.Coordinates[0], point.Coordinates[1]])
        elif isinstance(inner_curves, ifcopenshell.entity_instance):
            if inner_curves.is_a() == "IfcCompositeCurve":
                if isinstance(inner_curves, tuple):
                    for curve in inner_curves:
                        for segment in curve.Segments:
                            for parent in segment.ParentCurve:
                                if parent.is_a() == "IfcCircle":
                                    curves.append(IfcCircleProfileDef(parent))
                                elif parent.is_a() == "IfcTrimmedCurve":
                                    curves.append(IfcTrimmedCurve(parent))
                                else:
                                    print(parent)
                elif isinstance(inner_curve, ifcopenshell.entity_instance):
                    for segment in inner_curve.Segments:
                        if isinstance(segment.ParentCurve, tuple):
                            for parent in segment.ParentCurve:
                                if parent.is_a() == "IfcCircle":
                                    curves.append(IfcCircleProfileDef(parent))
                                elif parent.is_a() == "IfcTrimmedCurve":
                                    curves.append(IfcTrimmedCurve(parent))
                                else:
                                    print(parent)
                        elif segment.ParentCurve.is_a() == "IfcPolyline":
                            for point in segment.ParentCurve.Points:
                                curves.append([point.Coordinates[0], point.Coordinates[1]])
            elif inner_curve.is_a() == "IfcPolyline":
                for point in inner_curve.Points:
                    curves.append([point.Coordinates[0], point.Coordinates[1]])
        return curves

    def add_outer_curve_array(self, outer_curves):
        #print(inner_curves)
        curves = []
        try:
            if outer_curves.is_a() == "IfcCompositeCurve":
                if isinstance(outer_curves, tuple):
                    for curve in outer_curves:
                        for segment in curve.Segments:
                            for parent in segment.ParentCurve:
                                if parent.is_a() == "IfcCircle":
                                    curves.append(IfcCircleProfileDef(parent))
                                elif parent.is_a() == "IfcTrimmedCurve":
                                    curves.append(IfcTrimmedCurve(parent))
                                else:
                                    print(parent)
                elif isinstance(outer_curves, ifcopenshell.entity_instance):
                    for segment in outer_curves.Segments:
                        if isinstance(segment.ParentCurve, tuple):
                            for parent in segment.ParentCurve:
                                if parent.is_a() == "IfcCircle":
                                    curves.append(IfcCircleProfileDef(parent))
                                elif parent.is_a() == "IfcTrimmedCurve":
                                    curves.append(IfcTrimmedCurve(parent))
                                else:
                                    print(parent)
                        elif segment.ParentCurve.is_a() == "IfcPolyline":
                            for point in segment.ParentCurve.Points:
                                curves.append([point.Coordinates[0], point.Coordinates[1]])

            elif outer_curves.is_a() == "IfcPolyline":
                for point in outer_curves.Points:
                    curves.append([point.Coordinates[0], point.Coordinates[1]])
            return curves
        except:
            print(outer_curves)
            return None
    
    def footprint(self):
        return self.outerCurve

class IfcCartesianTransformationOperator:
    def __init__(self, element):
        self.id = element.id()
        self.x = element.LocalOrigin.Coordinates[0]
        self.y = element.LocalOrigin.Coordinates[1]
        self.z = element.LocalOrigin.Coordinates[2]
        self.scale = element.Scale
        self.axis1 = element.Axis1
        self.axis2 = element.Axis2
            
    

