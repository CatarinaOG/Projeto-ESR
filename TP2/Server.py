
import socket
import threading
import time
import sys
import json

from VideoStream import VideoStream
from RtpPacket import RtpPacket

class Server:	

    nodePort1 = 3000
    nodePort2 = 4000

    serverAddress = ''
    serverPort1 = 3000
    serverPort2 = 4000
    serverPort3 = 5000
    serverPort4 = 6000
    serverPort5 = 7000

    filename = 'movie.Mjpeg'

    nodes_master = 0
    topology_master = {}
    isMaster = False
    servers = []
    best_routes_to_nodes = {}
    actives = []

    count = 0
    
    def __init__(self,isMaster,serverAddress):
        self.isMaster = isMaster
        self.serverAddress = serverAddress
        self.videoStream = VideoStream(self.filename)

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


    def sendMonitoring(self,s2):

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
                s2.sendto(infoJSON.encode('utf-8'), (nextHop, self.nodePort2))

            time.sleep(20)


    def updateEachActives(self,msg,add):

        info = json.loads(msg.decode('utf-8'))

        lock = threading.Lock()

        lock.acquire()
        self.actives.append(add[0])
        lock.release()



    def updateActives(self,s3):

        while(True):
            msg, add = s3.recvfrom(1024)
            threading.Thread(target=self.updateEachActives, args=(msg,add)).start()
    

    def makeRtp(self, payload, frameNbr):
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26 # MJPEG type
        seqnum = frameNbr
        ssrc = 0 
        
        rtpPacket = RtpPacket()
        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
        return rtpPacket.getPacket()


    def sendRtp(self):

        while True:

            data = self.videoStream.nextFrame()

            if data: 

                time.sleep(0.05)

                for neighbourActive in self.actives:
            
                    frameNumber = self.videoStream.frameNbr()

                    try:
                        self.rtpSocket.sendto(self.makeRtp(data, frameNumber),(neighbourActive,self.serverPort5))
                    except:
                        print("Connection Error")

            else : 
                self.videoStream = VideoStream(self.filename)

                    


    def sendMovie(self):

        while(True):
            if(len(self.actives) > 0):
                self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sendRtp()



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

        threading.Thread(target=self.sendMonitoring, args=(s2,)).start()
        threading.Thread(target=self.updateActives, args=(s3,)).start()
        threading.Thread(target=self.sendMovie, args=()).start()


        
