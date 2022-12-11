import socket
import threading
import time
import sys
import json

class Node:	

    serverAddress = ''
    serverPort1 = 3000
    serverPort2 = 4000
    serverPort4 = 6000

    nodePort1 = 3000
    nodePort2 = 4000
    nodePort3 = 5000
    nodePort4 = 6000
    nodePort5 = 7000


    myNeighbours = []
    ipNode = ''
    bestRoutes = {}
    neighboursFlood = []
    serversNode = []
    bestServer = {}
    configFile = ''

    actives = []
    isActive = False
    count = 0


    
    def __init__(self,ipNode,configFile):
        self.configFile = configFile
        self.ipNode = ipNode


    def getNeighbours(self,s):

        msg = 'neighbours'
        s.sendto(msg.encode('utf-8'), (self.serverAddress, self.serverPort1))
        
        answer, server_add = s.recvfrom(1024)

        return json.loads(answer.decode('utf-8'))['neighbours']


    def getNodeName(self,add):

        if (add == '10.0.3.1'): return "N2"
        elif(add == '10.0.6.2'): return "N3"
        elif(add == '10.0.5.1'): return "N1"
        elif(add == '10.0.3.10'): return "S1"
        elif(add == '10.0.7.10'): return "S2"
        elif(add == '10.0.2.2'): return "N4"

        #if (add == '10.0.2.10'): return "S1"
        #elif(add == '10.0.2.1'): return "N1"
        #elif(add == '10.0.1.1'): return "N2"


        

    def getNodeNameInList(self,lista):

        newlist = []

        for i in range(len(lista)):
            newlist.append(self.getNodeName(lista[i]))

        return newlist


    def updateBestRoutes(self,info):

        info['depth'] += 1
        info['totalDelay'] += time.time() - info['startTime']
        info['startTime'] = time.time()

        server = info['server']

        if (server not in self.bestRoutes.keys()):
            info['route'].append(self.ipNode)
            self.bestRoutes[server] = info
            self.bestRoutes[server]['from'] = self.ipNode
            return True

        elif (self.bestRoutes[server]['totalDelay'] > info['totalDelay']):
            info['route'].append(self.ipNode)
            self.bestRoutes[server] = info
            self.bestRoutes[server]['from'] = self.ipNode
            return True
        
        return False


    def continueEachFlood(self,msg : bytes, add : tuple, s : socket.socket, lock : threading.Lock):

        changed = False
        lock.acquire()
        info = json.loads(msg.decode('utf-8'))
        changed = self.updateBestRoutes(info)

        if(changed):
            for neighbour in self.myNeighbours:
                if(neighbour != add[0]):

                    infoJSON = json.dumps(self.bestRoutes[info['server']])
                    s.sendto(infoJSON.encode('utf-8'), (neighbour, self.nodePort1))

        lock.release()



    def continueFlood(self,s,s1):

        lock = threading.Lock()
        s.settimeout(3)#7

        try:
            while(True):
                msg, add = s.recvfrom(1024)
                threading.Thread(target=self.continueEachFlood, args=(msg,add,s,lock)).start()
        except socket.timeout as e:
            self.sendBackFlood(s1)
            
            


    def sendBackFlood(self,s):

        for server in self.bestRoutes:
            infoJSON = json.dumps(self.bestRoutes[server])
            s.sendto(infoJSON.encode('utf-8'), (server, self.serverPort2))


    def getServers(self):

        with open(self.configFile) as json_file:
            file = json.load(json_file)
            return file['servers']


    def continueEachMonitoring(self,msg,s1,s3,lock):

        info = json.loads(msg.decode('utf-8'))

        if(len(info['path']) > 1):
            info['path'].pop(0)
            nextHop = info['path'][0]        
            infoJSON = json.dumps(info)
            s1.sendto(infoJSON.encode('utf-8'), (nextHop, self.nodePort2))
        
        else:
            lock.acquire()
            info["totalDelay"] = time.time() - info["startTime"]

            

            
            if(not self.bestServer):
                self.bestServer['server'] = info['server']
                self.bestServer['delay'] = info['totalDelay']
                self.bestServer['depth'] = info['depth']

            else:
                print("old: ",self.bestServer['delay'], "de ",self.bestServer['server'])
                print("novo: ",info['totalDelay'], "de ",info['server'])
                if(self.bestServer['delay'] == info['totalDelay']):
                    if(self.bestServer['depth'] >= info['depth']):
                        oldBestServer = self.bestServer['server'] 
                        self.bestServer['server'] = info['server']
                        self.bestServer['delay'] = info['totalDelay']
                        self.bestServer['depth'] = info['depth']

                        if(self.isActive):
                            print("enviei active e inactive")
                            self.sendActive(s3)
                            self.sendInactive(s3,oldBestServer)

                else:
                    if(self.bestServer['delay'] > info['totalDelay']):
                        oldBestServer = self.bestServer['server'] 
                        self.bestServer['server'] = info['server']
                        self.bestServer['delay'] = info['totalDelay']
                        self.bestServer['depth'] = info['depth']

                        if(self.isActive):
                            print("enviei active e inactive")
                            self.sendActive(s3)
                            self.sendInactive(s3,oldBestServer)

            lock.release()



    def continueMonitoring(self,s1,s3):

        lock = threading.Lock()

        while(True):
            msg, add = s1.recvfrom(1024)
            threading.Thread(target=self.continueEachMonitoring, args=(msg,s1,s3,lock)).start()



    def sendActive(self,s3):

        bestRouteCopy = list(self.bestRoutes[self.bestServer['server']]['route'])
        bestRouteCopy.pop()

        info = {
            "route" : bestRouteCopy,
            "type": "active",
            "nodeActive" : self.ipNode
        }

        send = json.dumps(info)
        last = len(bestRouteCopy) - 1

        s3.sendto(send.encode('utf-8'), (bestRouteCopy[last], self.nodePort4))
        print("enviei active")




    def sendInactive(self,s3,oldBestServer):

        bestRouteCopy = list(self.bestRoutes[oldBestServer]['route'])
        bestRouteCopy.pop()

        info = {
            "route" : bestRouteCopy,
            "type": "diactivate",
            "nodeActive" : self.ipNode
        }

        send = json.dumps(info)
        last = len(bestRouteCopy) - 1

        s3.sendto(send.encode('utf-8'), (bestRouteCopy[last], self.nodePort4))
        print("enviei inactive")



    def connectEachClient(self,msg,add,s3):

        info = json.loads(msg.decode('utf-8'))

        lock = threading.Lock()

        lock.acquire()

        if(not self.isActive):
            self.isActive = True
            self.sendActive(s3)

        if(add[0] not in self.actives):
            self.actives.append(add[0])
        
        lock.release()




    def connectClients(self,s2,s3):

        while(True):
            msg, add = s2.recvfrom(1024)
            threading.Thread(target=self.connectEachClient, args=(msg,add,s3)).start()
            


    def continueEachSendActive(self,msg,add,s3):

        lock = threading.Lock()

        info = json.loads(msg.decode('utf-8'))
        info["route"].pop()

        lock.acquire()

        if(info["type"] == 'active'):
            self.isActive = True
            self.actives.append(add[0])

            last = len(info["route"]) - 1
            send = json.dumps(info)
            s3.sendto(send.encode('utf-8'), (info["route"][last], self.nodePort4))
            print("adicionei-me")

        else:
            self.actives.remove(add[0])

            if(len(self.actives) == 0):
                self.isActive = False
                last = len(info["route"]) - 1
                send = json.dumps(info)
                s3.sendto(send.encode('utf-8'), (info["route"][last], self.nodePort4))
                print("Tambem me removi")
        
        lock.release()


        


    def continueSendActive(self,s3):

        while(True):
            msg,add = s3.recvfrom(1024)
            threading.Thread(target=self.continueEachSendActive, args=(msg,add,s3)).start()


    def receiveEachPacketMovie(self,s4,msg):

        self.count += 1

        for dest in self.actives:
            s4.sendto(msg,(dest,self.nodePort5))


    def receiveMovie(self,s4):

        while(True):
            msg,add = s4.recvfrom(20480)
            threading.Thread(target=self.receiveEachPacketMovie, args=(s4,msg)).start()




    def run(self):


        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.ipNode, self.nodePort1))

        s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s1.bind((self.ipNode, self.nodePort2))

        s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s2.bind((self.ipNode, self.nodePort3))

        s3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s3.bind((self.ipNode, self.nodePort4))

        s4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s4.bind((self.ipNode, self.nodePort5))

        self.serversNode = self.getServers()
        self.serverAddress = self.serversNode[0]
        self.myNeighbours = self.getNeighbours(s)

        self.continueFlood(s,s1)

        threading.Thread(target=self.continueMonitoring, args=(s1,s3)).start()
        threading.Thread(target=self.continueSendActive, args=(s3,)).start()
        threading.Thread(target=self.connectClients, args=(s2,s3)).start()
        threading.Thread(target=self.receiveMovie, args=(s4,)).start()

