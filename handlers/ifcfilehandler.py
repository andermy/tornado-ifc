# Handles file uploads in Python Tornado: http://tornadoweb.org/

import tornado.web
import tornado.iostream
import logging
import os
import uuid
import json


class IfcFileHandler(tornado.web.RequestHandler):
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

class DownloadHandler(tornado.web.RequestHandler):
    async def get(self, filename):
        # chunk size to read
        chunk_size = 1024 * 1024 * 1 # 1 MiB

        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                try:
                    self.write(chunk) # write the chunk to response
                    await self.flush() # send the chunk to client
                except tornado.iostream.StreamClosedError:
                    # this means the client has closed the connection
                    # so break the loop
                    break
                finally:
                    # deleting the chunk is very important because 
                    # if many clients are downloading files at the 
                    # same time, the chunks in memory will keep 
                    # increasing and will eat up the RAM
                    del chunk