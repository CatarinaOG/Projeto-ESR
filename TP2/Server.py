
import socket
import threading
import time
import sys
import json

class Server:	

    nodePort1 = 3000
    nodePort2 = 4000

    serverAddress = ''
    serverPort1 = 3000
    serverPort2 = 4000
    serverPort3 = 5000
    serverPort4 = 6000

    nodes_master = 0
    topology_master = {}
    isMaster = False
    servers = []
    best_routes_to_nodes = {}
    
    def __init__(self,isMaster,serverAddress):
        self.isMaster = isMaster
        self.serverAddress = serverAddress

    def getTopology(self):

        with open(sys.argv[3]) as json_file:
            file = json.load(json_file)
            self.servers = file['servers']
            self.topology_master = file['neighbours']

        for key in self.topology_master:
            self.nodes_master += 1

        self.nodes_master -= 1 + len(self.servers)



    def sendEachNeighbours(self,s : socket, msg : bytes, add : tuple):
        
        if(msg.decode('utf-8') == "neighbours"):

            response = self.topology_master[add[0]]
            
            info = {
                'ip' : add[0],
                'neighbours' : response
            }

            send=json.dumps(info)
            s.sendto(send.encode('utf-8'), add)



    def sendNeighbours(self,s):

        nodes = 0

        while nodes < self.nodes_master:
            msg, add = s.recvfrom(1024)
            threading.Thread(target=self.sendEachNeighbours, args=(s, msg, add)).start()
            nodes += 1



    def flood(self,s):

        neighbours = self.topology_master[self.serverAddress]

        info = {
            "server" : self.serverAddress,
            "from" : self.serverAddress,
            "depth" : 0,
            "startTime" : time.time(),
            "totalDelay" : 0,
            "route" : [self.serverAddress]
        }


        for neighbour in neighbours:
            infoJSON = json.dumps(info)
            
            s.sendto(infoJSON.encode('utf-8'), (neighbour, self.nodePort1))



    def notifyOtherServers(self,s):

        for server in self.servers:
            s.sendto("start".encode('utf-8'), (server, self.serverPort1))


    def getEachFloodBack(self,msg,add):
        
        self.best_routes_to_nodes[add[0]] = json.loads(msg.decode('utf-8'))


    def getFloodBack(self,s):

        nodes = 0
        
        while nodes < self.nodes_master:
            print(nodes)
            msg, add = s.recvfrom(1024)
            threading.Thread(target=self.getEachFloodBack, args=(msg,add)).start()
            nodes += 1


    def sendMonitoring(self,s):

        while(True):

            time.sleep(2)#5
            print("send monitoring")

            for node in self.best_routes_to_nodes:
                copy_routes = list(self.best_routes_to_nodes[node]['route'])
                copy_routes.pop(0)

                info = {
                    "server" : self.serverAddress,
                    "depth" : len(copy_routes),
                    "startTime" : time.time(),
                    "totalDelay" : 0,
                    "route" : self.best_routes_to_nodes[node]['route'],
                    "path" : copy_routes
                }

                nextHop = copy_routes[0]
                infoJSON = json.dumps(info)
                s.sendto(infoJSON.encode('utf-8'), (nextHop, self.nodePort2))

            time.sleep(20)

    def updateActives():
        print("hello")

    def run(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.serverAddress, self.serverPort1))

        s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s1.bind((self.serverAddress, self.serverPort2))

        s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s2.bind((self.serverAddress, self.serverPort3))
        
        s3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s3.bind((self.serverAddress, self.serverPort4))

        self.getTopology()

        if(self.isMaster):
            self.sendNeighbours(s)
            self.notifyOtherServers(s)
        else:
            msg, add = s.recvfrom(1024)
        
        time.sleep(1) # necessário para cada nodo ler os seus vizinhos e preparar a socket

        self.flood(s)
        self.getFloodBack(s1) # necessário outra porta por alguma razão...

        threading.Thread(target=self.sendMonitoring(s2), args=(msg,add)).start()
        threading.Thread(target=self.updateActives(s3), args=(msg,add)).start()

        
