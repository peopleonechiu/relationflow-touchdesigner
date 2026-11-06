import json
import re
import struct
import time
import numpy as np

state = {'connected': False, 'configured': False, 'busy': False, 'sent': 0.0, 'inference_ms': 0.0,
         'last_result': 0.0, 'tags': (), 'last_frame': 0.0, 'config': None, 'tag_text': None, 'initialized': False}

OBJECT_CLASSES = ('person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush')

client = None

def set_client(value):
    global client
    client = value

def comp():
    return me.parent()

def table(name, rows):
    dat = comp().op(name)
    dat.clear()
    for row in rows:
        dat.appendRow(row)

def parse_tags(text):
    raw = [part.strip() for part in text.split(',') if part.strip()]
    seen, tags, duplicate = set(), [], False
    for tag in raw:
        if len(tag) > 100:
            return (), 'Each tag must be at most 100 characters'
        if tag.casefold() in seen:
            duplicate = True
            continue
        seen.add(tag.casefold())
        tags.append(tag)
    if not tags:
        return (), 'Enter at least one English relation tag'
    if len(tags) > 32:
        return (), 'Use at most 32 different tags'
    return tuple(tags), ('Duplicate tags removed' if duplicate else 'Tags OK')

def parse_objects(text, classes=OBJECT_CLASSES):
    allowed = {x.casefold(): x for x in classes}
    found, unknown = [], []
    for name in (x.strip().casefold() for x in text.split(',')):
        if not name: continue
        if name not in allowed:
            if name not in unknown: unknown.append(name)
        elif allowed[name] not in found:
            found.append(allowed[name])
    if unknown:
        return (), 'Unknown YOLO class: ' + ', '.join(unknown[:3])
    if not found:
        return (), 'Enter at least one YOLO class'
    if len(found) > 20:
        return (), 'Use at most 20 classes'
    return tuple(found), 'Objects OK'

def available_objects():
    detector = str(comp().par.Detector.eval())
    if detector == 'yolo26n':
        built_in = OBJECT_CLASSES
    else:
        if 'wide_classes' not in state:
            raw = comp().vfs['models/yoloe-11s-pf.classes.json'].byteArray
            state['wide_classes'] = tuple(json.loads(bytes(raw).decode('utf-8')))
        built_in = state['wide_classes']
    desc = state.get('custom_desc')
    return tuple(built_in) + tuple(desc['names']) if desc else built_in

def refresh_custom(now):
    enabled = bool(comp().par.Customenable.eval())
    model = str(comp().par.Custommodel.eval())
    classes = str(comp().par.Customclasses.eval())
    key = (enabled, model, classes)
    if key == state.get('custom_key') and now - state.get('custom_checked', 0) < 1:
        return
    state['custom_checked'] = now
    state['custom_key'] = key
    old = state.get('custom_desc')
    try:
        desc = comp().op('custom_model').module.inspect(model, classes, project.folder) if enabled else None
        error = ''
    except Exception as exc:
        desc = None
        error = str(exc)
    old_revision = old['revision'] if old else None
    revision = desc['revision'] if desc else None
    state['custom_desc'] = desc
    state['custom_error'] = error
    if old_revision != revision:
        state['custom_ready'] = False
        state['object_text'] = None
        state.update(last_result=0.0, last_objects=[])
        raw_result()
        scores({}, False)
        object_scores([], 1, 1, False)
    if error:
        table('table_custom_status', [['status'], [error]])
    elif not enabled:
        table('table_custom_status', [['status'], ['Disabled']])
    elif revision != old_revision:
        table('table_custom_status', [['status'], ['Loading model']])

def object_scores(objects, width, height, valid):
    names, values = ['objects_valid', 'custom_ready'], [int(valid), int(bool(state.get('custom_ready')))]
    used = set()
    selected, _ = parse_objects(str(comp().par.Objectclasses.eval()), available_objects())
    for label in selected:
        key = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_') or 'class'
        if key[0].isdigit(): key = 'class_' + key
        base, suffix = key, 2
        while key in used:
            key, suffix = base + '_' + str(suffix), suffix + 1
        used.add(key)
        matches = [o for o in objects if o['label'].lower() == label.lower()] if valid else []
        best = max(matches, key=lambda o: o['score']) if matches else None
        box = best['box'] if best else [0, 0, 0, 0]
        names.extend([key+'_count', key+'_confidence', key+'_x', key+'_y', key+'_width', key+'_height'])
        values.extend([len(matches), best['score'] if best else 0,
                       (box[0]+box[2])/(2*max(width,1)), (box[1]+box[3])/(2*max(height,1)),
                       (box[2]-box[0])/max(width,1), (box[3]-box[1])/max(height,1)])
    table('table_object_channels', [names, values])

