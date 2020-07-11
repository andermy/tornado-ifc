import mongo
from OCC.TopoDS import *
from OCC.TopAbs import *
from OCC.TopExp import *
from OCC.TopLoc import *
from OCC.TopoDS import *
from OCC.BRep import BRep_Builder
from OCC import BRep
from OCCUtils.Topology import Topo
import OCC.GProp
import OCC.BRepGProp

import numpy as np
import helper as helper

from OCC.gp import gp_Vec, gp_Pnt

import ifcopenshell
import ifcopenshell.geom

import os
import uuid

from OCC.Visualization import Tesselator
import OCCUtils.Common as Common

from shapely.geometry import Point, Polygon
from scipy.spatial import ConvexHull
from shapely.ops import nearest_points
import asyncio

#@receiver(post_save, sender=File)
#sender, instance, created, **kwargs

def import_ifc(datafile, project):
    #if kwargs.get(created, False):
    #    file = kwargs.get('instance')
    print("Start")
    # which IFC type must create which Connected Properties type

    #ifcfiles = IfcFile.objects.filter(project=project)
    #version = len(ifcfiles)-1
    ifcfile = ifcopenshell.open(datafile)
    #ifcfile = ifcopenshell.open(ifcfiles[version].datafile.path)
    #project = datafile.project.all()[0]

    # building relations tables
    prodrepr = {}  # product/representations table
    mattable = {}  # { objid:matid }
    floorAnnotations = {}  # { host:[child,...], ... }
    additions = {}  # { host:[child,...], ... }
    colors = {}  # { id:(r,g,b)}
    groups = {}  # { host:[child,...], ... }     # used in structural IFC
    subtractions = []  # [ [opening,host], ... ]
    properties = {}  # { obj : { cat : [property, ... ], ... }, ... }

    pMatrix = []

    floors = ifcfile.by_type("IfcBuildingStorey")
    products = ifcfile.by_type("IfcProduct")
    openings = ifcfile.by_type("IfcOpeningElement")
    annotations = ifcfile.by_type("IfcAnnotation")
    materials = ifcfile.by_type("IfcMaterial")
    rooms = ifcfile.by_type("IfcSpace")
    relFillsElements = ifcfile.by_type("IfcRelFillsElement")
    relVoidsElements = ifcfile.by_type("IfcRelVoidsElement")

    ifcProject = ifcfile.by_type("IfcProject")[0]

    unit = ifcfile.by_type("IfcSIUnit")[0]
    length = unit.Name
    prefix = unit.Prefix

    count = 0
    
    task = []
    print("loading storeys")
    for product in floors:
        count = count + 1
        task.append(iterate_shape(product, colors, project, ifcfile, length, prefix, count))
    print("loading rooms")
    for product in rooms:
        count = count + 1
        task.append(iterate_shape(product, colors, project, ifcfile, length, prefix, count))
    print("loading products")
    for product in products:
        count = count + 1
        task.append(iterate_shape(product, colors, project, ifcfile, length, prefix, count))   
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*task))
    loop.close()
    #iterate_shapes(products, colors, project, ifcfile, length, prefix)

    #update_storeys(project)
    #setRelations(ifcfile, project)
    #setRoomRelation(ifcfile, project)
    #validateFloorRelations(project)
    #set_corners_init(project)
    #products = ProjectProduct.objects.all()
    #count = 0
    #for product in products:
    #    calc_center(product, ifcfile)
    #    print(count)
    #    count = count + 1
    #add_product_to_room2(project)
    #set_window_door_in_walls(project)
    #set_wall_in_room(project)    


