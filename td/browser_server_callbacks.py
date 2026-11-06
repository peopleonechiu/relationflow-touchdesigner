import mimetypes
from pathlib import Path

def onHTTPRequest(dat, request, response):
    name = request['uri'].split('?', 1)[0].lstrip('/') or 'index.html'
    try:
        if name == 'custom/model.onnx':
            logic = parent().op('logic').module
            desc = logic.state.get('custom_desc')
            if not parent().par.Customenable.eval() or not desc:
                raise FileNotFoundError(name)
            current = parent().op('custom_model').module.inspect(
                parent().par.Custommodel.eval(), parent().par.Customclasses.eval(), project.folder)
            if current['revision'] != desc['revision']:
                raise ValueError('Custom files changed during load; retry')
            data = Path(desc['model_path']).read_bytes()
        else:
            data = parent().vfs[name].byteArray
        response['statusCode'] = 200
        response['statusReason'] = 'OK'
        response['content-type'] = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response['data'] = data
    except Exception:
        response['statusCode'] = 404
        response['statusReason'] = 'Not Found'
        response['data'] = 'Not Found'
    return response

def onWebSocketOpen(dat, client, uri):
    parent().op('logic').module.set_client(client)

def onWebSocketClose(dat, client):
    parent().op('logic').module.set_client(None)
    parent().op('logic').module.reset('disconnected')

def onWebSocketReceiveText(dat, client, data):
    import json
    logic = parent().op('logic').module
    if json.loads(data).get('type') == 'ready': logic.connected()
    else: logic.receive(data)

def onWebSocketReceiveBinary(dat, client, data): pass

def onWebSocketReceivePing(dat, client, data): dat.webSocketSendPong(client, data=data)
def onWebSocketReceivePong(dat, client, data): pass
def onServerStart(dat): pass
def onServerStop(dat): pass
