import sys, socket

from ServerWorker import ServerWorker

class Server:	
	
	def main(self,serverAddr,serverPort):
		
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		rtspSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
		rtspSocket.bind((serverAddr, serverPort))
		rtspSocket.listen(5)        
        PRINT("CHEGEU AQUI")
		# Receive client info (address,port) through RTSP/TCP session
		#while True:
		#	clientInfo = {}
		#	clientInfo['rtspSocket'] = rtspSocket.accept()
		#	ServerWorker(clientInfo).run()		

if __name__ == "__main__":
	(Server()).main()