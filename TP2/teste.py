import socket
import threading
import time
import sys
import json

masterAddress = '10.0.2.10'
masterPort1 = 3000

nodePort1 = 3000

topology_master = {}
myNeighbours_node = []

ip_node = ''

nodes_master = 0

best_node = {}

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
            "route" : []
        }

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

def getNeighbours():

    global ip_node

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((ip_node, nodePort1))
    msg = 'neighbours'
    s.sendto(msg.encode('utf-8'), (masterAddress, masterPort1))
    answer, server_add = s.recvfrom(1024)
    s.close()
    
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


def continueFlood1(msg : bytes, add : tuple, s : socket.socket, lock : threading.Lock):

    global myNeighbours_node
    global best_node
    global ip_node

    info = json.loads(msg.decode('utf-8'))
    #print("-----------------------------------")
    #print("recebi: ",info)
    #print("-----------------------------------")


    if(info['type'] == 'update'):
        info['depth'] += 1
        info['totalDelay'] += time.time() - info['start_time']
        info['start_time'] = time.time()

    if(len(best_node) == 0):
        lock.acquire()
        best_node = info
        best_node["route"].append(add[0])
        best_node["from"] = add[0]
        lock.release()

    elif (best_node['totalDelay'] > info['totalDelay']):
        lock.acquire()
        best_node = info
        best_node["route"].append(add[0])
        best_node["from"] = add[0]
        lock.release()

    for neighbour in myNeighbours_node:
        if(neighbour != add[0] and neighbour not in best_node["route"]):
            print("-----------------------------------")
            print('Enviar para ' + neighbour)
            print('info : ', info)
            print("-----------------------------------")

            infoJSON = json.dumps(best_node)
            time.sleep(0.5)
            s.sendto(infoJSON.encode('utf-8'), (neighbour, nodePort1))


def continueFlood():

    global ip_node

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((ip_node, nodePort1))
    
    print("NODE: ip: "+ip_node + " porta: "+str(nodePort1))

    lock = threading.Lock()
    
    while(True):
        msg, add = s.recvfrom(1024)
        threading.Thread(target=continueFlood1, args=(msg,add,s,lock)).start()
        

#-----------------

def node():

    global ip_node
    global myNeighbours_node

    ip_node = sys.argv[3]

    myNeighbours_node = getNeighbours()
    print("neighbours: ",myNeighbours_node)
    
    continueFlood()
    



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