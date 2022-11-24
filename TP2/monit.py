#info = {
#    "type" : 'monit',
#    "from" : masterAddress,
#    "start_time" : time.time()
#    "path" : [1,2,3,4]
#    "totalDelay" : 0
#}


def sendMonitS():
    #nextHop
    ipClient
    ipNodoFolha
    listToClient = routes[ipNodoFolha]
    while(True):
            neighbours = topology_master[masterAddress]

            info = {
                "server" : masterAddress,
                "path": listToClient,
                "start_time" : time.time(),
                "total_delay": 0,
                "ip_client" : ipClient
            }
            nextHop = info["path"][0]
            time.sleep(1) # necessário para cada nodo ler os seus vizinhos e preparar a socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((masterAddress,masterPort1))
            infoJSON = json.dumps(info)
            s.sendto(infoJSON.encode('utf-8'), (nextHop, nodePort1))

            time.sleep(10000)


def sendMonitN(s:socket.socket):
    
    global best_route
    serverConnected = best_route["route"][0]

    info = json.loads(msg.decode('utf-8'))

    if(len(info['path']>1)):
        info['path'].pop(0)
        nextHop = info['path'][0]        
        infoJSON = json.dumps(info)
        s.sendto(infoJSON.encode('utf-8'), (nextHop, nodePort1)) #temos que alterar as portas
        
    # Last node 
    else:
        info["total_delay"] = time.time() - info["start_time"]
        numberServers
        i = 0
        while(i < numberServers):
            info = json.loads(msg.decode('utf-8'))
            delayServer = info["total_delay"]
            if (i = 0):
                bestServer = ([info["server"]],delayServer)
            
            if(delayServer < bestServer[1]):
                bestServer[0] = info["server"] 
                bestServer[1] = delayServer
            
        # Send to Client the best Server
        msg 
        if (serverConnected != bestServer[0]):
            print("Devia passar para o server com ip: ", bestServer) # transformar num send
        else :
            print("O servidor atual é o melhor") # transformar num send
        
        #infoJSON = json.dumps(info)
        #s.sendto(infoJSON.encode('utf-8'), (info["ip_client"], nodePort1)) #temos que alterar as portas 
        
        



def receiveMoniClient():
            