from random import randint
from RtpPacket import RtpPacket
from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import json

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class ClientStream:	

	clientAddress = ''
	clientPort = 0
	frameNbr = 0
	sessionId = 0

	nodePort6 = 8000


	def __init__(self,master,clientAddress,clientPort,nodeAddress):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.clientAddress = clientAddress
		self.clientPort = clientPort
		self.nodeAddress = nodeAddress
		self.createWidgets()
		self.openRtpPort()


	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""

		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		
		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(5)
		
		try:
			# Bind the socket to the address using the RTP port given by the client user
			self.rtpSocket.bind((self.clientAddress, self.clientPort))
		except:
			tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

	def listenRtp(self):

		while True:
			data = self.rtpSocket.recv(20480)
			
			rtpPacket = RtpPacket()
			rtpPacket.decode(data)
			
			currFrameNbr = rtpPacket.seqNum()
								
			self.frameNbr = currFrameNbr
			self.updateMovie(self.writeFrame(rtpPacket.getPayload()))


	def playMovie(self):	
		"""Listen for RTP packets."""
		threading.Thread(target=self.listenRtp).start()
	

	def stopRtp(self):
		print("entrei'2")

		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.bind((self.clientAddress,self.nodePort6))

		send = {
			"command" : "stop"
		}

		infoJSON = json.dumps(send)
		s.sendto(infoJSON.encode('utf-8'), (self.nodeAddress, self.nodePort6))


	def stopMovie(self):	
		"""Listen for RTP packets."""
		print("entrei'1")
		threading.Thread(target=self.stopRtp).start()


			
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""

		cachename = CACHE_FILE_NAME + str(self.clientAddress) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename
				
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""

		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo

	def createWidgets(self):

		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] = self.stopMovie
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 


	def handler(self):

		if (tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?")):
			self.master.destroy() # Close the gui window
			os.remove(CACHE_FILE_NAME + str(self.clientAddress) + CACHE_FILE_EXT) # Delete the cache image from video