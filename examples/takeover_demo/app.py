"""Deliberately broken WSGI fixture. Synthetic data only; not a production app."""

import json
from pathlib import Path


def make_app(storage):
    storage = Path(storage)

    def application(environ, start_response):
        status, payload = '404 Not Found', {'error': 'not found'}
        if environ.get('PATH_INFO') == '/items':
            method = environ.get('REQUEST_METHOD')
            items = json.loads(storage.read_text()) if storage.exists() else []
            if method == 'GET':
                status, payload = '200 OK', {'items': items}
            elif method == 'POST':
                try:
                    length = int(environ.get('CONTENT_LENGTH', '0'))
                    if not 0 < length <= 4096:
                        raise ValueError('invalid body length')
                    body = json.loads(environ['wsgi.input'].read(length))
                    title = body.get('title') if isinstance(body, dict) else None
                    if not isinstance(title, str) or not title.strip() or len(title) > 100:
                        raise ValueError('title is required')
                except (ValueError, UnicodeError):
                    status, payload = '400 Bad Request', {'error': 'invalid title or JSON'}
                else:
                    item = {'id': len(items) + 1, 'title': title.strip()}
                    items.append(item)
                    # Intentional fixture defect: the successful write is never persisted.
                    status, payload = '201 Created', item
        data = json.dumps(payload).encode()
        start_response(status, [('Content-Type', 'application/json'), ('Content-Length', str(len(data)))])
        return [data]

    return application
