import sys
import json
from socket import *
import re
topology = {}
myNeighbours = []


def runController():

    # Opening JSON file
    global topology
    
    with open(sys.argv[1]) as json_file:
        topology = json.load(json_file)
        print(topology)
    
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("", serverPort))
    serverSocket.listen()

    while(True):
        connectionSocket, addr = serverSocket.accept()
        sentence = connectionSocket.recv(1024).decode()
        if(sentence=="neighbours"):
            response = topology[addr[0]]
            m = response
            send=json.dumps(m) 
            connectionSocket.send(bytes(send,encoding="utf-8"))
            connectionSocket.close()




def askForNeighbours():

    controllerIP = sys.argv[1]

    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((controllerIP, 12000))

    sentence = 'neighbours'
    clientSocket.send(sentence.encode())
    modifiedSentence = clientSocket.recv(1024)
    neighbours = modifiedSentence.decode("utf-8")
    myNeighbours = json.loads(neighbours)

    clientSocket.close()



def runClient():

    askForNeighbours()



def main():

    # Verificar se é controlador ou cliente
    if(len(sys.argv) == 3):
        runController()
    else:
        runClient()
   
    #capitalizedSentence = sentence.upper()
    #connectionSocket.send(capitalizedSentence.encode())


main()