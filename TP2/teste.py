import socket
import threading
import time
import sys
import json


# ----- Master Globals ------

masterAddress = '10.0.2.10'
masterPort1 = 3000
nodes_master = 0
topology_master = {}


# ------ Node Globals ------

nodePort1 = 3000
myNeighbours = []
ip_node = ''
best_route = {}
neighboursFlood = []

#-----------------------------Master------------------------------------

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


#-----------------

def getTopology():
    global topology_master
    global nodes_master

    with open(sys.argv[2]) as json_file:
        topology_master = json.load(json_file)

    for key in topology_master:
        nodes_master += 1

    nodes_master -= 1

#----------------

def sendNeighbours():

    global nodes_master

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((masterAddress, masterPort1))

    nodes = 0
    while nodes < nodes_master:
        msg, add = s.recvfrom(1024)
        threading.Thread(target=sendEachNeighbours, args=(s, msg, add)).start()
        nodes += 1


#----------------

def flood():

    #while(True):
        neighbours = topology_master[masterAddress]

        info = {
            "type" : 'update',
            "server" : masterAddress,
            "from" : masterAddress,
            "depth" : 0,
            "start_time" : time.time(),
            "totalDelay" : 0,
            "route" : [masterAddress]
        }

        time.sleep(1) # necessário para cada nodo ler os seus vizinhos e preparar a socket

        for neighbour in neighbours:
            print("Enviei para " + neighbour + "info: " + json.dumps(info))
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((masterAddress,masterPort1))
            infoJSON = json.dumps(info)
            s.sendto(infoJSON.encode('utf-8'), (neighbour, nodePort1))

    #    time.sleep(1000)

#-----------------

def master():

    getTopology()
    sendNeighbours()
    threading.Thread(target=flood, args=()).start()




#------------------------------Node + client---------------------------------

def getNeighbours(s):

    msg = 'neighbours'
    s.sendto(msg.encode('utf-8'), (masterAddress, masterPort1))
    answer, server_add = s.recvfrom(1024)

    return json.loads(answer.decode('utf-8'))['neighbours']

#---------------------------------Client---------------------------------

def client():

    print("cliente")



#----------------------------------Node--------------------------------

#info = {
#    "type" : 'update',
#    "from" : masterAddress,
#    "depth" : 0,
#    "start_time" : time.time()
#    "totalDelay" : 0,
#    "route" : []
#}

def getNodeName(add):

    if (add == '10.0.3.1'): return "N2"
    elif (add == '10.0.2.1'): return "N3"
    elif(add == '10.0.5.1'): return "N1"
    elif(add == '10.0.2.10'): return "S1"


def getNodeNameInList(lista):

    newlist = []

    for i in range(len(lista)):
        newlist.append(getNodeName(lista[i]))

    return newlist


def continueFlood1(msg : bytes, add : tuple, s : socket.socket, lock : threading.Lock):

    global myNeighbours
    global best_route
    global ip_node
    global neighboursFlood

    best_route_changed = False

    lock.acquire()


    info = json.loads(msg.decode('utf-8'))
    neighboursFlood.append(info['from'])

    print("-----------------------------------")
    print('Recebi de ' + getNodeName(info['from']) + "--- ROUTE: ",getNodeNameInList(info['route']))
    print("-----------------------------------")

    if(info['type'] == 'update'):
        info['depth'] += 1
        info['totalDelay'] += time.time() - info['start_time']
        info['start_time'] = time.time()

    if(len(best_route) == 0):
        best_route = info
        best_route["route"].append(ip_node)
        best_route["from"] = ip_node
        best_route_changed = True

    elif (best_route['totalDelay'] > info['totalDelay']):
        best_route = info
        best_route["route"].append(ip_node)
        best_route["from"] = ip_node
        best_route_changed = True
        
    if(best_route_changed):
        for neighbour in myNeighbours:
            if(neighbour != add[0] and neighbour not in neighboursFlood):

                print("-----------------------------------")
                print('Enviar para ' + getNodeName(neighbour) + "--- ROUTE: ",getNodeNameInList(info['route']))
                print("-----------------------------------")

                infoJSON = json.dumps(best_route)
                s.sendto(infoJSON.encode('utf-8'), (neighbour, nodePort1))

    lock.release()

    print("BEST ROUTE: ",getNodeNameInList(best_route['route']))


def continueFlood(s):

    global ip_node

    lock = threading.Lock()
    
    while(True):
        msg, add = s.recvfrom(1024)
        threading.Thread(target=continueFlood1, args=(msg,add,s,lock)).start()
        

#-----------------

def node():

    global ip_node
    global nodePort1
    global myNeighbours

    ip_node = sys.argv[3]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((ip_node, nodePort1))

    myNeighbours = getNeighbours(s)
    
    continueFlood(s)
    



#---------------------------------Main----------------------------------

if __name__ == "__main__":

    if(len(sys.argv) == 3 and sys.argv[1] == 'master'):
        # python3 teste.py master config.json 
        master()

    elif(len(sys.argv) == 4 and sys.argv[1] == 'node'):
        # python3 teste.py node 10.0.2.10 <ip_nodo>
        node()
    
    else:
        # python3 teste.py 10.0.2.10
        client()

#----------------------------------------------------------