async def iterate_shape(product, colors, project, ifcfile, length, prefix, count, version):

    site = ['IfcSite']
    building = ['IfcBuilding']
    floor = ['IfcBuildingStorey']
    structure = ['IfcBeam', 'IfcBeamStandardCase', 'IfcColumn', 'IfcColumnStandardCase', 'IfcSlab',
                 'IfcFooting', 'IfcPile', 'IfcTendon']
    wall = ['IfcWall', 'IfcWallStandardCase', 'IfcCurtainWall']
    window = ['IfcWindow', 'IfcWindowStandardCase']
    door = ['IfcDoor', 'IfcDoorStandardCase']
    roof = ['IfcRoof']
    stairs = ['IfcStair', 'IfcStairFlight', 'IfcRamp', 'IfcRampFlight']
    space = ['IfcSpace']
    rebar = ['IfcReinforcingBar'],
    panel = ['IfcPlate']
    equipment = ['IfcFurnishingElement', 'IfcSanitaryTerminal', 'IfcFlowTerminal', 'IfcElectricAppliance']
    pipe = ['IfcPipeSegment', 'IfcFlowSegment']
    pipeConnector = ['IfcPipeFitting']
    opening = ['IfcOpeningElement']

    # Prepere mongoDB
    m = mongo.MongoDb()

    pid = product.id()
    guid = product.GlobalId
    ptype = product.is_a()
    name = ""
    if product.Name:
        name = product.Name

    #if product.Representation:
        # 2D footprint -if we need 2D
    #    for r in product.Representation.Representations:
    #        if r.RepresentationIdentifier == "FootPrint":
    #            print("annotation")

    try:
        shape = get_shape(product)
    except:
        shape = None

    if shape is not None:
        
        if ptype in building:
            m.define_collection('building')
            dict = {
                'project': project,
                'version': version,
                'pid': pid,
                'guid': guid,
                'ptype': ptype,
                'name': name
            }
            m.insert_one(dict)
                
        elif ptype in floor:
            # IFC Building storey or IfcRoof
            top = correctLengt(product.ObjectPlacement.RelativePlacement.Location.Coordinates[2], length, prefix)
            bottom = correctLengt(product.ObjectPlacement.RelativePlacement.Location.Coordinates[1], length, prefix)
            vertices = get_vertices(shape, length)
            corners = get_corners(vertices, False)
            bbox = get_bbox(shape, length)
            m.define_collection('storey')
            dict = {
                'project': project,
                'version': version,
                'pid': pid,
                'guid': guid,
                'ptype': ptype,
                'name': name,
                'top': top,
                'bottom': bottom,
                'vertices': vertices,
                'corners': corners,
                'bbox': bbox
            }
            m.insert_one(dict)

        elif ptype in space:
            # IFCSpaces - building rooms / zones
            area = calc_area(product)
            vertices = get_vertices(shape, length)
            corners = get_corners(vertices, True)
            bbox = get_bbox(shape, length)
            m.define_collection('space')
            dict = {
                'project': project,
                'version': version,
                'pid': pid,
                'guid': guid,
                'ptype': ptype,
                'name': name,
                'longName': product.LongName,
                'area': area,
                'vertices': vertices,
                'corners': corners,
                'bbox': bbox
            }
            m.insert_one(dict)

        elif ptype in opening:
                # IFCWalls
            vertices = get_vertices(shape, length)
            corners = get_corners(vertices, False)
            bbox = get_bbox(shape, length)
            m.define_collection('opening')
            dict = {
                'project': project,
                'version': version,
                'pid': pid,
                'guid': guid,
                'ptype': ptype,
                'name': name,
                'vertices': vertices,
                'corners': corners,
                'bbox': bbox
            }
            m.insert_one(dict)
                
        else:
            # IFC objects / products - rest av all products
            vertices = get_vertices(shape, length)
            corners = get_corners(vertices, False)
            bbox = get_bbox(shape, length)
            m.define_collection('product')
            dict = {
                'project': project
                'version': version,
                'pid': pid,
                'guid': guid,
                'ptype': ptype,
                'name': name,
                'vertices': vertices,
                'corners': corners,
                'bbox': bbox
            }
            m.insert_one(dict)
    else:
        if ptype in floor:
            top = correctLengt(product.ObjectPlacement.RelativePlacement.Location.Coordinates[2], length, prefix)
            bottom = correctLengt(product.ObjectPlacement.RelativePlacement.Location.Coordinates[1], length, prefix)
            m.define_collection('storey')
            dict = {
                'project': project,
                'version': version,
                'pid': pid,
                'guid': guid,
                'ptype': ptype,
                'name': name,
                'top': top,
                'bottom': bottom
            }
            m.insert_one(dict)
        else:
            print("No shape and not IfcBuildingStorey")
            print(ptype)
            print(guid)
    print(count)  
                    

def get_vertices(shape, length):
    bt = BRep.BRep_Tool()
    t = Topo(shape)
    vertices = t.vertices()
    vert = []
    for vertex in vertices:
        vert.append([correctLengt(bt.Pnt(vertex).Coord()[0], length, None), correctLengt(bt.Pnt(vertex).Coord()[1], length, None), correctLengt(bt.Pnt(vertex).Coord()[2], length, None)])
    
    return vert

def get_bbox(shape, length):

    vertices = []
    shape = Common.get_boundingbox(shape)
    vertices.append([correctLengt(shape[0], length, None), correctLengt(shape[1], length, None), correctLengt(shape[2], length, None)])
    vertices.append([correctLengt(shape[3], length, None), correctLengt(shape[1], length, None), correctLengt(shape[2], length, None)])
    vertices.append([correctLengt(shape[0], length, None), correctLengt(shape[4], length, None), correctLengt(shape[2], length, None)])
    vertices.append([correctLengt(shape[0], length, None), correctLengt(shape[1], length, None), correctLengt(shape[5], length, None)])
    vertices.append([correctLengt(shape[3], length, None), correctLengt(shape[1], length, None), correctLengt(shape[5], length, None)])
    vertices.append([correctLengt(shape[0], length, None), correctLengt(shape[4], length, None), correctLengt(shape[5], length, None)])
    
    return vertices

