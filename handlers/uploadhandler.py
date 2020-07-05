# Handles file uploads in Python Tornado: http://tornadoweb.org/

import tornado.web
import logging
import os
import uuid
import json


class UploadHandler(tornado.web.RequestHandler):
    "Handle file uploads."

    def initialize(self, upload_path, naming_strategy):
        """Initialize with given upload path and naming strategy.
        :keyword upload_path: The upload path.
        :type upload_path: str
        """
        self.upload_path = upload_path

    def post(self):
        fileinfo = self.request.files['filearg'][0]
        filename = fileinfo['filename']
        print(self.get_body_argument("test", default=None, strip=False))
        try:
            with open(os.path.join(self.upload_path, filename), 'wb') as fh:
                fh.write(fileinfo['body'])
            logging.info("%s uploaded %s, saved as %s",
                         str(self.request.remote_ip),
                         str(fileinfo['filename']),
                         filename)
        except IOError as e:
            logging.error("Failed to write file due to IOError %s", str(e))
    
    def get(self):
        file_name = 'CP.txt'
        buf_size = 4096
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + file_name)
        file = open(os.path.join(self.upload_path, file_name), 'r')
        self.write(file.read()) 
        self.finish()

