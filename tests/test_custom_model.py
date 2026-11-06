import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('custom_model', Path(__file__).resolve().parents[1] / 'td' / 'custom_model.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)

class CustomModelTest(unittest.TestCase):
    def test_valid_paths_and_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'model.onnx').write_bytes(b'model')
            (root / 'classes.json').write_text(json.dumps(['cup', 'device']))
            data = model.inspect('model.onnx', 'classes.json', root)
            self.assertEqual(data['names'], ['cup', 'device'])
            self.assertEqual(data['size'], 5)
            (root / 'classes.json').write_text(json.dumps(['cup', 'another']))
            self.assertNotEqual(data['revision'], model.inspect('model.onnx', 'classes.json', root)['revision'])

    def test_rejects_bad_labels_and_wrong_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'model.onnx').write_bytes(b'model')
            (root / 'classes.json').write_text('["Cup", "cup"]')
            with self.assertRaises(ValueError): model.inspect('model.onnx', 'classes.json', root)
            with self.assertRaises(ValueError): model.inspect('model.pt', 'classes.json', root)