def get_corners(vertices, bottom):
    #pipe = ['IfcPipeSegment', 'IfcFlowSegment']
    corners = []
    pts = np.array(vertices)
    if bottom:
        pts = pts[np.where(pts[:,2]==min(pts[:,2]))]
    else:
        try:
            pts = pts[ConvexHull(pts[:,:2]).vertices]
        except:
            try:
                pts = pts[:,:2]
            except:
                print(pts)

    try:
        polygon = Polygon(pts)
        for c in list(polygon.exterior.coords):
            corners.append(c)
    except:
        try:
            for c in pts:
                corners.append([c[0], c[1]])
        except:
            print("Error, no corner")
    return corners


def distance(P1, P2):
        import math
        return math.sqrt(math.pow(P1[0] - P2[0], 2) +
                         math.pow(P1[1] - P2[1], 2) +
                         math.pow(P1[2] - P2[2], 2)) 


def get_shape(ifc_shape):

    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_PYTHON_OPENCASCADE, True)
    settings.set(settings.INCLUDE_CURVES, True)

    roomocc = ifcopenshell.geom.create_shape(settings, ifc_shape)
    shape = OCC.TopoDS.TopoDS_Iterator(roomocc.geometry).Value()

    return shape


def calc_area(room):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_PYTHON_OPENCASCADE, True)
    settings.set(settings.INCLUDE_CURVES, True)

    try: 
        roomocc = ifcopenshell.geom.create_shape(settings, room)
        shape = OCC.TopoDS.TopoDS_Iterator(roomocc.geometry).Value()

        b,t = get_room_height(shape)
        props = OCC.GProp.GProp_GProps()
        OCC.BRepGProp.brepgprop_VolumeProperties(roomocc.geometry, props)
        return props.Mass()/abs(t-b)
    except:
        return 0

def calc_center(product, ifcfile):
    productIfc = ifcfile.by_id(product.pid)
    try:
        productShape = get_shape(productIfc)
        center = Common.center_boundingbox(productShape)
        pnt = Pnt(X=center.Coord()[0], Y=center.Coord()[1], Z=center.Coord()[2])
        pnt.save()
        product.center.add(pnt)
        product.save()
        
    except:
        pass


def correctLengt(scalar, length, prefix):
    if length == 'METRE':
        if prefix == 'MILLI':
            scalar = scalar
        else:
            scalar = scalar * 1000
    
    return scalar

def old_stuff():
    for r in ifcfile.by_type("IfcRelAggregates"):
        # categorisering: f.eks. tak og ulike takelementer: må ha
        additions.setdefault(r.RelatingObject.id(), []).extend([e.id() for e in r.RelatedObjects])

    for r in ifcfile.by_type("IfcRelAssociatesMaterial"):
        # Angir materialsammenhenger- must
        for o in r.RelatedObjects:
            if r.RelatingMaterial.is_a("IfcMaterial"):
                mattable[o.id()] = r.RelatingMaterial.id()
            elif r.RelatingMaterial.is_a("IfcMaterialLayer"):
                mattable[o.id()] = r.RelatingMaterial.Material.id()
            elif r.RelatingMaterial.is_a("IfcMaterialLayerSet"):
                mattable[o.id()] = r.RelatingMaterial.MaterialLayers[0].Material.id()
            elif r.RelatingMaterial.is_a("IfcMaterialLayerSetUsage"):
                mattable[o.id()] = r.RelatingMaterial.ForLayerSet.MaterialLayers[0].Material.id()

    for p in ifcfile.by_type("IfcProduct"):
        # Om product har shape/ representation
        if hasattr(p, "Representation"):
            if p.Representation:
                for it in p.Representation.Representations:
                    for it1 in it.Items:
                        prodrepr.setdefault(p.id(), []).append(it1.id())
                        if it1.is_a("IfcBooleanResult"):
                            prodrepr.setdefault(p.id(), []).append(it1.FirstOperand.id())
                        elif it.Items[0].is_a("IfcMappedItem"):
                            prodrepr.setdefault(p.id(), []).append(it1.MappingSource.MappedRepresentation.id())
                            if it1.MappingSource.MappedRepresentation.is_a("IfcShapeRepresentation"):
                                for it2 in it1.MappingSource.MappedRepresentation.Items:
                                    prodrepr.setdefault(p.id(), []).append(it2.id())

    for r in ifcfile.by_type("IfcStyledItem"):
        # Farger
        if r.Styles:
            if r.Styles[0].is_a("IfcPresentationStyleAssignment"):
                if r.Styles[0].Styles[0].is_a("IfcSurfaceStyle"):
                    if r.Styles[0].Styles[0].Styles[0].is_a("IfcSurfaceStyleRendering"):
                        if r.Styles[0].Styles[0].Styles[0].SurfaceColour:
                            c = r.Styles[0].Styles[0].Styles[0].SurfaceColour
                            if r.Item:
                                for p in prodrepr.keys():
                                    if r.Item.id() in prodrepr[p]:
                                        colors[p] = (c.Red, c.Green, c.Blue)
                        else:
                            for m in ifcfile.by_type("IfcMaterialDefinitionRepresentation"):
                                for it in m.Representations:
                                    if it.Items:
                                        if it.Items[0].id() == r.id():
                                            colors[m.RepresentedMaterial.id()] = (c.Red, c.Green, c.Blue)