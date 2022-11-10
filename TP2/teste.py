import socket
import threading
import time
import sys
import json

masterAdress = '10.0.2.10'
masterPort = 3000

topology = {}
myNeighbours = []

def processamento(s : socket, msg : bytes, add : tuple):
    
    if(msg.decode('utf-8') == "neighbours"):
        response = topology[add[0]]
        send=json.dumps(response) 
        s.sendto(send.encode('utf-8'), add)


def servico():

    global topology

    with open(sys.argv[1]) as json_file:
        topology = json.load(json_file)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((masterAdress, masterPort))

    print(f"Estou à escuta no {masterAdress}:{masterPort}")

    while True:
        msg, add = s.recvfrom(1024)
        threading.Thread(target=processamento, args=(s, msg, add)).start()

    s.close()



def master():
    threading.Thread(target=servico, args=()).start()


def getNeighbours(s):

    global myNeighbours

    msg = 'neighbours'

    s.sendto(msg.encode('utf-8'), (masterAdress, 3000))
    answer, server_add = s.recvfrom(1024)
    myNeighbours = json.loads(answer.decode('utf-8'))

    s.close()



def client():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    getNeighbours(s)

    


if __name__ == "__main__":

    if(len(sys.argv) == 3):
        master()
    else:
        client()