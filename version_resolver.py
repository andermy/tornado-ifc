#import mongo as m
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
import models as m

class VersionResolver():

    def __init__(self, version=None, branch=None, project=None, versionObject=None):
        self.version = None
        self.project = None
        self.branch = None
        self.versionObject = None
        if version is not None:
            self.version = version
            self.versionObject = self.get_version_object(version)
            self.branch = self.versionObject.branch
            self.project = self.versionObject.project
        elif versionObject is not None:
            self.versionObject = versionObject
            self.branch = versionObject.branch
            self.project = versionObject.project
        elif branch is not None:
            self.set_branch(branch, project)
        else:
            self.set_branch("master", project)
            

    def set_branch(self, branch, project):

        if project is not None:
            try:
                if branch is None:
                    branch = "master"
                project = m.Project.objects.get({'_id':ObjectId(project)})
                q = {'project': project.pk, 'branch': branch}
                
                versions =  m.Version.objects.raw(q)
                if versions.count() > 0:
                    self.version = versions.first()
                    self.project = versions.first().project
                    self.branch = versions.first().branch
            except:
                print("Project does not exist")


    def get_version_object(self, version):

        result = m.Version.objects.get({'_id':ObjectId(version)})
        return result
    
    def get_branch_versions(self):

        q = {'project': self.project.pk, 'branch': self.branch}
        result = m.Version.objects.raw(q)
        return result
    
    def create_new_version(self):
        latest_version = self.get_latest_version()
        if latest_version is not None:
            return m.Version(branch= latest_version.branch, project= latest_version.project, version= int(latest_version.version) + 1).save()
        else:
            return m.Version(branch= latest_version.branch, project= latest_version.project, version= 0).save()
            
    def get_latest_version(self):
        versions = self.get_branch_versions()
        if versions.count() > 0:
            latest_version = versions.first()
            for v in versions:
                if v.version >= latest_version.version:
                    latest_version = v
        else:
            latest_version = None
        return latest_version
    
    def get_version_id(self, version):

        return version['_id']['$oid']
    
    def get_previous_version(self):
        latest_version = self.get_latest_version()
        if latest_version is not None:
            q = {'version': latest_version.version-1, 'project': latest_version.project.pk, 'branch': latest_version.branch}
            prev_version = m.Version.objects.raw(q)
            if prev_version.count() >= 1:
                return prev_version.first()
        else:
            return None
        

    def update_version_elements(self, new_version):
        prev_version = self.get_previous_version(new_version)
        if prev_version is not None:
            print("figure this out in versionresoolver")
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
    



