from os import remove
import pandas as pd
from openpyxl import load_workbook
from bson.objectid import ObjectId
import operator
from itertools import chain

from pandas.core.frame import DataFrame

from models import IfcProduct, IfcSpace, IfcStorey, IfcProductType, Version, IfcSystem, IfcSingleProperty


class Excel():
    def __init__(self, excelfile):
        self.excelfile = excelfile
        self.sheet_names = self.get_sheet_names()
        self.df = []
        self.save_dataframes()

    def get_sheet_names(self):
        wb = load_workbook(filename = self.excelfile.path)
        return wb.sheetnames
    
    def save_dataframes(self):
        for sheet in self.sheet_names:
            df = DataFrame(from_model=False, name=sheet, version=self.excelfile.version, excelfile=self.excelfile, sheetname=sheet).save()
            self.df.append(df)

class Table():
    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.df = None
        if self.dataframe.from_model == True:
            if self.dataframe.type == "space":
                self.create_from_ifc_spaces()
            elif self.dataframe.type == "product":
                self.create_from_ifc_products()
            elif self.dataframe.type == "productType":
                self.create_from_ifc_product_types()
            if self.dataframe.pset == True:
                self.add_dataframe_properties(self.df)
        else:
            self.create_from_excel()
        
        for calc in self.dataframe.calculation:
            self.calculation(calc)

    def create_from_ifc_product_types(self):
        productTypes = IfcProductType.objects.raw({'version': self.dataframe.version.pk}).values()
        productTypes = pd.json_normalize(productTypes)

        self.df = productTypes

    def create_from_ifc_spaces(self):
        spaces = IfcSpace.objects.raw({'version': self.dataframe.version.pk}).values()
        spaces = pd.json_normalize(spaces)

        self.df = spaces

    def create_from_ifc_products(self):
        products = IfcProduct.objects.raw({'version': self.dataframe.version.pk}).values()
        spaces = IfcSpace.objects.raw({'version': self.dataframe.version.pk}).values()
        storeys = IfcStorey.objects.raw({'version': self.dataframe.version.pk}).values()
        productTypes = IfcProductType.objects.raw({'version': self.dataframe.version.pk}).values()
        
        products = pd.json_normalize(products)
        spaces = pd.json_normalize(spaces)
        storeys = pd.json_normalize(storeys)
        productTypes = pd.json_normalize(productTypes)

        storeys = storeys.rename(columns={"_id": "storey.id" ,"name": "storey.name", "longName": "storey.longName"})
        drops = storeys.columns.tolist()
        for s in ["storey.id" ,"storey.name", "storey.longName"]:
            drops.remove(s)
        storeys = storeys.drop(drops, axis=1)
        
        productTypes = productTypes.drop(["pid", "guid", "ptype", "version", "material","_cls"], axis=1)
        productTypes = productTypes.rename(columns={"_id": "productType.id", "name": "productType.name", "predefined": "productType.predefined"})
        spaces = spaces.rename(columns={"_id":"space.id", "name": "space.name", "longName": "space.longName"})
        drops = spaces.columns.tolist()
        for s in ["space.id", "space.name", "space.longName"]:
            drops.remove(s)
        spaces = spaces.drop(drops, axis=1)

        products = products.explode('storey')
        products = products.explode('space')
        products = products.merge(productTypes, left_on="productType", right_on="productType.id")
        products = products.merge(storeys, left_on="storey", right_on="storey.id")
        products = products.merge(spaces, left_on="space", right_on="space.id")
        
        self.df = products.drop(["pid", "guid", "filepath", "group", "version", "storey", "_cls", "shape.pid", "shape.identifier", "shape.RepresentationType", "shape.footprint", "shape.footprint_react.x", "shape.top", "shape.bottom", "shape.center", "shape._cls"], axis=1)


    def add_dataframe_properties(self, df):

        properties = IfcSingleProperty.objects.raw({'version': self.dataframe.version.pk}).values()
        properties = pd.json_normalize(properties)
        properties = properties.rename(columns={"_id":"pset.id", "name": "pset.name", "value_type": "pset.type", "value": "pset.value"})
        df = df.explode('pset')
        df = df.merge(properties, left_on="pset", right_on="pset.id")

        self.df = df

    def to_react_table_json(self):
        new_data = self.df
        row_count = new_data.shape[0]
        column_count = new_data.shape[1]
        column_names = new_data.columns.tolist()
        final_row_data = []
        for index, rows in new_data.iterrows():
            final_row_data.append(rows.to_dict())

        json_result = {'rows': row_count, 'cols': column_count, 'columns': column_names, 'rowData': final_row_data}
        return json_result
    
    def create_from_excel(self):
        self.df = pd.read_excel(self.dataframe.excelfile.path, sheet_name=self.dataframe.sheetname, header=self.dataframe.header)

    def calculation(self, calculation):
        try:
            #x = calculation.recipe.replace("bananas", "apples")
            self.df[calculation.variable] = eval(calculation.recipe)
        except:
            pass