def raw_result(data=None):
    if data is None:
        payload = {'result_valid': False, 'objects': [], 'relations': []}
    else:
        width, height = max(1, data['width']), max(1, data['height'])
        objects = []
        for obj in data['objects']:
            x1, y1, x2, y2 = obj['box']
            objects.append({'index': obj['index'], 'label': obj['label'], 'confidence': obj['score'],
                            'source': obj.get('source', 'builtin'),
                            'box_pixels': obj['box'], 'center_x': (x1+x2)/(2*width),
                            'center_y': (y1+y2)/(2*height), 'width': (x2-x1)/width,
                            'height': (y2-y1)/height, 'z': None})
        payload = {'result_valid': True, 'received_unix': time.time(), 'width': width, 'height': height,
                   'inference_ms': data.get('inference_ms', 0), 'objects': objects, 'relations': data['relations']}
    comp().op('raw_data').text = json.dumps(payload, ensure_ascii=False)

def reset(status):
    state.update(connected=False, configured=False, busy=False, last_result=0.0, tags=(), config=None, inference_ms=0.0)
    state['custom_ready'] = False
    raw_result()
    table('table_relations', [['subject', 'relation', 'object', 'score']])
    table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']])
    table('table_status', [['status', 'inference_ms'], [status, 0]])
    scores({}, False)
    state.update(last_objects=[], frame_width=1, frame_height=1)
    object_scores([], 1, 1, False)

def scores(values, valid):
    tags = [str(comp().op('table_tags')[i, 0]).strip() for i in range(1, comp().op('table_tags').numRows)]
    names, numbers, used = ['connected', 'result_valid', 'inference_ms'], [int(state['connected']), int(valid), state['inference_ms'] if valid else 0.0], set(['connected', 'result_valid', 'inference_ms'])
    for i, tag in enumerate(tags):
        if not tag: continue
        name = re.sub(r'[^A-Za-z0-9_]+', '_', tag).strip('_').lower() or 'tag'
        if name[0].isdigit(): name = 'tag_' + name
        base = name
        suffix = 2
        while name in used:
            name = base + '_' + str(suffix)
            suffix += 1
        used.add(name); names.append(name); numbers.append(values.get(tag, 0.0))
    table('table_scores', [names, numbers])

def connected():
    state.update(connected=True, configured=False, busy=False, tags=())
    table('table_status', [['status', 'inference_ms'], ['connected', 0]])
    scores({}, False)

def receive(message):
    try:
        data = json.loads(message)
        typ = data.get('type')
        if typ == 'loading':
            table('table_status', [['status', 'inference_ms'], [data.get('message', 'loading'), 0]])
        elif typ == 'custom_status':
            state['custom_ready'] = bool(data.get('ok'))
            table('table_custom_status', [['status'], [data.get('message', '')]])
            object_scores(state.get('last_objects', []), state.get('frame_width', 1),
                          state.get('frame_height', 1), bool(state['last_result']))
        elif typ == 'configured':
            state.update(configured=True, busy=False, pending_config=False)
        elif typ == 'result':
            current_tags, _ = parse_tags(str(comp().par.Tags.eval()))
            current_custom = (bool(comp().par.Customenable.eval()),
                              str(comp().par.Custommodel.eval()), str(comp().par.Customclasses.eval()))
            if (not state['config'] or current_tags != state['config'][0]
                    or str(comp().par.Detector.eval()) != state['config'][4]
                    or current_custom != state.get('custom_key')):
                state['busy'] = False
                return
            raw_result(data)
            state.update(last_objects=data['objects'], frame_width=data['width'], frame_height=data['height'])
            object_scores(data['objects'], data['width'], data['height'], True)
            objects = {o['index']: o for o in data['objects']}
            table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']] +
                  [[o['index'], o['label'], o['score']] + o['box'] for o in data['objects']])
            rows, values = [['subject', 'relation', 'object', 'score', 'subject_index', 'object_index']], {}
            for r in data['relations']:
                a, b = objects.get(r['subject'], {}), objects.get(r['object'], {})
                rows.append([a.get('label', r['subject']), r['tag'], b.get('label', r['object']), r['score'], r['subject'], r['object']])
                values[r['tag']] = max(values.get(r['tag'], 0.0), r['score'])
            table('table_relations', rows)
            state.update(busy=False, last_result=time.monotonic(), inference_ms=float(data.get('inference_ms', 0)))
            table('table_status', [['status', 'inference_ms'], ['running', data.get('inference_ms', 0)]])
            scores(values, True)
        elif typ == 'error':
            state.update(busy=False, configured=False, pending_config=False, last_result=0.0, last_objects=[])
            raw_result()
            object_scores([], 1, 1, False)
            table('table_status', [['status', 'inference_ms'], [data.get('message', 'error'), 0]])
            scores({}, False)
    except Exception as exc:
        state.update(busy=False, configured=False)
        table('table_status', [['status', 'inference_ms'], [str(exc), 0]])

