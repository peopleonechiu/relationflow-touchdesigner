import importlib.util
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('callbacks', Path(__file__).resolve().parents[1] / 'td' / 'browser_server_callbacks.py')
callbacks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(callbacks)

class File:
    byteArray = bytearray(b'content')
class Component:
    vfs = {'vendor/runtime.mjs': File(), 'vendor/runtime.wasm': File(), 'index.html': File()}

class BrowserMimeTest(TestCase):
    def test_browser_assets_have_stable_mime_types_across_platforms(self):
        callbacks.parent = lambda: Component()
        with patch.object(callbacks.mimetypes, 'guess_type', return_value=('text/plain', None)):
            for filename, expected in [('vendor/runtime.mjs','application/javascript'),('vendor/runtime.wasm','application/wasm'),('index.html','text/html')]:
                response = callbacks.onHTTPRequest(None, {'uri':'/'+filename}, {})
                self.assertEqual(response['statusCode'], 200)
                self.assertEqual(response['content-type'], expected)
