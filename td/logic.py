import json
import re
import struct
import time
import numpy as np

state = {'connected': False, 'configured': False, 'busy': False, 'sent': 0.0,
         'last_result': 0.0, 'tags': (), 'last_frame': 0.0, 'config': None, 'tag_text': None}

def comp():
    return me.parent()

def table(name, rows):
    dat = comp().op(name)
    dat.clear()
    for row in rows:
        dat.appendRow(row)

def reset(status):
    state.update(connected=False, configured=False, busy=False, last_result=0.0, tags=(), config=None)
    table('table_relations', [['subject', 'relation', 'object', 'score']])
    table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']])
    table('table_status', [['status', 'inference_ms'], [status, 0]])
    scores({}, False)

def scores(values, valid):
    tags = [str(comp().op('table_tags')[i, 0]).strip() for i in range(1, comp().op('table_tags').numRows)]
    names, numbers, used = ['connected', 'result_valid'], [int(state['connected']), int(valid)], set(['connected', 'result_valid'])
    for i, tag in enumerate(tags):
        if not tag: continue
        name = re.sub(r'[^A-Za-z0-9_]+', '_', tag).strip('_').lower() or 'tag'
        if name[0].isdigit(): name = 'tag_' + name
        if name in used: name += '_' + str(i + 1)
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
        if typ == 'configured':
            state.update(configured=True, busy=False)
        elif typ == 'result':
            current_tags = tuple(t.strip() for t in str(comp().par.Tags.eval()).split(',') if t.strip())[:32]
            if not state['config'] or current_tags != state['config'][0]:
                state['busy'] = False
                return
            objects = {o['index']: o for o in data['objects']}
            table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']] +
                  [[o['index'], o['label'], o['score']] + o['box'] for o in data['objects']])
            rows, values = [['subject', 'relation', 'object', 'score', 'subject_index', 'object_index']], {}
            for r in data['relations']:
                a, b = objects.get(r['subject'], {}), objects.get(r['object'], {})
                rows.append([a.get('label', r['subject']), r['tag'], b.get('label', r['object']), r['score'], r['subject'], r['object']])
                values[r['tag']] = max(values.get(r['tag'], 0.0), r['score'])
            table('table_relations', rows)
            state.update(busy=False, last_result=time.monotonic())
            table('table_status', [['status', 'inference_ms'], ['running', data.get('inference_ms', 0)]])
            scores(values, True)
        elif typ == 'error':
            state.update(busy=False, configured=False)
            table('table_status', [['status', 'inference_ms'], [data.get('message', 'error'), 0]])
            scores({}, False)
    except Exception as exc:
        state.update(busy=False, configured=False)
        table('table_status', [['status', 'inference_ms'], [str(exc), 0]])

def tick():
    now = time.monotonic()
    text = str(comp().par.Tags.eval())
    if text != state['tag_text']:
        tags = [t.strip() for t in text.split(',') if t.strip()][:32]
        table('table_tags', [['tag']] + [[t] for t in tags])
        state['tag_text'] = text
        state['last_result'] = 0
        table('table_relations', [['subject', 'relation', 'object', 'score', 'subject_index', 'object_index']])
        table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']])
        scores({}, False)
    if state['last_result'] and now - state['last_result'] > float(comp().par.Stale):
        state['last_result'] = 0
        table('table_relations', [['subject', 'relation', 'object', 'score']])
        table('table_objects', [['index', 'label', 'score', 'x1', 'y1', 'x2', 'y2']])
        scores({}, False)
    if not state['connected']: return
    if state['busy']:
        if now - state['sent'] > 30:
            reset('request timed out; reconnect')
        return
    tags = tuple(str(comp().op('table_tags')[i, 0]).strip() for i in range(1, comp().op('table_tags').numRows))
    tags = tuple(t for t in tags if t)
    if not tags:
        scores({}, False)
        return
    ws = comp().op('websocket_service')
    config = (tags[:32], float(comp().par.Confidence), int(comp().par.Maxobjects))
    if config != state['config'] or not state['configured']:
        ws.sendText(json.dumps({'type': 'config', 'tags': list(config[0]), 'confidence': config[1], 'max_boxes': config[2]}))
        state.update(tags=tags, config=config, busy=True, sent=now, configured=False)
        return
    if now - state['last_frame'] < 1.0 / max(float(comp().par.Fps), 0.1): return
    source = comp().op('resolution_inference')
    if source.width < 2 or source.height < 2: return
    pixels = source.numpyArray(delayed=True)
    if pixels is None: return
    rgb = np.ascontiguousarray((np.clip(pixels[::-1, :, :3], 0, 1) * 255).astype(np.uint8))
    height, width = rgb.shape[:2]
    ws.sendBinary(b'TDR1' + struct.pack('>II', width, height) + rgb.tobytes())
    state.update(busy=True, sent=now, last_frame=now)
