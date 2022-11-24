import socket
import threading
import time
import sys
import json


# ----- Master Globals ------

serverAddress = ''
serverPort1 = 3000
nodes_master = 0
topology_master = {}
isMaster = False
servers = []


# ------ Node Globals ------

nodePort1 = 3000
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

        print("sent: ",info)

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
        print("Enviei para " + neighbour + "- ROUTE: " , info['route'])
        infoJSON = json.dumps(info)
        s.sendto(infoJSON.encode('utf-8'), (neighbour, nodePort1))




def notifyOtherServers(s):

    for server in servers:
        s.sendto("start".encode('utf-8'), (server, serverPort1))




def server():

    global serverAddress
    serverAddress = sys.argv[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((serverAddress, serverPort1))
    
    getTopology()

    if(isMaster):
        sendNeighbours(s)
        notifyOtherServers(s)
    else:
        msg, add = s.recvfrom(1024)
    
    time.sleep(1) # necessário para cada nodo ler os seus vizinhos e preparar a socket
    threading.Thread(target=flood, args=(s,)).start()




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
    

def getNodeNameInList(lista):

    newlist = []

    for i in range(len(lista)):
        newlist.append(getNodeName(lista[i]))

    return newlist


def updateBestRoutes(info):

    global best_routes

    info['depth'] += 1
    info['totalDelay'] += time.time() - info['start_time']
    info['start_time'] = time.time()

    if(len(best_routes) == 0):
        best_routes = info
        best_routes["route"].append(ip_node)
        best_routes["from"] = ip_node
        return True

    elif (best_routes['totalDelay'] > info['totalDelay']):
        best_routes = info
        best_routes["route"].append(ip_node)
        best_routes["from"] = ip_node
        return True
    
    return False


def continueFlood1(msg : bytes, add : tuple, s : socket.socket, lock : threading.Lock):

    global myNeighbours
    global ip_node

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

                print("-----------------------------------")
                print('Enviar para ' + getNodeName(neighbour) + "--- ROUTE: ",getNodeNameInList(info['route']))
                print("-----------------------------------")

                infoJSON = json.dumps(best_routes)
                s.sendto(infoJSON.encode('utf-8'), (neighbour, nodePort1))

    lock.release()

    print("BEST ROUTE: ",getNodeNameInList(best_routes['route']))


def continueFlood(s):

    global ip_node

    lock = threading.Lock()
    
    while(True):
        msg, add = s.recvfrom(1024)
        threading.Thread(target=continueFlood1, args=(msg,add,s,lock)).start()
        

#-----------------


def getServers():

    with open(sys.argv[3]) as json_file:
        file = json.load(json_file)
        return file['servers']


def node():

    global serverAddress
    global servers_node
    global ip_node
    global myNeighbours

    ip_node = sys.argv[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((ip_node, nodePort1))

    servers_node = getServers()
    serverAddress = servers_node[0]
    myNeighbours = getNeighbours(s)

    continueFlood(s)
    



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