from sys import version

from numpy.core.numeric import _ones_like_dispatcher
import ifcopenshell
import ifcopenshell.geom

import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, point, polygon
from scipy.spatial.transform import Rotation as R
from scipy.spatial import ConvexHull

from OCC.Core.gp import gp_Vec, gp_Pnt, gp_Dir, gp_Pln
#from OCC.Visualization import Tesselator
import OCCUtils.Common as Common
from OCC.Core.TopoDS import *
from OCC.Core.TopAbs import *
from OCC.Core.TopExp import *
from OCC.Core.TopLoc import *
from OCC.Core.TopoDS import *
from OCC.Core.BRep import BRep_Builder
from OCC.Core import BRep
from OCCUtils.Topology import Topo
import OCC.Core.GProp
import OCC.Core.BRepGProp
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Section
#import mongo as m
from bson.objectid import ObjectId
#from version_resolver import VersionResolver
import os

libPath = '../models'
import sys
if not libPath in sys.path: sys.path.append(libPath)
import models as m


class IfcFile:
    def __init__(self, file):
        self.versionid = file['version']
        self.url = file['path']
        self.ifc = ifcopenshell.open(file['path'])
        self.version = self.define_version(self.versionid)
        self.store = IfcStore(self.version, self.url)
        
        print("Adding elements")
        #self.add_ifc_data()
        print("Adding relations")
        #self.add_product_type_relations()
        #self.add_material_relations()
        #self.add_group_relations()
        #self.add_structure_relations()
        #self.add_building_relations()
        #self.add_pset_relations()
        print("Adding geometry")
        #self.add_ifc_shapes()

    def define_version(self, version):
        vs = m.VersionResolver(version)
        return vs.get_version_object(version)
        
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
        self.iterate_ifc_elements(self.ifc.by_type("IfcPropertySingleValue"), "IfcPropertySingleValue")
    
    # Takes an array of elements and forwards each object to add_object from ifcopenshell.by_type query
    def iterate_ifc_elements(self, ifcElements, ifcType):
        
        for s in ifcElements:
            self.store.add_element(s, ifcType)

    # Iterates and creates geometry/ shapes for each storey, space and product (IfcBuildingStorey, IfcSpace and IfcProduct)
    def add_ifc_shapes(self):
        elements = self.store.storeys + self.store.spaces + self.store.products + self.store.buildings
        for e in elements:
            ifc_element = self.ifc.by_id(e.pid)
            if ifc_element is not None:
                if ifc_element.Representation is not None:
                    try:
                        self.store.add_shape(e, ifc_element)
                    except:
                        print("Print missing shape: " + str(e.pid))
                        #pass
    
    # Subfunction for mapping relative objects. Called by mainobject at init.
    def add_product_type_relations(self):
        
        print("Adding product types")
        for rel_element in self.ifc.by_type("IfcRelDefinesByType"):
            for ifcelement in rel_element.RelatedObjects:
                element = self.store.get_object_by_id(ifcelement.id())
                if element is None:
                    element = self.store.add_element(ifcelement, "IfcProduct")
                rel_ifc_object = rel_element.RelatingType
                rel_object = self.store.get_object_by_id(rel_ifc_object.id())
                if rel_object is None:
                    rel_object = self.store.add_element(rel_ifc_object, "IfcProductType")
                if rel_object is None:
                    print(rel_ifc_object)
                else:
                    self.store.add_product_type_relation(element, rel_object)

    def add_material_relations(self):
        print("Adding materials")
        for rel_element in self.ifc.by_type("IfcRelAssociatesMaterial"):
                for ifcelement in rel_element.RelatedObjects:
                    try:
                        element = self.store.get_object_by_id(ifcelement.id())
                        if element is None:
                            element = self.store.add_element(ifcelement, "IfcProductType")
                        if rel_element.RelatingMaterial.is_a() == "IfcMaterialList":
                            for ifcmat in rel_element.RelatingMaterial[0]:
                                material = self.store.get_object_by_id(ifcmat.id())
                                if material is not None:
                                    self.store.add_material_relation(element, material)
                                else:
                                    print("No material")
                                    print(rel_element)
                        else:
                            material = self.store.get_object_by_id(rel_element.RelatingMaterial.id())
                            if material is not None:
                                self.store.add_material_relation(element, material)
                            else:
                                print("No material")
                                print(rel_element)
                    except:
                        print(ifcelement)
    def add_group_relations(self):
        print("Adding groups and systems")
        for rel_element in self.ifc.by_type("IfcRelAssignsToGroup"):
            # Could also be "IfcRelAssigns"
            group = self.store.get_object_by_id(rel_element.id())
            if group is None:
                group = self.store.add_element(rel_element, "IfcGroup")
            for ifcelement in rel_element.RelatedObjects:
                try:
                    element = self.store.get_object_by_id(ifcelement.id())
                    self.store.add_group_relation(element, group)
                    if rel_element[6] is not None:
                        try:
                            system = self.store.get_object_by_id(rel_element[6].id())
                            if system.ptype == "IfcSystem":
                                self.store.add_system_relation(element, system)
                        except:
                            print(rel_element[6])
                except:
                    print(ifcelement)
    def add_structure_relations(self):
        print("Adding space, storey and building relations")
        for rel_element in self.ifc.by_type("IfcRelContainedInSpatialStructure"):
            relatedStructure = self.store.get_object_by_id(rel_element.RelatingStructure.id())
            for ifcelement in rel_element.RelatedElements:
                try:
                    element = self.store.get_object_by_id(ifcelement.id())
                    if rel_element.RelatingStructure.is_a() == "IfcBuilding":
                        self.store.add_building_relation(element, relatedStructure)
                    if rel_element.RelatingStructure.is_a() == "IfcBuildingStorey":
                        self.store.add_storey_relation(element, relatedStructure)
                    if rel_element.RelatingStructure.is_a() == "IfcSpace":
                        self.store.add_space_relation(element, relatedStructure)
                except:
                    print(ifcelement)
                    print(rel_element)
    def add_building_relations(self):
        print("adding building, site and space relations")
        for rel_element in self.ifc.by_type("IfcRelAggregates"):
            for ifcelement in rel_element.RelatedObjects:
                try:
                    element = self.store.get_object_by_id(ifcelement.id())
                    if element is None:
                        element = self.store.add_element(ifcelement, ifcelement.is_a())
                    rel_ifc_object = rel_element.RelatingObject
                    rel_object = self.store.get_object_by_id(rel_ifc_object.id())
                    if rel_object is None:
                        rel_object = self.store.add_element(rel_ifc_object, ifcelement.is_a())
                    if ifcelement.is_a() == "IfcSite":
                        self.store.add_project_relation(element, rel_object)
                    elif ifcelement.is_a() == "IfcBuilding":
                        self.store.add_site_relation(element, rel_object)
                    elif ifcelement.is_a() == "IfcBuildingStorey":
                        self.store.add_building_relation(element, rel_object)
                    elif ifcelement.is_a() == "IfcSpace":
                        self.store.add_storey_relation(element, rel_object)
                except:
                    print(rel_element)
    def add_pset_relations(self):
        print("Adding Pset")
        for rel_element in self.ifc.by_type("IfcRelDefinesByProperties"):
            for ifcelement in rel_element.RelatedObjects:
                #try:
                element = self.store.get_object_by_id(ifcelement.id())
                if element is None:
                    element = self.store.add_element(ifcelement, "IfcGroup")
                for ifc_pset in rel_element.RelatingPropertyDefinition.HasProperties:
                    pset = self.store.get_object_by_id(ifc_pset.id())
                    if pset is None:
                        pset = self.store.add_element(ifc_pset, "IfcPropertySingleValue")
                        #pset = IfcSingleProperty(ifc_pset)
                    if pset is not None:
                        self.store.add_pset(element, pset)
                #except:
                    #print(rel_element)
                #    print(rel_element)

