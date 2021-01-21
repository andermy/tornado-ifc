import mongo as m
from bson.objectid import ObjectId
from bson.json_util import dumps
import json

class VersionResolver():

    def __init__(self, version=None, branch=None, project=None):
        self.db = m.MongoDb()
        self.db.define_collection('version')
        self.version = None
        self.project = None
        self.branch = None
        if version is not None:
            self.version = version
            self.versionObject = self.get_version_object(version)
            self.branch = self.versionObject['project']
            self.project = self.versionObject['branch']
        elif branch is not None:
            
            self.set_branch(branch, project)
        else:
            self.set_branch("master", project)
            

    def set_branch(self, branch, project):

        if project is not None:
            if branch is None:
                branch = "master"
            q = {'project': project, 'branch': branch}
            result = self.db.query(q)
            versions =  list(json.loads(dumps(result)))
            if len(versions) > 0:
                self.version = versions[0]['version']
                self.project = versions[0]['project']
                self.branch = versions[0]['branch']


    def get_version_object(self, version):

        result = self.db.find_one(version)
        return result
    
    def get_branch_versions(self):

        q = {'project': self.project, 'branch': self.branch}
        result = self.db.query(q)
        return list(json.loads(dumps(result)))
    
    def create_new_version(self):
        latest_version = self.get_latest_version()
        if latest_version is not None:
            new_version = {'branch': latest_version['branch'], 'project': latest_version['project'], 'version': latest_version['version'] + 1}
            new_version_object = self.db.insert_one(new_version)
            return self.get_version_object(new_version_object)
        else:
            data = {'project': self.project, 'branch': self.branch, 'version': 0}
            return self.db.insert_one(data)
    
    def get_latest_version(self):
        versions = self.get_branch_versions()
        if len(versions) > 0:
            latest_version = versions[0]
            for v in versions:
                if v['version'] >= latest_version['version']:
                    latest_version = v
        else:
            latest_version = None
        return latest_version
    
    def get_version_id(self, version):

        return version['_id']['$oid']
    
    def get_previous_version(self, new_version):
        latest_version = self.get_latest_version()
        if latest_version['version'] == new_version['version']:
            if latest_version['version'] > 0:
                q = {'version': latest_version['version']-1, 'project': latest_version['project'], 'branch': latest_version['branch']}
                prev_version = self.db.query(q)
                if len(prev_version) >= 1:
                    return prev_version[0]
            else:
                return None
        else:
            return None

    def update_version_elements(self, new_version):
        prev_version = self.get_previous_version(new_version)
        if prev_version is not None:
            self.update_version("projects", prev_version ,new_version)

    def update_version_elementType(self, db_type, prev_version, new_version):
        self.db.define_collection(db_type)
        
        types = self.db.find({"version": ObjectId(prev_version['_id']['$oid'])})
        new_types = self.db.find({"version": ObjectId(new_version['_id']['$oid'])})
        for t in types:
            for nt in new_types:
                if t['id'] not in nt['id']:
                    t['version'].append(ObjectId(new_version['_id']['$oid']))
                    self.db.update_one(t['_id']['$oid'], t)
    
    def get_elements_query(self, version, storey=None):
        
        return 



