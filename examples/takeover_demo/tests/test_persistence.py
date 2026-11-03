"""Acceptance contract kept unchanged throughout the demonstration."""

import io
import json
from pathlib import Path
import tempfile
import unittest

from app import make_app


def request(app, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else b''
    result = {}

    def respond(status, headers):
        result['status'] = int(status.split()[0])

    payload = b''.join(app({'REQUEST_METHOD': method, 'PATH_INFO': path,
                           'CONTENT_LENGTH': str(len(data)), 'wsgi.input': io.BytesIO(data)}, respond))
    return result['status'], json.loads(payload)


class PersistenceTests(unittest.TestCase):
    def test_successful_save_survives_new_app_instance(self):
        with tempfile.TemporaryDirectory() as folder:
            storage = Path(folder) / 'items.json'
            status, created = request(make_app(storage), 'POST', '/items', {'title': 'Synthetic example'})
            self.assertEqual(status, 201)
            status, loaded = request(make_app(storage), 'GET', '/items')
            self.assertEqual(status, 200)
            self.assertEqual(loaded['items'], [created], 'A successful save must survive a new app instance')

    def test_invalid_title_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            status, _ = request(make_app(Path(folder) / 'items.json'), 'POST', '/items', {'title': ''})
            self.assertEqual(status, 400)

    def test_unknown_route_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            status, _ = request(make_app(Path(folder) / 'items.json'), 'GET', '/missing')
            self.assertEqual(status, 404)