class IfcStore:
    def __init__(self, version, filepath=None):
        self.version = version
        self.verisonResolver = m.VersionResolver(versionObject=self.version)
        self.filepath = filepath
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
        self.update_from_db()
        # Creates an element from an ifcElement, and saving it in store and db.
    def update_from_db(self):
        self.projects = list(m.IfcProject.objects.raw({'version':self.version.pk}))
        self.sites = list(m.IfcSite.objects.raw({'version':self.version.pk}))
        self.buildings = list(m.IfcBuilding.objects.raw({'version':self.version.pk}))
        self.storeys = list(m.IfcStorey.objects.raw({'version':self.version.pk}))
        self.spaces = list(m.IfcSpace.objects.raw({'version':self.version.pk}))
        self.products = list(m.IfcProduct.objects.raw({'version':self.version.pk}))
        self.materials = list(m.IfcMaterial.objects.raw({'version':self.version.pk}))
        self.systems = list(m.IfcSystem.objects.raw({'version':self.version.pk}))
        self.pset = list(m.IfcSingleProperty.objects.raw({'version':self.version.pk}))
        self.groups = list(m.IfcGroup.objects.raw({'version':self.version.pk}))
        self.productTypes = list(m.IfcProductType.objects.raw({'version':self.version.pk}))
        if self.filepath is None:
            self.filepath = self.products[0].filepath

    def validate_and_update(self):
        print("Adding elements from previous versions")
        self.update_prev_version_site()
        self.update_prev_version_storeys()
        self.update_prev_version_spaces()
        self.update_prev_version_products()
        print("Adding top to storeys")
        self.set_storey_top()
        print("Updating storey and space realtions")
        self.update_product_space_storey_relation()
        self.update_product_space_relation()
        
    def add_element(self, ifcElement, ifcType):
        try:
            element = None
            if self.get_object_by_id(ifcElement.id()) is None:
                if ifcType == "IfcProject":
                    element = m.IfcProject(pid=ifcElement.id(), guid = ifcElement.GlobalId, ptype = ifcElement.is_a(), name = ifcElement.Name, longName = ifcElement.LongName, phase = ifcElement.Phase, lengthUnit = ifcElement.UnitsInContext.Units[0].Name, lengthPrefix = ifcElement.UnitsInContext.Units[0].Prefix, dir=ifcElement.RepresentationContexts[0].TrueNorth.DirectionRatios).save()
                    element.version.append(self.version.pk)
                    if ifcElement.Description is not None:
                        element.description = ifcElement.Description
                    element.save()
                    self.projects.append(element)
                elif ifcType == "IfcSite":
                    element = m.IfcSite(pid = ifcElement.id(), guid = ifcElement.GlobalId, ptype = ifcElement.is_a(), name = ifcElement.Name, refLatitude = ifcElement.RefLatitude, refLongitude = ifcElement.RefLongitude, refElevation = ifcElement.RefElevation, LandTitleNumber = ifcElement.LandTitleNumber).save()
                    element.version.append(self.version.pk)
                    if ifcElement.Description is not None:
                        element.description = ifcElement.Description
                    element.save()
                    self.sites.append(element)
                elif ifcType == "IfcBuilding":
                    element = m.IfcBuilding(pid = ifcElement.id(), guid = ifcElement.GlobalId, ptype = ifcElement.is_a(), name = ifcElement.Name, longName = ifcElement.LongName).save()
                    element.version.append(self.version.pk)
                    if ifcElement.Description is not None:
                        element.description = ifcElement.Description
                    element.save()
                    self.buildings.append(element)
                elif ifcType == "IfcBuildingStorey":
                    element = m.IfcStorey(pid = ifcElement.id(), guid = ifcElement.GlobalId, ptype = ifcElement.is_a(), name = ifcElement.Name, longName = ifcElement.LongName).save()
                    element.version.append(self.version.pk)
                    element.bottom = ifcElement.ObjectPlacement.RelativePlacement.Location.Coordinates[2]
                    if ifcElement.Description is not None:
                        element.description = ifcElement.Description
                    element.save()
                    self.storeys.append(element)
                elif ifcType == "IfcSpace":
                    element = m.IfcSpace(pid = ifcElement.id(), guid = ifcElement.GlobalId, ptype = ifcElement.is_a(), name = ifcElement.Name, longName = ifcElement.LongName).save()
                    element.version.append(self.version.pk)
                    if ifcElement.Description is not None:
                        element.description = ifcElement.Description
                    element.save()
                    self.spaces.append(element)
                elif ifcType == "IfcProduct":
                    element = m.IfcProduct(pid = ifcElement.id(), guid = ifcElement.GlobalId, ptype = ifcElement.is_a(), name = ifcElement.Name, filepath=self.filepath).save()
                    element.version.append(self.version.pk)
                    if ifcElement.Description is not None:
                        element.description = ifcElement.Description
                        element.save()
                    self.products.append(element)
                elif ifcType == "IfcMaterial":
                    element = m.IfcMaterial(pid = ifcElement.id(), ptype = ifcElement.is_a(), name = ifcElement.Name).save()
                    element.version.append(self.version.pk)
                    element.save()
                    self.materials.append(element)
                elif ifcType == "IfcSystem":
                    element = m.IfcSystem(pid = ifcElement.id(), guid = ifcElement.GlobalId, ptype = ifcElement.is_a(), name = ifcElement.Name).save()
                    element.version.append(self.version.pk)
                    if ifcElement.Description is not None:
                        element.description = ifcElement.Description
                    element.save()
                    self.systems.append(element)
                elif ifcType == "IfcGroup":
                    if ifcElement.Name is not None:
                        element = m.IfcGroup(pid = ifcElement.id(), ptype = ifcElement.is_a(), name = ifcElement.Name).save()
                    else:
                        element = m.IfcGroup(pid = ifcElement.id(), ptype = ifcElement.is_a()).save()
                    element.version.append(self.version.pk)
                    element.save()
                    self.groups.append(element)
                elif ifcType == "IfcPropertySingleValue":
                    element = m.IfcSingleProperty(pid = ifcElement.id(), ptype = ifcElement.is_a()).save()
                    if ifcElement.NominalValue is not None:
                        element.value_type = ifcElement.NominalValue.is_a()
                        element.value = ifcElement.NominalValue[0]
                    if ifcElement.Unit is not None:
                        element.unit=ifcElement.Unit
                    if ifcElement[0] is not None:
                        element.name = ifcElement[0]
                    element.save()
                    self.pset.append(element)
                elif ifcType == "IfcProductType":        
                    element = m.IfcProductType(pid = ifcElement.id(), guid = ifcElement.GlobalId, ptype = ifcElement.is_a(), name = ifcElement.Name).save()
                    try:
                        predefined = ifcElement.PredefinedType
                    except:
                        predefined = None
                    try:
                        tag = ifcElement.tag
                    except:
                        tag = None
                    if predefined is not None:
                        element.predefined = predefined
                    if tag is not None:
                        element.tag = tag
                    element.version.append(self.version.pk)
                    element.save()
                    self.productTypes.append(element)
            return element
        except:
            print("Not fit for module classes "+str(ifcElement.id()))
            return None
        
        # Identifies object by ifc id() and returns relevant object from all subclasses of IfcFile.
    def get_object_by_id(self, prop):
        l = []

        elements = self.projects + self.sites + self.buildings + self.storeys + self.spaces + self.products + self.materials + self.systems + self.groups + self.productTypes + self.shapes
        for x in elements:
            if x.pid == prop:
                l.append(x)
        if len(l) == 1:
            return l[0]
        elif len(l) == 0:
            return None
        else:
            return l
    
    def update_element(self, new_element):
        if isinstance(new_element, m.IfcProject):
            self.projects = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.projects]
        elif isinstance(new_element, m.IfcSite):
            self.sites = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.sites]
        elif isinstance(new_element, m.IfcBuilding):
            self.buildings = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.buildings]
        elif isinstance(new_element, m.IfcProduct):
            self.products = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.products]
        elif isinstance(new_element, m.IfcProductType):
            self.productTypes = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.productTypes]
        elif isinstance(new_element, m.IfcMaterial):
            self.materials = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.materials]
        elif isinstance(new_element, m.IfcGroup):
            self.groups = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.groups]
        elif isinstance(new_element, m.IfcSystem):
            self.systems = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.systems]
        elif isinstance(new_element, m.IfcStorey):
            self.storeys = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.storeys]
        elif isinstance(new_element, m.IfcSpace):
            self.spaces = [new_element if old_element.pid == new_element.pid else old_element for old_element in self.spaces]

    def add_product_type_relation(self, element, productType):
        element.productType = productType
        element.save()
        self.update_element(element)
        
    def add_material_relation(self, element, material):
        element.material.append(material)
        element.save()
        self.update_element(element)
        
    def add_group_relation(self, element, group):
        element.group.append(group)
        element.save()
        self.update_element(element)
        
    def add_system_relation(self, element, system):
        element.system.append(system)
        element.save()
        self.update_element(element)
        
    def add_building_relation(self, element, building):
        element.building.append(building)
        element.save()
        self.update_element(element)
        
    def add_storey_relation(self, element, storey):
        element.storey.append(storey)
        element.save()
        self.update_element(element)
        
    def add_space_relation(self, element, space):
        element.space.append(space)
        element.save()
        self.update_element(element)
        
    def add_site_relation(self, element, site):
        element.site = site
        element.save()
        self.update_element(element)
        
    def add_project_relation(self, element, project):
        element.project = project
        element.save()
        self.update_element(element)
        
    def add_pset(self, element, pset):
        element.pset.append(pset)
        element.save()
        self.update_element(element)
        
    def add_shape(self, element, ifcElement):
        shape = IfcShapeRepresentation(ifcElement)
        ifc_element = m.IfcShapeRepresentation(pid=shape.pid, identifier=shape.identifier, RepresentationType=shape.RepresentationType, footprint=shape.footprint, footprint_react=shape.footprint_react, top=shape.top, bottom=shape.bottom, center=shape.center)
        self.shapes.append(ifc_element)
        element.shape = ifc_element
        element.save()
        self.update_element(element)
    
    def add_version(self, element, version):
        element.version.append(version)
        element.save()
        self.update_element(element)
        

    ## Update previous version functions to sync ifc-objects from other
    def update_prev_version_site(self):
        prev_version = self.verisonResolver.get_previous_version()
        sites = m.IfcSite.objects.raw({'version': prev_version.pk})
        for site in sites:
            self.sites.append(site)
        
    def update_prev_version_storeys(self):
        prev_version = self.verisonResolver.get_previous_version()
        if len(self.storeys) == 0:
            storeys = m.IfcStorey.objects.raw({'version': prev_version.pk})
            for old_storey in storeys:
                storey = self.get_object_by_id(old_storey.pid)
                if storey is None:
                    old_storey.version.append(self.version)
                    old_storey.save()
                    self.storeys.append(old_storey)
        
    def update_prev_version_spaces(self):
        prev_version = self.verisonResolver.get_previous_version()
        if len(self.spaces) == 0:
            spaces = m.IfcSpace.objects.raw({'version': prev_version.pk})
            for old_space in spaces:
                space = self.get_object_by_id(old_space.pid)
                if space is None:
                    old_space.version.append(self.version)
                    old_space.save()
                    self.spaces.append(old_space)
        
    def update_prev_version_products(self):
        prev_version = self.verisonResolver.get_previous_version()
        ready_prod = []
        prev_file = []
        products = m.IfcProduct.objects.raw({'version': prev_version.pk})
        for old_product in products:
            product = self.get_object_by_id(old_product.pid)
            if product is None:
                ready_prod.append(old_product)
            else:
                if old_product.filepath not in prev_file:
                    prev_file.append(old_product.filepath)
        for file in prev_file:
            for prod in ready_prod:
                if prod.filepath == file:
                    ready_prod.remove(prod)
        
        for prod in ready_prod:
            self.add_previous_product_to_store(prod)

    def add_previous_product_to_store(self, old_product):
        old_product.version.append(self.version)
        old_product.save()
        self.products.append(old_product)
        for old_element in old_product.system:
            element = self.get_object_by_id(old_element.pid)
            if element is None:
                old_element.version.append(self.version)
                old_element.save()
                self.systems.append(old_element)
        for old_element in old_product.group:
            element = self.get_object_by_id(old_element.pid)
            if element is None:
                old_element.version.append(self.version)
                old_element.save()
                self.groups.append(old_element)
        for old_element in old_product.material:
            element = self.get_object_by_id(old_element.pid)
            if element is None:
                old_element.version.append(self.version)
                old_element.save()
                self.materials.append(old_element)
        old_element = old_product.productType
        if old_element is not None:
            element = self.get_object_by_id(old_element.pid)
            if element is None:
                old_element.version.append(self.version)
                old_element.save()
                self.productTypes.append(old_element)
        
    def update_product_space_relation(self):
        for space in self.spaces:
            for product in self.products:
                if product.storey == space.storey:
                    try:
                        s_shape = Polygon(space.shape.footprint)
                        p_shape = Polygon(product.shape.footprint)
                        if p_shape.intersects(s_shape):
                            if product.space == space:
                                print("Correct product - space relation")
                            else:
                                if product.space is not None:
                                    print("Updating space relation")
                                self.add_space_relation(product, space)
                    except:
                        print("No shape")
                        print(product.pid)
                        print(space.pid)
        
    def update_product_space_storey_relation(self):

        for element in self.products+self.spaces:
            for storey in self.storeys:
                if element.shape is not None:
                    if element.shape.center[2]*1000 >= storey.bottom:
                        if element.shape.center[2] * 1000 <= storey.top:
                            if element.storey == storey:
                                print("Correct")
                            else:
                                if element.storey is not None:
                                    print("Updating storey")
                                self.add_storey_relation(element, storey)

    def set_storey_top(self):
        for storey in self.storeys:
            init_top = 10000000000
            for other_storey in self.storeys:
                if other_storey.bottom > storey.bottom:
                    if other_storey.bottom - storey.bottom < init_top - storey.bottom:
                        init_top = other_storey.bottom
            storey.top = init_top
            storey.save()
            self.update_element(storey)
                            

