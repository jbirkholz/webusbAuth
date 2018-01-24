#python version check
from sys import version_info
if version_info[0] < 3:
    raise Exception("Python >= 3.6 required.")

#simple HTTP server, equal to /usr/bin/python3 -m http.server 8000
ssl = False     #generate certificate:
                #   openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
                #server.pem then also contains the private key, which should be protected
import http.server
import socketserver
import os

os.chdir(os.getcwd()+'/src')

httpServer = socketserver.TCPServer(("",8000),http.server.SimpleHTTPRequestHandler)
if ssl:
    import ssl
    httpServer.socket = ssl.wrap_socket (httpServer.socket, certfile='../server.pem', server_side=True)
httpServer.serve_forever()
