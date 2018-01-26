"""
WebSocket based authentication server example (SimpleWebSocketServer) for Python >= 3.6
- install using 'python3.6 -m pip install git+https://github.com/dpallot/simple-websocket-server.git'
- use SSL/TLS as descibed at https://github.com/dpallot/simple-websocket-server and update wss:// url in demo.html
"""
#python version check
from sys import version_info
if version_info[0] < 3 or (version_info[0] == 3 and version_info[1] < 6):
    raise Exception("Python >= 3.6 required.")

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import secrets #https://docs.python.org/3.6/library/secrets.html#module-secrets

class AuthenticationExample(WebSocket):
    def handleMessage(self):    #WebSocket session, included in self is automatically saved and loaded for each request
        myChallenge = self.authentication.get('challenge')
        responseAPDU = self.data
        responseData = responseAPDU[0:len(responseAPDU)-2]
        responseStatus = responseAPDU[len(responseAPDU)-2:len(responseAPDU)]
        print(self.address,'received', ''.join('%02x ' % byte for byte in responseAPDU))

        #check response APDU
        if responseStatus[0] == 0x90 and responseStatus[1] == 0x00:
            #print('check challenge\'s response')

            #calculate expected response result from challenge. Often a hash function is used.
            expectedResponse = bytearray(myChallenge)
            #for i in range(6) #debug length fill to match size
            #    expectedResponse.append(0x00)

            #compare expected response to received response data
            success = False
            if len(responseData) == len(expectedResponse):
                #compare each byte
                byteEqual = False
                for index, responseByte in enumerate(responseData):
                    if responseByte == expectedResponse[index] and byteEqual == True:
                        byteEqual = True
                    else:
                        byteEqual = False
                if byteEqual == True:
                    success = True

            if success == True:
                print(self.address,'authentication successful')
            else:
                print(self.address,'authentication failed')

        else:
            print(self.address,'Error handling, authentication failed.')

    def handleConnected(self):
        print(self.address, 'connected')

        #WebSocket server controls client communication
        #example challenge
        challenge = secrets.token_bytes(16)

        #build authentication APDU
        #as an example ISO 7816-4 INTERNAL AUTHENTICATE is used [CLA,INS,P1,P2,Lc,Data,Le]
        CLA = 0x00
        INS = 0x88
        P1 = 0x00
        P2 = 0x00
        Lc = 0x10
        Data = challenge
        Le = 0x00
        byteArray = bytearray([]) #append to byteArray
        byteArray.append(CLA)
        byteArray.append(INS)
        byteArray.append(P1)
        byteArray.append(P2)
        byteArray.append(Lc)
        for byte in Data:
            byteArray.append(byte)
        byteArray.append(Le)

        #send APDU
        self.sendMessage(byteArray)

        #save challenge in WebSocket session
        self.authentication = {'challenge': Data}

    def handleClose(self):
        print(self.address, 'closed')

server = SimpleWebSocketServer('', 8081, AuthenticationExample) #create WebSocket server from custom WebSocket instance, which handles all clients
server.serveforever()
