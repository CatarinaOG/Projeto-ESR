import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]
		fileName = sys.argv[4]	
		myAddress = sys.argv[5]
	except:
		print("[Usage: ClientLauncher.py Server_address Server_port RTP_port Video_file clientAddress]\n")	
	
	root = Tk()
	
	# Create a new client
	app = Client(root, serverAddr, serverPort, rtpPort, fileName,myAddress)
	app.master.title("RTPClient")	
	root.mainloop()
	