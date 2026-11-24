"""Exercise the exact upload ZIP in an isolated Python process."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]

class DemoPackageTests(unittest.TestCase):
    def test_packaged_cases_and_http_contract(self):
        subprocess.run([sys.executable,'demo/build.py'],cwd=ROOT,check=True,capture_output=True)
        with tempfile.TemporaryDirectory() as directory:
            with ZipFile(ROOT/'demo/build/govqa-demo.zip') as archive:
                self.assertTrue(all(not name.endswith('.pyc') for name in archive.namelist()))
                archive.extractall(directory)
            code='''
import json
from handler import lambda_handler, CASES, DOCUMENTS
from govqa.assistant import FALLBACK
def request(method,path,body=None,**kwargs):
 return lambda_handler(dict(rawPath=path,requestContext={'http':{'method':method}},body=body,**kwargs),None)
assert set(DOCUMENTS)=={'bree','hobbiton','rivendell'}
assert len(CASES)==50
for case in CASES.values():
 response=request('POST','/ask',json.dumps({'case_id':case['id']}))
 assert response['statusCode']==200
 answer=json.loads(response['body'])['answer']
 if case['source']:
  assert answer['status']=='answered'
  assert answer['source']==case['source']
  assert answer['topic']==case['topic']
  assert answer['text']==DOCUMENTS[case['source']]['facts'][case['topic']]
 else:
  assert answer['status']=='abstained' and answer['text']==FALLBACK
for payload in ('null','[]','{}','{"case_id":1}','{"case_id":"missing"}','{"case_id":"04","question":"injected"}','x'*257):
 assert request('POST','/ask',payload)['statusCode']==400
assert request('POST','/ask','{}',isBase64Encoded=True)['statusCode']==400
assert request('GET','/ask')['statusCode']==405
assert request('GET','/missing')['statusCode']==404
for asset in ('/','/app.js','/style.css','/cases'):
 assert request('GET',asset)['statusCode']==200
print('50 renamed cases, invalid inputs and assets passed')
'''
            subprocess.run([sys.executable,'-I','-c',"import sys;sys.path.insert(0,sys.argv[1]);exec(sys.argv[2])",directory,code],check=True,capture_output=True,text=True)
