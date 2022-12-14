import socket
import threading
import time
import sys
import json
from tkinter import Tk


from ClientStream import ClientStream

class Client:

    clientAddress = ''
    clientPort = 3000


    nodeAddress = ''
    nodePort3 = 5000 
    nodePort5 = 7000


    def __init__(self,clientAddress,nodeAddress):
        self.clientAddress = clientAddress
        self.nodeAddress = nodeAddress

    def connectToNode(self,s):

        info = {
            "request" : "connect"
        }

        infoJSON = json.dumps(info)
        s.sendto(infoJSON.encode('utf-8'), (self.nodeAddress, self.nodePort3))


    def run(self):
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.clientAddress,self.clientPort))

        self.connectToNode(s)

        root = Tk()
        clientStream = ClientStream(root,self.clientAddress,self.nodePort5,self.nodeAddress)
        root.mainloop()
        


