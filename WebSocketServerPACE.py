"""
WebSocket Server running Password Authenticated Connection Establishment (PACE) between nPA token and terminal

Based on [SimpleWebSocketServer] and [pypace].
Requires Python >= 3.6 and pip packages: pycryptodome, ecdsa, pytlv, git+https://github.com/dpallot/simple-websocket-server.git .
To enable SSL/TLS see [SimpleWebSocketServer].

Usage: upon WebSocket connection, the client is sent APDUs, to which an response APDU is expected as answer.

[SimpleWebSocketServer]: https://github.com/dpallot/simple-websocket-server
[pypace]: https://github.com/tsenger/pypace
"""
#python version check
from sys import version_info
import sys
if version_info[0] < 3 or (version_info[0] == 3 and version_info[1] < 6):
    raise Exception("Python >= 3.6 required.")

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import secrets #https://docs.python.org/3.6/library/secrets.html#module-secrets
import threading
import time
from Pace import Pace   #sudo python3.6 -m pip install pycryptodome
                        #sudo python3.6 -m pip install ecdsa
                        #sudo python3.6 -m pip install pytlv

class AuthenticationExample(WebSocket):
    def handleMessage(self):    #WebSocket session, included in self is automatically saved and loaded for each request
        self.responseAPDU = self.data
        print(self.address,'received', ''.join('%02x ' % byte for byte in self.responseAPDU))
        self.workerEvent.set() #unblock worker

    def handleConnected(self):
        print(self.address, 'connected')
        try: #use try-exception to have errors outputted to terminal
            self.workerEvent = threading.Event()
            workerThread = Worker(self) #starts automatically and does not block SimpleWebSocketServer
        except:
            print("Unexpected error:", sys.exc_info())
            raise

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
    def __init__(self, websocket):
        self.websocket = websocket
        thread = threading.Thread(target=self.run, args=())
        thread.start()

    def run(self):
        connection = Connection(self)
        pace_operator = Pace(connection)
        pw_ref   = 2 # CAN (password type)
        password = "123456" #6 digit CAN, printed in the bottom right of the nPA front
        pace_oid = [0x04, 0x00, 0x7f, 0x00, 0x07, 0x02, 0x02, 0x04, 0x02, 0x02] # PACE_ECDH_AES128
        chat = [0x06, 0x09, 0x04, 0x00, 0x7f, 0x00, 0x07, 0x03, 0x01, 0x02, 0x02, 0x53, 0x05, 0x3f, 0xff, 0xff, 0xff, 0xf7]
        pace_operator.performPACE(pace_oid, bytes(password,'ascii'), pw_ref, chat)

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
