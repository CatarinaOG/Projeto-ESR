import socket
import threading
import time
import sys
import json


# ----- Master Globals ------

serverAddress = ''
serverPort1 = 3000
serverPort2 = 4000
serverPort3 = 5000
nodes_master = 0
topology_master = {}
isMaster = False
servers = []
best_routes_to_nodes = {}


# ------ Node Globals ------

nodePort1 = 3000
nodePort2 = 4000
nodePort3 = 5000

myNeighbours = []
ip_node = ''
best_routes = {}
neighboursFlood = []
serversNode = []
bestServer = {}


# ------- Client Globals ---------

nodeAddress = ''

#-----------------------------Master------------------------------------


def getTopology():
    global topology_master
    global nodes_master
    global servers

    with open(sys.argv[3]) as json_file:
        file = json.load(json_file)
        servers = file['servers']
        topology_master = file['neighbours']

    for key in topology_master:
        nodes_master += 1

    nodes_master -= 1 + len(servers)



def sendEachNeighbours(s : socket, msg : bytes, add : tuple):
    
    global topology_master

    if(msg.decode('utf-8') == "neighbours"):

        response = topology_master[add[0]]
        
        info = {
            'ip' : add[0],
            'neighbours' : response
        }

        send=json.dumps(info)
        s.sendto(send.encode('utf-8'), add)



def sendNeighbours(s):

    global nodes_master
    nodes = 0

    while nodes < nodes_master:
        msg, add = s.recvfrom(1024)
        threading.Thread(target=sendEachNeighbours, args=(s, msg, add)).start()
        nodes += 1



def flood(s):
    neighbours = topology_master[serverAddress]

    info = {
        "server" : serverAddress,
        "from" : serverAddress,
        "depth" : 0,
        "startTime" : time.time(),
        "totalDelay" : 0,
        "route" : [serverAddress]
    }


    for neighbour in neighbours:
        infoJSON = json.dumps(info)
        
        #print("-----------------------------------")
        #print('Eviei para ' + getNodeName(neighbour))
        #print("-----------------------------------")

        s.sendto(infoJSON.encode('utf-8'), (neighbour, nodePort1))



def notifyOtherServers(s):

    for server in servers:
        s.sendto("start".encode('utf-8'), (server, serverPort1))


def getEachFloodBack(msg,add):
    
    global best_routes_to_nodes
    best_routes_to_nodes[add[0]] = json.loads(msg.decode('utf-8'))


def getFloodBack(s):

    global nodes_master
    nodes = 0
    
    while nodes < nodes_master:
        msg, add = s.recvfrom(1024)
        threading.Thread(target=getEachFloodBack, args=(msg,add)).start()
        nodes += 1


def sendMonitoring(s):

    global serverAddress
    global nodePort2
    global best_routes_to_nodes

    while(True):

        time.sleep(5)

        for node in best_routes_to_nodes:
            copy_routes = list(best_routes_to_nodes[node]['route'])
            copy_routes.pop(0)

            info = {
                "server" : serverAddress,
                "depth" : len(copy_routes),
                "startTime" : time.time(),
                "totalDelay" : 0,
                "route" : best_routes_to_nodes[node]['route'],
                "path" : copy_routes
            }

            nextHop = copy_routes[0]
            infoJSON = json.dumps(info)
            s.sendto(infoJSON.encode('utf-8'), (nextHop, nodePort2))

        time.sleep(20)



