"""
WebSocket Server Relaying APDUs from virtual smart card reader to a websocket

Based on [SimpleWebSocketServer] and [vsmartcard].

Usage: upon WebSocket connection, the client will be connected to vpcd, which allows an host applications to send APDUs via PC/SC. From the client, an response APDU is expected as answer

[SimpleWebSocketServer]: https://github.com/dpallot/simple-websocket-server
[vsmartcard]: https://github.com/frankmorgner/vsmartcard
"""
import sys

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from virtualsmartcard.VirtualSmartcard import SmartcardOS, Iso7816OS, VirtualICC
import threading

class VICCProxy(WebSocket):
    def handleMessage(self):
        if (type(self.data) is bytearray): #received apdu
            self.responseAPDU = self.data
            self.workerEvent.set() #unblock worker

        if(type(self.data) is str): #received string
            print(self.address,'received', self.data)
            try: #use try-exception to have errors outputted to terminal
                self.workerEvent = threading.Event()
                workerThread = Worker(self) #starts automatically and does not block SimpleWebSocketServer
            except:
                print("Unexpected error:", sys.exc_info())
                raise

    def handleConnected(self):
        print(self.address, 'connected')

    def handleClose(self):
        print(self.address, 'closed')

class Worker:
    def __init__(self, websocket):
        self.websocket = websocket
        thread = threading.Thread(target=self.run, args=())
        thread.start()

    def run(self):
        # vpcd is expected to be running on localhost:35963
        vicc = VirtualICC(datasetfile=None, card_type='iso7816', host='localhost', port=35963)
        vicc.os = WebSocketOS(self)
        vicc.run()

    def transceive(self,msg):
        self.websocket.sendMessage(msg)

        #block worker until websocket receives response
        self.websocket.workerEvent.wait()
        self.websocket.workerEvent.clear() #reset for next event in case of event reuse

        #get response from shared variable
        data = self.websocket.responseAPDU

        return data

class WebSocketOS(SmartcardOS):
    def __init__(self, worker):
        self.worker = worker

    def getATR(self):
        return Iso7816OS.makeATR(directConvention=True)

    def execute(self, msg):
        return self.worker.transceive(msg)

server = SimpleWebSocketServer('', 8081, VICCProxy) #create WebSocket server from custom WebSocket instance, which handles all clients
server.serveforever()
