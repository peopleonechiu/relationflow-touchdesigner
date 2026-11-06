"""Validation for a single-file YOLO26 end-to-end ONNX detector."""
import hashlib
import json
from pathlib import Path

MAX_MODEL_BYTES = 256 * 1024 * 1024
MAX_CLASSES_BYTES = 1024 * 1024

def inspect(model_path, classes_path, project_folder):
    def resolve(value):
        if not str(value).strip():
            raise ValueError('Select both ONNX and classes JSON files')
        path = Path(str(value)).expanduser()
        return (path if path.is_absolute() else Path(project_folder) / path).resolve()
    model, classes = resolve(model_path), resolve(classes_path)
    if model.suffix.lower() != '.onnx' or classes.suffix.lower() != '.json':
        raise ValueError('Choose one .onnx model and one .json class list')
    for path in (model, classes):
        if not path.is_file():
            raise ValueError('File not found: ' + path.name)
    ms, cs = model.stat(), classes.stat()
    if not 0 < ms.st_size <= MAX_MODEL_BYTES:
        raise ValueError('ONNX file must be between 1 byte and 256 MiB')
    if not 0 < cs.st_size <= MAX_CLASSES_BYTES:
        raise ValueError('Class list must be between 1 byte and 1 MiB')
    try:
        names = json.loads(classes.read_text(encoding='utf-8-sig'))
    except (ValueError, UnicodeError) as exc:
        raise ValueError('Class JSON must be a UTF-8 string array') from exc
    if (not isinstance(names, list) or not 1 <= len(names) <= 1000 or
        any(not isinstance(x, str) or not x.strip() or len(x.strip()) > 100 for x in names)):
        raise ValueError('Class JSON requires 1–1000 nonempty names, each at most 100 characters')
    names = [x.strip() for x in names]
    if len({x.casefold() for x in names}) != len(names):
        raise ValueError('Class names must be unique (ignoring case)')
    signature = hashlib.sha256((str(model)+'|'+str(ms.st_size)+'|'+str(ms.st_mtime_ns)+'|'+
                                str(classes)+'|'+str(cs.st_size)+'|'+str(cs.st_mtime_ns)).encode()).hexdigest()
    return {'model_path': str(model), 'classes_path': str(classes), 'names': names,
            'size': ms.st_size, 'revision': signature}
