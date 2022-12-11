import socket
import threading
import time
import sys
import json
from tkinter import Tk

from Server import Server
from Node import Node
from Client import Client


if __name__ == "__main__":

    if(len(sys.argv) == 5 and sys.argv[1] == 'server'):
        # python3 teste.py server <ip_server> config.json master 
        server = Server(True,sys.argv[2])
        server.run()

    elif(len(sys.argv) == 4 and sys.argv[1] == 'server'):
        # python3 teste.py server <ip_server> config.json 
        server = Server(False,sys.argv[2])
        server.run()

    elif(len(sys.argv) == 4 and sys.argv[1] == 'node'):
        # python3 teste.py node <ip_nodo> configNode.json
        node = Node(sys.argv[2],sys.argv[3])
        node.run()
    
    elif(len(sys.argv) == 4 and sys.argv[1] == 'client'):
        # python3 teste.py client <ip_client> <ip_nodo>
        client = Client(sys.argv[2],sys.argv[3])
        client.run()

