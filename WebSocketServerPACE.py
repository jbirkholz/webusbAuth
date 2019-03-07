"""
WebSocket Server running Password Authenticated Connection Establishment (PACE) between nPA token and terminal

Based on [SimpleWebSocketServer] and [pypace].
Requires Python(3) and pip packages: pycryptodome, ecdsa, pytlv, git+https://github.com/dpallot/simple-websocket-server.git .
To enable SSL/TLS see [SimpleWebSocketServer] and update wss:// url in demo.html.

Usage: upon WebSocket connection, the client is sent APDUs, to which an response APDU is expected as answer.

[SimpleWebSocketServer]: https://github.com/dpallot/simple-websocket-server
[pypace]: https://github.com/tsenger/pypace
"""
import sys

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import threading
import time
from Pace import Pace   #python3 -m pip install pycryptodome
                        #python3 -m pip install ecdsa
                        #python3 -m pip install pytlv

class AuthenticationExample(WebSocket):
    def handleMessage(self):    #WebSocket session, included in self is automatically saved and loaded for each request
        if(type(self.data) is bytearray): #received apdu
            self.responseAPDU = self.data
            print(self.address,'received', ''.join('%02x ' % byte for byte in self.responseAPDU))
            self.workerEvent.set() #unblock worker

        if(type(self.data) is str): #received CAN string
            can = self.data
            print(self.address,'received', self.data)
            try: #use try-exception to have errors outputted to terminal
                self.workerEvent = threading.Event()
                workerThread = Worker(self,can) #starts automatically and does not block SimpleWebSocketServer
            except:
                print("Unexpected error:", sys.exc_info())
                raise


    def handleConnected(self):
        print(self.address, 'connected')

    def handleClose(self):
        print(self.address, 'closed')

#pyscard compatible Connection, supporting only transmit
class Connection:
    def __init__(self,worker):
        self.worker = worker
    def transmit(self,msg):
        responseAPDU = self.worker.transceive(msg)
        data = list(responseAPDU[0:len(responseAPDU)-2])
        sw1 = responseAPDU[len(responseAPDU)-2]
        sw2 = responseAPDU[len(responseAPDU)-1]
        return data, sw1, sw2

#event and shared variable synchronized worker
class Worker:
    def __init__(self, websocket, can):
        self.websocket = websocket
        self.can = can
        thread = threading.Thread(target=self.run, args=())
        thread.start()

    def run(self):
        connection = Connection(self)
        pace_operator = Pace(connection)

        # we arbitrarily chose authentication by CAN and PACE-ECDH-GM-AES-CBC-CMAC-128 algorithms; and provide a terminal/pcd auth template.
        pw_ref   = 2 # CAN (password type)
        password = self.can #6 digit CAN, printed in the bottom right of the nPA front
        pace_oid = [0x04, 0x00, 0x7f, 0x00, 0x07, 0x02, 0x02, 0x04, 0x02, 0x02] # PACE_ECDH_AES128, algorithm object identifier (oid) see http://oid-info.com/get/0.4.0.127.0.7.2.2.4.2.2=id-PACE-ECDH-GM-AES-CBC-CMAC-128 (BSI-TR-03110-3) p.46 https://www.bsi.bund.de/EN/Publications/TechnicalGuidelines/TR03110/BSITR03110-eIDAS_Token_Specification.html, part 2
        #GM~Generic Mapping (GM) based on a Diffie-Hellman Key Agreement (no extra fields included as in IM/CAM) [http://static.javadoc.io/org.jmrtd/jmrtd/0.6.4/org/jmrtd/protocol/PACEProtocol.html]
        chat = [0x06, 0x09, 0x04, 0x00, 0x7f, 0x00, 0x07, 0x03, 0x01, 0x02, 0x02, 0x53, 0x05, 0x3f, 0xff, 0xff, 0xff, 0xf7] #Certificate Holder Authorization Template (CHAT)
        try:
            paceResult = pace_operator.performPACE(pace_oid, bytes(password,'ascii'), pw_ref, chat)
            self.websocket.sendMessage(str(paceResult))
        except:
            self.websocket.sendMessage("-1") #already established PACE causes exception

    def transceive(self,msg):
        self.websocket.sendMessage(msg)

        #block worker until websocket receives response
        self.websocket.workerEvent.wait()
        self.websocket.workerEvent.clear() #reset for next event in case of event reuse

        #get response from shared variable
        data = self.websocket.responseAPDU

        return data

server = SimpleWebSocketServer('', 8081, AuthenticationExample) #create WebSocket server from custom WebSocket instance, which handles all clients
server.serveforever()
