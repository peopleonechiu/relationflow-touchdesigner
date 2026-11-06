def onConnect(dat):
    parent().op('logic').module.connected()

def onDisconnect(dat):
    parent().op('logic').module.reset('disconnected')

def onReceiveText(dat, rowIndex, message):
    parent().op('logic').module.receive(message)

def onReceiveBinary(dat, contents):
    pass

def onReceivePing(dat, contents):
    dat.sendPong(contents)

def onReceivePong(dat, contents):
    pass

def onMonitorMessage(dat, message):
    pass