def server():

    global serverAddress
    global serverPort1
    global serverPort2
    global serverPort3


    serverAddress = sys.argv[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((serverAddress, serverPort1))

    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s1.bind((serverAddress, serverPort2))

    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s2.bind((serverAddress, serverPort3))
    
    getTopology()

    if(isMaster):
        sendNeighbours(s)
        notifyOtherServers(s)
    else:
        msg, add = s.recvfrom(1024) # espera pelo sinal do master para continuar
    
    time.sleep(1) # necessário para cada nodo ler os seus vizinhos e preparar a socket

    flood(s)
    getFloodBack(s1) # necessário outra porta por alguma razão...

    #meter numa thread
    sendMonitoring(s2)
    




#------------------------------Node + client---------------------------------

def getNeighbours(s):

    msg = 'neighbours'
    s.sendto(msg.encode('utf-8'), (serverAddress, serverPort1))
    
    answer, server_add = s.recvfrom(1024)

    return json.loads(answer.decode('utf-8'))['neighbours']



#----------------------------------Node--------------------------------

def getNodeName(add):

    if (add == '10.0.3.1'): return "N2"
    elif(add == '10.0.6.2'): return "N3"
    elif(add == '10.0.5.1'): return "N1"
    elif(add == '10.0.3.10'): return "S1"
    elif(add == '10.0.7.10'): return "S2"
    elif(add == '10.0.2.2'): return "N4"

    

def getNodeNameInList(lista):

    newlist = []

    for i in range(len(lista)):
        newlist.append(getNodeName(lista[i]))

    return newlist


def updateBestRoutes(info):

    global best_routes
    global ip_node

    info['depth'] += 1
    info['totalDelay'] += time.time() - info['startTime']
    info['startTime'] = time.time()

    server = info['server']

    if (server not in best_routes.keys()):
        info['route'].append(ip_node)
        best_routes[server] = info
        best_routes[server]['from'] = ip_node
        return True

    elif (best_routes[server]['totalDelay'] > info['totalDelay']):
        info['route'].append(ip_node)
        best_routes[server] = info
        best_routes[server]['from'] = ip_node
        return True
    
    return False


def continueEachFlood(msg : bytes, add : tuple, s : socket.socket, lock : threading.Lock):

    global myNeighbours

    changed = False
    lock.acquire()
    info = json.loads(msg.decode('utf-8'))
    changed = updateBestRoutes(info)

    if(changed):
        for neighbour in myNeighbours:
            if(neighbour != add[0]):

                infoJSON = json.dumps(best_routes[info['server']])
                s.sendto(infoJSON.encode('utf-8'), (neighbour, nodePort1))

    lock.release()

    for r in best_routes:
        print("BEST ROUTES ",getNodeName(r),": ", getNodeNameInList(best_routes[r]['route']))



def continueFlood(s):

    global ip_node

    lock = threading.Lock()
    
    while(True): # resolver como parar isto...
        msg, add = s.recvfrom(1024)
        threading.Thread(target=continueEachFlood, args=(msg,add,s,lock)).start()
        


def sendBackFlood(s):

    global best_routes
    global serverPort2

    for server in best_routes:
        infoJSON = json.dumps(best_routes[server])
        s.sendto(infoJSON.encode('utf-8'), (server, serverPort2))


def getServers():

    with open(sys.argv[3]) as json_file:
        file = json.load(json_file)
        return file['servers']


def continueEachMonitoring(msg,s,lock):

    global nodePort2
    global bestServer

    info = json.loads(msg.decode('utf-8'))

    if(len(info['path']) > 1):
        info['path'].pop(0)
        nextHop = info['path'][0]        
        infoJSON = json.dumps(info)
        s.sendto(infoJSON.encode('utf-8'), (nextHop, nodePort2))
    
    else:
        lock.acquire()
        info["totalDelay"] = time.time() - info["startTime"]
        
        if(not bestServer):
            bestServer['server'] = info['server']
            bestServer['delay'] = info['totalDelay']
            bestServer['depth'] = info['depth']

        else:
            if(bestServer['delay'] == info['totalDelay']):
                if(bestServer['depth'] >= info['depth']):
                    bestServer['server'] = info['server']
                    bestServer['delay'] = info['totalDelay']
                    bestServer['depth'] = info['depth']
            else:
                if(bestServer['delay'] > info['totalDelay']):
                    bestServer['server'] = info['server']
                    bestServer['delay'] = info['totalDelay']
                    bestServer['depth'] = info['depth']

        lock.release()
        print("BestServer: ",bestServer)



def continueMonitoring(s):

    lock = threading.Lock()

    while(True):
        msg, add = s.recvfrom(1024)
        threading.Thread(target=continueEachMonitoring, args=(msg,s,lock)).start()


def connectEachClient(msg,add,s,lock):

    global bestServer

    info = json.loads(msg.decode('utf-8'))
    print("connect from",add)
    print("bestServer: ",bestServer)



def connectClients(s):

    lock = threading.Lock()

    while(True):
        msg, add = s.recvfrom(1024)
        threading.Thread(target=connectEachClient, args=(msg,add,s,lock)).start()




def node():

    global serverAddress
    global serversNode
    global ip_node
    global myNeighbours
    global nodePort1
    global nodePort2
    global nodePort3


    ip_node = sys.argv[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((ip_node, nodePort1))

    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s1.bind((ip_node, nodePort2))

    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s2.bind((ip_node, nodePort3))

    serversNode = getServers()
    serverAddress = serversNode[0]
    myNeighbours = getNeighbours(s)

    threading.Thread(target=continueFlood, args=(s,)).start()
    time.sleep(5) # para tentar tirar...
    sendBackFlood(s1)

    threading.Thread(target=continueMonitoring, args=(s1,)).start()
    threading.Thread(target=connectClients, args=(s2,)).start()


def connectToNode():

    global nodeAddress
    global nodePort3


    nodeAddress = sys.argv[2]

    info = {
        "request" : "connect"
    }

    infoJSON = json.dumps(info)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(infoJSON.encode('utf-8'), (nodeAddress, nodePort3))

    

def client():

    connectToNode()
   



#---------------------------------Main----------------------------------

if __name__ == "__main__":

    if(len(sys.argv) == 5 and sys.argv[1] == 'server'):
        # python3 teste.py server <ip_server> config.json master 
        isMaster = True
        server()

    elif(len(sys.argv) == 4 and sys.argv[1] == 'server'):
        # python3 teste.py server <ip_server> config.json 
        server()

    elif(len(sys.argv) == 4 and sys.argv[1] == 'node'):
        # python3 teste.py node <ip_nodo> configNode.json
        node()
    
    elif(len(sys.argv) == 3 and sys.argv[1] == 'client'):
        # python3 teste.py client <ip_nodo>
        client()

#----------------------------------------------------------