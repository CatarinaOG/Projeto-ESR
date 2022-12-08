import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		rtpPort = sys.argv[2]
		fileName = sys.argv[3]
		myAddress = sys.argv[4]
	except:
		print("[Usage: ClientLauncher.py Server_address Server_port RTP_port Video_file clientAddress]\n")	
	
	root = Tk()
	
	# Create a new client
	app = Client(root, serverAddr, rtpPort, fileName,myAddress)
	app.master.title("RTPClient")	
	root.mainloop()
	