import sys
import json
from socket import *
 

def main():
    # Opening JSON file
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("", serverPort))
    serverSocket.listen(1)
    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)
    
        # Print the type of data variable
        print("Type:", type(data))
    
        # Print the data of dictionary
        for key in data:
            print(key, '->', data[key])
        
    
    while(True):
        connectionSocket, addr = serverSocket.accept()
        sentence = connectionSocket.recv(1024).decode()
        if(sentence=="neighbours"):
            response = data[addr[0]]
            print(response)
            m = {addr[0]  : response}
            data = json.dumps(m)
            connectionSocket.send(bytes(data,encoding="utf-8"))
            connectionSocket.close()
        print(sentence)


            
        #capitalizedSentence = sentence.upper()
        #connectionSocket.send(capitalizedSentence.encode())
main()