def tick():
    if not state['initialized']:
        reset('loading')
        state['initialized'] = True
    now = time.monotonic()
    if comp().par.Run.eval() and client is None and now - state.get('last_reload', 0) > 5:
        state['last_reload'] = now
        comp().op('browser_runtime').par.reload.pulse()
    refresh_custom(now)
    custom_desc = state.get('custom_desc')
    object_text = (str(comp().par.Objectclasses.eval()) + '\n' + str(comp().par.Detector.eval()) +
                   '\n' + (custom_desc['revision'] if custom_desc else ''))
    if object_text != state.get('object_text'):
        detector = str(comp().par.Detector.eval())
        if state.get('detector_selection') not in (None, detector):
            state.update(last_result=0.0, last_objects=[])
            raw_result()
            scores({}, False)
            table('table_relations', [['subject', 'relation', 'object', 'score', 'subject_index', 'object_index']])
            table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']])
        state['detector_selection'] = detector
        _, objstatus = parse_objects(str(comp().par.Objectclasses.eval()), available_objects())
        table('table_object_status', [['status'], [objstatus]])
        state['object_text'] = object_text
        object_scores(state.get('last_objects', []), state.get('frame_width', 1), state.get('frame_height', 1), bool(state['last_result']))
    text = str(comp().par.Tags.eval())
    if text != state['tag_text']:
        tags, tag_status = parse_tags(text)
        table('table_tags', [['tag']] + [[t] for t in tags])
        table('table_tag_status', [['status'], [tag_status]])
        state['tag_text'] = text
        state['last_result'] = 0
        raw_result()
        table('table_relations', [['subject', 'relation', 'object', 'score', 'subject_index', 'object_index']])
        table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']])
        scores({}, False)
        state['last_objects'] = []
        object_scores([], 1, 1, False)
    if state['last_result'] and now - state['last_result'] > float(comp().par.Stale):
        state['last_result'] = 0
        raw_result()
        table('table_relations', [['subject', 'relation', 'object', 'score']])
        table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']])
        scores({}, False)
        state['last_objects'] = []
        object_scores([], 1, 1, False)
    if not state['connected']: return
    if state['busy']:
        timeout = 180 if state.get('pending_config') else 30
        if now - state['sent'] > timeout:
            reset('request timed out; reconnect')
        return
    tags = tuple(str(comp().op('table_tags')[i, 0]).strip() for i in range(1, comp().op('table_tags').numRows))
    tags = tuple(t for t in tags if t)
    if not tags:
        state['configured'] = False
        scores({}, False)
        return
    ws = comp().op('webserver_browser')
    if client is None: return
    config = (tags[:32], float(comp().par.Confidence), int(comp().par.Maxobjects),
              float(comp().par.Overlaythreshold), str(comp().par.Detector.eval()),
              custom_desc['revision'] if custom_desc else '', float(comp().par.Customconfidence),
              float(comp().par.Custommerge))
    if config != state['config'] or not state['configured']:
        custom = {'enabled': bool(custom_desc), 'confidence': config[6], 'merge_iou': config[7]}
        if custom_desc:
            custom.update(revision=custom_desc['revision'], size=custom_desc['size'], classes=custom_desc['names'])
        ws.webSocketSendText(client, json.dumps({'type': 'config', 'tags': list(config[0]), 'confidence': config[1], 'max_boxes': config[2], 'overlay_threshold': config[3], 'detector': config[4], 'custom': custom}))
        state.update(tags=tags, config=config, busy=True, pending_config=True, sent=now, configured=False)
        return
    if now - state['last_frame'] < 1.0 / max(float(comp().par.Fps), 0.1): return
    source = comp().op('resolution_inference')
    if source.width < 2 or source.height < 2: return
    pixels = source.numpyArray(delayed=True)
    if pixels is None: return
    rgb = np.ascontiguousarray((np.clip(pixels[::-1, :, :3], 0, 1) * 255).astype(np.uint8))
    height, width = rgb.shape[:2]
    ws.webSocketSendBinary(client, b'TDR1' + struct.pack('>II', width, height) + rgb.tobytes())
    state.update(busy=True, sent=now, last_frame=now)
