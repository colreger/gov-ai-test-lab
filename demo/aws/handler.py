"""Dependency-free Lambda handler. Only versioned, fictional cases are accepted."""
import json
from dataclasses import asdict
from pathlib import Path
from govqa.assistant import Assistant
from govqa.models import FixtureModel

ROOT = Path(__file__).resolve().parent
NAMES = {'lindenfeld': 'bree', 'birkenau': 'hobbiton', 'auenbrueck': 'rivendell'}
LABELS = {'Lindenfeld': 'Bree', 'Birkenau': 'Hobbiton', 'Auenbrück': 'Rivendell', 'Neustadt': 'Minas Tirith'}


def renamed(value):
    if isinstance(value, str):
        if value in NAMES:
            return NAMES[value]
        for old, new in LABELS.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [renamed(v) for v in value]
    if isinstance(value, dict):
        return {k: renamed(v) for k, v in value.items()}
    return value


DOCUMENTS = {d['id']: d for d in renamed(json.loads((ROOT / 'data/documents.json').read_text()))}
CASES = {c['id']: c for c in renamed(json.loads((ROOT / 'data/cases.json').read_text()))}


def response(status, value, content_type='application/json; charset=utf-8'):
    return {'statusCode': status, 'headers': {'Content-Type': content_type,
            'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'"},
            'body': value if content_type != 'application/json; charset=utf-8' else json.dumps(value, ensure_ascii=False)}


def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '/')
    if method == 'GET' and path in ('/', '/app.js', '/style.css'):
        filename, mime = {'/': ('index.html', 'text/html; charset=utf-8'),
                          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                          '/style.css': ('style.css', 'text/css; charset=utf-8')}[path]
        return response(200, (ROOT / 'web' / filename).read_text(), mime)
    if method == 'GET' and path == '/cases':
        return response(200, {'mode': 'deterministic_fixture', 'cases': [{'id': c['id'], 'question': c['question']} for c in CASES.values()]})
    if path != '/ask':
        return response(404, {'error': 'Not found'})
    if method != 'POST':
        return response(405, {'error': 'Use POST'})
    body = event.get('body')
    if event.get('isBase64Encoded') or not isinstance(body, str) or len(body.encode('utf-8')) > 256:
        return response(400, {'error': 'Send a small JSON object containing case_id.'})
    try:
        payload = json.loads(body)
        if not isinstance(payload, dict) or set(payload) != {'case_id'} or not isinstance(payload['case_id'], str):
            raise ValueError()
        case = CASES[payload['case_id']]
    except (ValueError, KeyError):
        return response(400, {'error': 'Choose a published case_id.'})
    assistant = Assistant(FixtureModel(), documents=DOCUMENTS)
    answer = assistant.ask(case['question'])
    return response(200, {'mode': 'deterministic_fixture', 'fictional': True,
        'question': case['question'], 'answer': asdict(answer), 'routing': assistant.last_diagnostic,
        'notice': 'Fiktive Testdaten. Vorprogrammiertes Testmodell; kein Aufruf eines Sprachmodells.'})
