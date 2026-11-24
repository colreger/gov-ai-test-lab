"""Build an explicit allowlist ZIP for Python Lambda; no credentials or evidence."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'demo' / 'build' / 'govqa-demo.zip'

def build():
    files = {'handler.py': ROOT/'demo/aws/handler.py'}
    for name in ('__init__.py', 'assistant.py', 'models.py'):
        files['govqa/'+name] = ROOT/'govqa'/name
    for name in ('documents.json', 'cases.json'):
        files['data/'+name] = ROOT/'data'/name
    for path in (ROOT/'demo/web').iterdir():
        if path.suffix in ('.html','.css','.js'):
            files['web/'+path.name] = path
    OUT.parent.mkdir(exist_ok=True)
    with ZipFile(OUT,'w',ZIP_DEFLATED) as archive:
        for name,path in sorted(files.items()): archive.writestr(name,path.read_bytes())
    print(OUT)
    return OUT
if __name__ == '__main__': build()