# Shape representation handling
class IfcShapeRepresentation:
    def __init__(self, ifcproduct):
        self.pid = ifcproduct.Representation.Representations[0].id()
        self.identifier = ifcproduct.Representation.Representations[0].RepresentationIdentifier
        self.RepresentationType = ifcproduct.Representation.Representations[0].RepresentationType
        self.position = None
        self.axis = [0,0,1]
        self.refDirection = [1,1,0]
        self.shape = None
        self.shape2 = PythonOCCshape(ifcproduct)
        self.footprint = None
        self.footprint_react = None
        self.top = None
        self.bottom = None
        self.center = None
        try:
            self.position = ifcproduct.ObjectPlacement.RelativePlacement.Location.Coordinates
        except:
            print("Missing objectplacement coordinates" + str(ifcproduct.id()))
        try:
            self.axis = ifcproduct.ObjectPlacement.RelativePlacement.Axis.DirectionRatios
        except:
            pass
        try:
            self.refDirection = ifcproduct.ObjectPlacement.RelativePlacement.RefDirection.DirectionRatios
        except:
            pass
        
        try:
            if ifcproduct.Representation.Representations[0].RepresentationType == "Brep":
                self.shape = IfcFacedBrep(ifcproduct.Representation.Representations[0].Items[0])
            elif ifcproduct.Representation.Representations[0].RepresentationType == "MappedRepresentation":
                self.shape = IfcMappedItem(ifcproduct.Representation.Representations[0].Items[0])
            elif ifcproduct.Representation.Representations[0].RepresentationType == "SurfaceModel":
                self.shape = IfcFaceBasedSurfaceModel(ifcproduct.Representation.Representations[0].Items)
            elif ifcproduct.Representation.Representations[0].RepresentationType == "SweptSolid":
                self.shape = IfcExtrudedAreaSolid(ifcproduct.Representation.Representations[0].Items[0])
                #print(len(element.Items))
            elif ifcproduct.Representation.Representations[0].RepresentationType == "GeometricCurveSet":
                self.shape = IfcGeometricCurveSet(ifcproduct.Representation.Representations[0].Items)
            elif ifcproduct.Representation.Representations[0].RepresentationType == "CSG":
                self.shape = None
                print("CSG")
            elif ifcproduct.Representation.Representations[0].RepresentationType == "Clipping":
                self.shape = None
                print("Clipping")
            else:
                print(ifcproduct.Representation.Representations[0].id())
                print(ifcproduct.Representation.Representations[0].RepresentationType)
                print("df")
            self.add_footprint()
            self.add_top_bottom()
            self.add_center()

        except:
            print(ifcproduct.Representation.Representations[0].id())
        
    def add_footprint(self):
        self.footprint = self.get_footprint(calc=True)
        self.footprint_react = self.get_footprint()
        
    def to_dict(self):
        p_dict = {}
        p_dict['pid'] = self.pid
        p_dict['identifier'] = self.identifier
        p_dict['RepresentationType'] = self.RepresentationType
        p_dict['footprint'] = self.footprint
        p_dict['footprint-react'] = self.footprint_react
        p_dict['top'] = self.top
        p_dict['bottom'] = self.bottom
        p_dict['center'] = self.center

        #p_dict['vertices'] = self.get_vertices()

        return p_dict
    
    def get_points(self):
        if self.RepresentationType == "GeometricCurveSet":
            return self.shape.footprint()
        else:
            shape_corners = self.shape.get_points()
            corners = []
            for point in shape_corners:
                #point = self.rotate("z", point)
                #point = self.rotate("x", point)
                x = point[0] + self.position[0]
                y = point[1] + self.position[1]
                z = point[2] + self.position[2]
                corners.append([x,y,z])
            return corners

    def get_footprint(self, calc=False):

        try:
            polygon = self.order_points(self.get_vertices())
            if self.need_section_for_footprint():
                polygon = self.order_points(self.footprint_sweptsolid())
            points = []
            for p in polygon:
                if calc:
                    points.append([p[0], p[1]])
                else:
                    points.append({'x': p[0], 'y': p[1]})

        except:
            print("No footprint")
            print(self.pid)
            points = None
        return points
    
    def add_top_bottom(self):
        vertices = np.array(self.get_vertices())
        self.top = max(vertices[:,2])
        self.bottom = min(vertices[:,2])
        
    def rotate(self, dir, point):
        if dir == "z":
            rotation_vector = np.array(self.axis) - np.array([0,0,1])
            r = R.from_rotvec(rotation_vector)
        elif dir == "x":
            rotation_vector = np.array(self.refDirection) - np.array([1,0,0])
            r = R.from_rotvec(rotation_vector)
        return r.apply(point)
    
    def get_max_dim(self):
        return self.shape.get_max_dim()

    def footprint_sweptsolid(self):
        section_height = self.shape2.center()[2]
        section_plane = gp_Pln(
            gp_Pnt(0, 0, section_height),
            gp_Dir(0, 0, 1)
        )
        dim = self.get_max_dim()
        center = self.shape2.center()
        
        section_face = BRepBuilderAPI_MakeFace(section_plane, center[0]-dim, center[0]+dim, center[1]-dim, center[1]+dim).Face()
        section = BRepAlgoAPI_Section(section_face, self.shape2.shape).Shape()
        
        bt = BRep.BRep_Tool()
        t = Topo(section)
        vertices = t.vertices()
        vert = []
        for vertex in vertices:
            vert.append([bt.Pnt(vertex).Coord()[0], bt.Pnt(vertex).Coord()[1], bt.Pnt(vertex).Coord()[2]])
        
        return vert
    
    def get_vertices(self):
        return self.shape2.get_vertices()
    
    def order_points(self, pts):
        # Creating the convex hull surrounding boundingbox
        pts = np.array(pts)
        pts = pts[:,:2]

        try:
            sortedC = pts[ConvexHull(pts[:,:2]).vertices]
            return sortedC
        except: 
            return np.array(pts)

    def need_section_for_footprint(self):
        section = False
        if self.RepresentationType == "MappedRepresentation":
            if self.shape.RepresentationType == "SweptSolid":
                if self.shape.shape.type == "IfcCircleProfileDef":
                    section = True
                elif self.shape.shape.type == "IfcCircleHollowProfileDef":
                    section = True
        elif self.RepresentationType == "SweptSolid":
            if self.shape.type == "IfcCircleProfileDef":
                section = True
            elif self.shape.type == "IfcCircleHollowProfileDef":
                section = True
        
        return section
    
    def add_center(self):
        self.center = self.shape2.center()

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
    
    def get_max_dim(self):
        return self.shape.get_max_dim()
            
