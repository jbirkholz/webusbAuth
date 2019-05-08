"""
WebSocket Server relaying APDUs from virtual smart card reader (vpcd) via a virtual smartcard (vicc) to a WebSocket.

Upon WebSocket connection, the (websocket) client will be connected to vpcd, which allows a host applications to send APDUs (via PC/SC). From the client, a response APDU is expected as the answer.

Example exchange:
          WebSocket<--vicc<--vpcd<--app<--CAPDU
  RAPDU-->WebSocket-->vicc-->vpcd-->app

[SimpleWebSocketServer]: https://github.com/dpallot/simple-websocket-server
[vsmartcard]: https://github.com/frankmorgner/vsmartcard
[https://frankmorgner.github.io/vsmartcard/virtualsmartcard/api.html#virtualsmartcard-api]
[vsmartcard/virtualsmartcard/src/vpicc/virtualsmartcard]: https://github.com/frankmorgner/vsmartcard/tree/master/virtualsmartcard/src/vpicc/virtualsmartcard
"""
# support PEP 582 (draft) packages
import sys, os
packagePath = '__pypackages__/'+str(sys.version_info[0])+'.'+str(sys.version_info[1])+'/lib'
sys.path.insert(1,os.path.join(os.getcwd(),packagePath))

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket #python3 -m pip install git+https://github.com/dpallot/simple-websocket-server.git

# vsmartcard/virtualsmartcard/src/vpicc/virtualsmartcard folder in site-packages, __pypackages__, current directory, or somewhere in $PATH
from virtualsmartcard.VirtualSmartcard import SmartcardOS, Iso7816OS, VirtualICC #https://github.com/frankmorgner/vsmartcard/tree/master/virtualsmartcard/src/vpicc/virtualsmartcard
import threading

class VICCProxy(WebSocket):
    def handleMessage(self):
        if (type(self.data) is bytearray): #received apdu
            self.responseAPDU = self.data
            print(self.address,'received', ''.join('%02x ' % byte for byte in self.responseAPDU))
            self.workerEvent.set() #unblock worker

        # use string to start the worker and hand over control of the smartcard communication to it
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
        # vpcd is expected to be running on localhost:35963 and handing out CAPDUs (from an application)
        # "VirtualICC provides the connection to the virtual smart card reader. It fetches an APDU and other requests from the vpcd." [https://frankmorgner.github.io/vsmartcard/virtualsmartcard/api.html#virtualsmartcard-api]. App--vpcd--VirtualICC.
        vicc = VirtualICC(datasetfile=None, card_type='iso7816', host='localhost', port=35963)
        vicc.os = WebSocketOS(self, self.websocket)
        vicc.run()

    # send apdu to client and wait for answer apdu from it to return it
    def transceive(self,msg):
        self.websocket.sendMessage(msg)

        #block worker until websocket receives response
        self.websocket.workerEvent.wait()
        self.websocket.workerEvent.clear() #reset for next event in case of event reuse

        #get response from shared variable
        data = self.websocket.responseAPDU

        return data

# Implementation of a virtual smartcard, which relays all APDUs between vpcd and WebSocket (in this order).
# https://frankmorgner.github.io/vsmartcard/virtualsmartcard/api.html#implementing-an-other-type-of-card
class WebSocketOS(SmartcardOS):
    def __init__(self, worker, websocket):
        self.worker = worker
        self.websocket = websocket

    def getATR(self):
        return Iso7816OS.makeATR(directConvention=True)

    def execute(self, msg):
        print(self.websocket.address,'send ', ''.join('%02x ' % byte for byte in msg))
        return self.worker.transceive(msg)

server = SimpleWebSocketServer('', 8083, VICCProxy) #create WebSocket server from custom WebSocket instance, which handles all clients
server.serveforever()
