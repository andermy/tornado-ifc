import mongo as m
from bson.objectid import ObjectId
import numpy as np

class ProductTag():
    def __init__(self, project):
        self.db = m.MongoDb()
        self.db.define_collection('tag_structure')
        self.project = project
        self.tags_before_running_index = []

    def createTag(product):
        tag_structure = self.db.query({'project': ObjectId(self.project)})
        tag = ""
        for item in tag_structure['items']:
            if item['type'] == 'constant':
                tag = tag + format(item['value'], "0"+str(item['length']))
            elif item['type'] == 'room':
                tag = tag + format(product['room']['name'], "0"+str(item['length']))
            elif item['type'] == 'system':
                tag = tag + format(product['system']['name'], "0"+str(item['length']))
            elif item['type'] == 'product_category':
                tag = tag + self.resolve_product_type_tag()
            elif item['type'] == 'running_index':
                tag = tag + self.running_index_pool(tag)
            tag = tag + str(item['end'])
        
        return tag
    
    def running_index_pool(self, tag):
        total_tags = np.array(self.tags_before_running_index)
        equal_tags = total_tags[np.where(tag==total_tags)]
        running_index_now = len(equal_tags)
        new_running_index = running_index_now + 1
        self.tags_before_running_index.append(tag)

        return new_running_index

    def resolve_product_type_tag(self, product, tag_structure):
        self.db.define_collection('product_type')
        product_type = self.db.find_one(product['productType'])

        return tag_structure['categories'][product_type['category']]
