"""
Example WebSocket Server sending a GET_CHALLENGE(1) CAPDU.

- use SSL/TLS as descibed at https://github.com/dpallot/simple-websocket-server and update wss:// url in demo.html
"""
# support PEP 582 (draft) packages
import sys, os
packagePath = '__pypackages__/'+str(sys.version_info[0])+'.'+str(sys.version_info[1])+'/lib'
sys.path.insert(1,os.path.join(os.getcwd(),packagePath))

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket #python3 -m pip install git+https://github.com/dpallot/simple-websocket-server.git
import threading

class APDUExample(WebSocket):
    def handleMessage(self):    #WebSocket session, included in self is automatically saved and loaded for each request
        # bytearray is defined as received RAPDU
        if(type(self.data) is bytearray):
            self.responseAPDU = self.data
            print(self.address,'received: ', ''.join('%02x ' % byte for byte in self.responseAPDU))
            self.workerEvent.set() #unblock worker

        # string is used to initiate CAPDU sending
        if(type(self.data) is str):
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


#event and shared variable synchronized worker
class Worker:
    def __init__(self, websocket):
        self.websocket = websocket
        thread = threading.Thread(target=self.run, args=())
        thread.start()

    def run(self):
        apdu = bytearray([0x00,0x84,0x00,0x00,0x00,0x00,0x01])
        print(self.websocket.address,'send: ',''.join('%02x ' % byte for byte in apdu))
        responseAPDU = self.transceive(apdu)

    def transceive(self,msg):
        self.websocket.sendMessage(msg)

        #block worker until websocket receives response
        self.websocket.workerEvent.wait()
        self.websocket.workerEvent.clear() #reset for next event in case of event reuse

        #get response from shared variable
        data = self.websocket.responseAPDU

        return data

server = SimpleWebSocketServer('', 8082, APDUExample) #create WebSocket server from custom WebSocket instance, which handles all clients
server.serveforever()
