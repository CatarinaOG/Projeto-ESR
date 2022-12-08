import socket
import threading
import time
import sys
import json

class Client:

    clientAddress = ''
    clientPort = 3000

    nodeAddress = ''
    nodePort3 = 5000 




    def __init__(self,clientAddress,nodeAddress):
        self.clientAddress = clientAddress
        self.nodeAddress = nodeAddress

    def connectToNode(self,s):

        info = {
            "request" : "connect"
        }

        infoJSON = json.dumps(info)
        s.sendto(infoJSON.encode('utf-8'), (self.nodeAddress, self.nodePort3))
        print("hello")

    def run(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.clientAddress,self.clientPort))

        self.connectToNode(s)
