
from typing import List
from bson.json_util import default
from openpyxl.descriptors.base import Float
from pymongo.write_concern import WriteConcern
from pymodm import EmbeddedMongoModel, MongoModel, fields
from pymodm.fields import ListField, IntegerField, ReferenceField, PointField, PolygonField, MultiPointField, EmbeddedDocumentListField, EmbeddedDocumentField, FloatField, CharField, EmailField, DictField, LineStringField, EmbeddedDocumentListField, BooleanField, FileField, DateTimeField

from pymongo.write_concern import WriteConcern

from pymodm import MongoModel, fields

class Project(MongoModel):
    name = CharField()
    area = FloatField()
    buildingType = CharField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class User(MongoModel):
    email = EmailField(primary_key=True)
    first_name = CharField()
    last_name = CharField()
    projects = ListField(ReferenceField(Project))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class Organisation(MongoModel):
    name = CharField()
    member = ListField(ReferenceField(User))
    projects = ListField(ReferenceField(Project))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class Version(MongoModel):
    project = ReferenceField(Project)
    branch = CharField()
    version = IntegerField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'
    
    def to_json(self):
        items = self.to_son()
        items['project'] = self.project.to_son()
        return items

class IfcSingleProperty(MongoModel):
    pid = IntegerField()
    ptype = CharField()
    value_type = CharField(blank=True)
    value = CharField(blank=True)
    unit = CharField(blank=True)
    name = CharField(blank=True)

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class  IfcShapeRepresentation(EmbeddedMongoModel):
    pid = IntegerField()
    identifier = CharField()
    RepresentationType = CharField()
    footprint = ListField(ListField())
    footprint_react = DictField()
    top = FloatField()
    bottom = FloatField()
    center = ListField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcProject(MongoModel):
    pid = IntegerField()
    guid = CharField()
    ptype = CharField()
    name = CharField(blank=True)
    longName = CharField(blank=True)
    description = CharField(blank=True)
    phase = CharField(blank=True)
    lengthUnit = CharField(blank=True)
    lengthPrefix = CharField(blank=True)
    dir = ListField(FloatField(blank=True))
    pset = ListField(ReferenceField(IfcSingleProperty))
    version = ListField(ReferenceField(Version))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcSite(MongoModel):
    pid = IntegerField()
    guid = CharField()
    ptype = CharField()
    name = CharField(blank=True)
    description = CharField(blank=True)
    refLatitude = ListField(blank=True)
    refLongitude = ListField(blank=True)
    refElevation = FloatField(blank=True)
    LandTitleNumber = CharField(blank=True)
    #quitself.SiteAddress = element.SiteAddress
    pset = ListField(ReferenceField(IfcSingleProperty))
    project = ReferenceField(IfcProject)
    version = ListField(ReferenceField(Version))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcBuilding(MongoModel):
    pid = IntegerField()
    guid = CharField()
    ptype = CharField(blank=True)
    name = CharField(blank=True)
    description = CharField(blank=True)
    longName = CharField(blank=True)
    site = ReferenceField(IfcSite)
    pset = ListField(ReferenceField(IfcSingleProperty))
    shape = EmbeddedDocumentField(IfcShapeRepresentation)
    version = ListField(ReferenceField(Version))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcStorey(MongoModel):
    pid = IntegerField()
    guid = CharField()
    ptype = CharField()
    name = CharField(blank=True)
    description = CharField(blank=True)
    longName = CharField(blank=True)
    building = ListField(ReferenceField(IfcBuilding))
    pset = ListField(ReferenceField(IfcSingleProperty))
    shape = EmbeddedDocumentField(IfcShapeRepresentation)
    version = ListField(ReferenceField(Version))
    bottom = FloatField(blank=True)
    top = FloatField(blank=True)

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcMaterial(MongoModel):
    pid = IntegerField()
    ptype = CharField()
    name = CharField(blank=True)
    pset = ListField(ReferenceField(IfcSingleProperty))
    version = ListField(ReferenceField(Version))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcSystem(MongoModel):
    pid = IntegerField()
    guid = CharField()
    ptype = CharField()
    name = CharField(blank=True)
    description = CharField(blank=True)
    pset = ListField(ReferenceField(IfcSingleProperty))
    version = ListField(ReferenceField(Version))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcGroup(MongoModel):
    pid = IntegerField()
    ptype = CharField()
    name = CharField(blank=True)
    pset = ListField(ReferenceField(IfcSingleProperty))
    version = ListField(ReferenceField(Version))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcProductType(MongoModel):
    pid = IntegerField()
    guid = CharField()
    ptype = CharField()
    name = CharField(blank=True)
    predefined = CharField(blank=True)
    tag = CharField(blank=True)
    pset = ListField(ReferenceField(IfcSingleProperty))
    material = ListField(ReferenceField(IfcMaterial))
    shape = EmbeddedDocumentField(IfcShapeRepresentation)
    version = ListField(ReferenceField(Version))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class ProductSignal(MongoModel):
    name = CharField()
    signalType = CharField()
    terminals = ListField()
    wires = IntegerField()
    min_value = FloatField()
    max_value = FloatField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class ProductPower(MongoModel):
    powerType = CharField()
    value = FloatField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class ProductType(MongoModel):
    name = CharField()
    producer = CharField()
    connection = ListField(ReferenceField(ProductSignal))
    power = ListField(ReferenceField(ProductPower))
    shape = ReferenceField(IfcShapeRepresentation)
    verified = BooleanField(default=False)
    pset = ListField(ReferenceField(IfcSingleProperty))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcSpace(MongoModel):
    pid = IntegerField()
    guid = CharField()
    ptype = CharField()
    name = CharField(blank=True)
    description = CharField(blank=True)
    longName = CharField(blank=True)
    pset = ListField(ReferenceField(IfcSingleProperty))
    group = ListField(ReferenceField(IfcGroup))
    building = ListField(ReferenceField(IfcBuilding))
    storey = ListField(ReferenceField(IfcStorey))
    shape = EmbeddedDocumentField(IfcShapeRepresentation)
    version = ListField(ReferenceField(Version))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcProduct(MongoModel):
    pid = IntegerField(blank=True)
    guid = CharField(blank=True)
    ptype = CharField(blank=True)
    name = CharField(blank=True)
    description = CharField(blank=True)
    pset = ListField(ReferenceField(IfcSingleProperty))
    group = ListField(ReferenceField(IfcGroup))
    material = ListField(ReferenceField(IfcMaterial))
    building = ListField(ReferenceField(IfcBuilding))
    storey = ListField(ReferenceField(IfcStorey))
    shape = EmbeddedDocumentField(IfcShapeRepresentation)
    space = ListField(ReferenceField(IfcSpace))
    system = ListField(ReferenceField(IfcSystem))
    productType = ReferenceField(IfcProductType)
    product = ReferenceField(ProductType)
    version = ListField(ReferenceField(Version))
    filepath = CharField(blank=True)

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class SpaceFunction(MongoModel):
    space = ReferenceField(IfcSpace)
    text = CharField()
    signal = ListField(ReferenceField(ProductSignal))

class Calculation(MongoModel):
    new_variable = CharField()
    recipe = CharField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'
    

class ExcelFile(MongoModel):
    path = CharField()
    filename = CharField()
    project = ReferenceField(Project)
    created = DateTimeField()
    created_by = ReferenceField(User)

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class DataFrame(MongoModel):
    from_model = BooleanField()
    pset = BooleanField(blank=True)
    type = CharField(blank=True)
    name = CharField(blank=True)
    calculation = ListField(ReferenceField(Calculation))
    version = ReferenceField(Version)
    excelfile = ReferenceField(ExcelFile)
    header = IntegerField(blank=True)
    sheetname = CharField(blank=True)

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class IfcFile(MongoModel):
    path = CharField()
    filename = CharField()
    version = ReferenceField(Version)
    project = ReferenceField(Project)
    created = DateTimeField()
    created_by = ReferenceField(User)

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'
