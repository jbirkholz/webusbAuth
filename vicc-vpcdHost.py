"""
Example Virtual Smart Card Reader aka Virtual Proximity Coupling Device (vpcd) application to run the WebSocketServerVICC example.

  It waits for a socket connecting virtual smart card aka Virtual Integrated Circuit Card (vicc) and sends a GET_CHALLENGE(1) CAPDU (command application protocol data unit).

  Example exchange:
          vicc<--vpcd<--app<--CAPDU
  RAPDU-->vicc-->vpcd-->app

[https://frankmorgner.github.io/vsmartcard/virtualsmartcard/api.html#virtualsmartcard-api]
"""
import socket
import threading

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(('', 35963)) #35963
s.listen()

def clienthandler(conn,addr):
    # CAPDU = 2 Bytes apdu length (bigendian), and following apdu. Apdu is an extended length get_challenge expecting one random byte in the respose apdu (RAPDU).
    apdu = bytearray([0x00,0x07,0x00,0x84,0x00,0x00,0x00,0x00,0x01])
    conn.sendall(apdu)
    print(addr[0], ':', str(addr[1]),' sent: ',''.join('%02x ' % byte for byte in apdu))
    receivedBytes = conn.recv(4096)
    print(addr[0], ':', str(addr[1]),' received: ', ''.join('%02x ' % byte for byte in receivedBytes))
    conn.close()

while 1: # all connections are taken within this main thread and then handled by a new thread each
    conn, addr = s.accept()
    print('client '+addr[0] + ':' + str(addr[1]))
    threading.Thread(target=clienthandler, args=(conn,addr)).start()

s.close()