# Types of shape
class IfcExtrudedAreaSolid:
    def __init__(self, element):
        self.x = element.Position.Location.Coordinates[0]
        self.y = element.Position.Location.Coordinates[1]
        self.z = element.Position.Location.Coordinates[2]
        self.dirX = element.ExtrudedDirection.DirectionRatios[0]
        self.dirY = element.ExtrudedDirection.DirectionRatios[1]
        self.dirZ = element.ExtrudedDirection.DirectionRatios[2]
        self.depth = element.Depth
        self.type = element.SweptArea.is_a()
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
        center, vertices = self.sweptArea.footprint()
        corners = []
        for point in vertices:
            corr = [self.x-center['x'], self.y-center['y'], self.z]
            c1 = [corr[2], point[1]+corr[1], point[0]+corr[0]]
            c2 = [corr[2]+self.depth, point[1]+corr[1], point[0]+corr[0]]
            corners.append(c1)
            corners.append(c2)
            #corners.append([point[0]+corr[0], point[1]+corr[1], corr[2]])
            #corners.append([point[0]+corr[0], point[1]+corr[1], corr[2]+self.depth])
        
        return corners

    def get_max_dim(self):
        return max([self.sweptArea.get_max_width(), self.depth])

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

    def get_max_width(self):
        return max([self.xDim, self.yDim])

    def footprint(self):
        center = {'x': self.x, 'y': self.y}
        return center, np.array([
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
    
    def get_max_width(self):
        return self.radius

    def footprint(self):
        parts = 12
        points = []
        center = {'x': self.x, 'y': self.y}
        for angle in np.linspace(self.trim1, self.trim2, parts):
            points.append([self.x + np.cos(angle)*self.radius, self.y + np.sin(angle)*self.radius])

        return center, points
            

class IfcTrimmedCurve:
    def __init__(self, element):
        self.id = element.id()
        self.basisCurve = IfcCircleProfileDef(element.BasisCurve)
        self.trim1 = element.Trim1[0][0]
        self.trim2 = element.Trim2[0][0]
    
    def footprint(self):
        parts = 12
        points = []
        center = {'x': self.basisCurve.x, 'y': self.basisCurve.y}
        for angle in np.linspace(self.trim1, self.trim2, parts):
            points.append([self.basisCurve.x + np.cos(angle)*self.basisCurve.radius, self.basisCurve.y + np.sin(angle)*self.basisCurve.radius])

        return center, points
    
    def get_max_width(self):
        return self.basisCurve.radius

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
    
class PythonOCCshape():
    def __init__(self, element):
        shape = None
        self.set_shape(element)

    def set_shape(self, ifc_shape):

        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_PYTHON_OPENCASCADE, True)
        settings.set(settings.INCLUDE_CURVES, True)

        roomocc = ifcopenshell.geom.create_shape(settings, ifc_shape)
        self.shape = OCC.Core.TopoDS.TopoDS_Iterator(roomocc.geometry).Value()


    def get_bbox(self):

        vertices = []
        shape = Common.get_boundingbox(self.shape)
        vertices.append([shape[0], shape[1], shape[2]])
        vertices.append([shape[3], shape[1], shape[2]])
        vertices.append([shape[0], shape[4], shape[2]])
        vertices.append([shape[0], shape[1], shape[5]])
        vertices.append([shape[3], shape[1], shape[5]])
        vertices.append([shape[0], shape[4], shape[5]])
        
        return vertices
    
    def get_vertices(self):
        bt = BRep.BRep_Tool()
        t = Topo(self.shape)
        vertices = t.vertices()
        vert = []
        for vertex in vertices:
            vert.append([bt.Pnt(vertex).Coord()[0], bt.Pnt(vertex).Coord()[1], bt.Pnt(vertex).Coord()[2]])
        
        return vert
    
    def center(self):
        return Common.center_boundingbox(self.shape).Coord()


    def footprint(self, shape):
        section_height = self.center()[2]
        section_plane = OCC.gp.gp_Pln(
            OCC.gp.gp_Pnt(0, 0, section_height),
            OCC.gp.gp_Dir(0, 0, 1)
        )
        dim = shape.get_max_dim()
        center = self.center()
        
        section_face = BRepBuilderAPI_MakeFace(section_plane, center[0]-dim, center[0]+dim, center[1]-dim, center[1]+dim).Face()
        section = BRepAlgoAPI_Section(section_face, self.shape).Shape()
        
        bt = BRep.BRep_Tool()
        t = Topo(section)
        vertices = t.vertices()
        vert = []
        for vertex in vertices:
            vert.append([bt.Pnt(vertex).Coord()[0], bt.Pnt(vertex).Coord()[1], bt.Pnt(vertex).Coord()[2]])
        
        return vert
    