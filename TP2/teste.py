import socket
import threading
import time
import sys
import json


# ----- Master Globals ------

serverAddress = ''
serverPort1 = 3000
serverPort2 = 4000
nodes_master = 0
topology_master = {}
isMaster = False
servers = []
best_routes_to_nodes = {}


# ------ Node Globals ------

nodePort1 = 3000
nodePort2 = 4000
myNeighbours = []
ip_node = ''
best_routes = {}
neighboursFlood = []
servers_node = []

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
        "type" : 'update',
        "server" : serverAddress,
        "from" : serverAddress,
        "depth" : 0,
        "start_time" : time.time(),
        "totalDelay" : 0,
        "route" : [serverAddress]
    }


    for neighbour in neighbours:
        infoJSON = json.dumps(info)
        s.sendto(infoJSON.encode('utf-8'), (neighbour, nodePort1))



def notifyOtherServers(s):

    for server in servers:
        s.sendto("start".encode('utf-8'), (server, serverPort1))


def getEachFloodBack(msg,add):
    
    global best_routes_to_nodes
    best_routes_to_nodes[add] = json.loads(msg.decode('utf-8'))
    print("recebi flood: ",best_routes_to_nodes[add]['route'])


def getFloodBack(s):

    global nodes_master
    nodes = 0
    
    while nodes < nodes_master:
        msg, add = s.recvfrom(1024)
        threading.Thread(target=getEachFloodBack, args=(msg,add)).start()
        nodes += 1
        print(nodes)



def server():

    global serverAddress
    global serverPort1
    global serverPort2
    serverAddress = sys.argv[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((serverAddress, serverPort1))

    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s1.bind((serverAddress, serverPort2))
    
    getTopology()

    if(isMaster):
        sendNeighbours(s)
        notifyOtherServers(s)
    else:
        msg, add = s.recvfrom(1024) # espera pelo sinal do master para continuar
    
    time.sleep(1) # necessário para cada nodo ler os seus vizinhos e preparar a socket
    flood(s)
    getFloodBack(s1)




#------------------------------Node + client---------------------------------

def getNeighbours(s):

    msg = 'neighbours'
    s.sendto(msg.encode('utf-8'), (serverAddress, serverPort1))
    
    answer, server_add = s.recvfrom(1024)

    return json.loads(answer.decode('utf-8'))['neighbours']



#----------------------------------Node--------------------------------

def getNodeName(add):

    if (add == '10.0.3.1'): return "N2"
    elif(add == '10.0.2.1'): return "N3"
    elif(add == '10.0.5.1'): return "N1"
    elif(add == '10.0.3.10'): return "S1"
    elif(add == '10.0.2.10'): return "S2"
    elif(add == '10.0.6.2'): return "N4"

    

def getNodeNameInList(lista):

    newlist = []

    for i in range(len(lista)):
        newlist.append(getNodeName(lista[i]))

    return newlist


def updateBestRoutes(info):

    global best_routes
    global ip_node

    info['depth'] += 1
    info['totalDelay'] += time.time() - info['start_time']
    info['start_time'] = time.time()

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

    print("-----------------------------------")
    print('Recebi de ' + getNodeName(info['from']) + "--- ROUTE: ",getNodeNameInList(info['route']))
    print("-----------------------------------")

    changed = updateBestRoutes(info)

    if(changed):
        for neighbour in myNeighbours:
            if(neighbour != add[0]):

                #print("-----------------------------------")
                #print('Enviar para ' + getNodeName(neighbour) + "--- ROUTE: ",getNodeNameInList(info['route']))
                #print("-----------------------------------")

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
        

#-----------------

def sendBackFlood(s):

    global best_routes
    global serverPort2

    for server in best_routes:
        infoJSON = json.dumps(best_routes[server])
        print(infoJSON)
        s.sendto(infoJSON.encode('utf-8'), (server, serverPort2))



def getServers():

    with open(sys.argv[3]) as json_file:
        file = json.load(json_file)
        return file['servers']


def node():

    global serverAddress
    global servers_node
    global ip_node
    global myNeighbours
    global nodePort1
    global nodePort2

    ip_node = sys.argv[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((ip_node, nodePort1))

    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s1.bind((ip_node, nodePort2))

    servers_node = getServers()
    serverAddress = servers_node[0]
    myNeighbours = getNeighbours(s)

    threading.Thread(target=continueFlood, args=(s,)).start()
    time.sleep(5)
    sendBackFlood(s1)
    



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

#----------------------------------------------------------