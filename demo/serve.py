"""Loopback-only preview of the packaged Lambda handler."""
import importlib
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from zipfile import ZipFile
from build import build

folder=tempfile.TemporaryDirectory(prefix='govqa-demo-')
with ZipFile(build()) as archive: archive.extractall(folder.name)
sys.path.insert(0, folder.name)
handler=importlib.import_module('handler').lambda_handler

class Preview(BaseHTTPRequestHandler):
    def serve(self):
        size=int(self.headers.get('Content-Length','0'))
        if size>256:
            self.send_error(413); return
        event={'rawPath': self.path.split('?')[0], 'requestContext':{'http':{'method':self.command}},
               'body':self.rfile.read(size).decode('utf-8',errors='replace') if size else None}
        response=handler(event,None)
        self.send_response(response['statusCode'])
        for k,v in response['headers'].items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(response['body'].encode())
    do_GET=serve
    do_POST=serve
    def log_message(self,*args): pass

print('Preview: http://127.0.0.1:8082',flush=True)
HTTPServer(('127.0.0.1',8082),Preview).serve_forever()
