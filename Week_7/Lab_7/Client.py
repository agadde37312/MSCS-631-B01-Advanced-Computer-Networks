# Client.py - Complete Implementation for Python Lab 7: Video Streaming with RTSP/RTP
from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3

    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0

        # Statistics tracking
        self.packetsReceived = 0
        self.packetsLost = 0
        self.bytesReceived = 0
        self.sessionStartTime = None
        self.lastSeqNum = -1

    def createWidgets(self):
        """Build GUI."""
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()
        cachefile = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        if os.path.exists(cachefile):
            os.remove(cachefile)

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        if self.state == self.READY:
            # ── COMPLETED: Start RTP listener thread and clear play event ──
            self.playEvent = threading.Event()
            threading.Thread(target=self.listenRtp).start()
            self.playEvent.clear()
            if self.sessionStartTime is None:
                self.sessionStartTime = time.time()
            self.sendRtspRequest(self.PLAY)

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    # Track statistics
                    self.packetsReceived += 1
                    self.bytesReceived += len(data)

                    # Detect packet loss
                    if self.lastSeqNum >= 0 and currFrameNbr > self.lastSeqNum + 1:
                        self.packetsLost += (currFrameNbr - self.lastSeqNum - 1)
                    self.lastSeqNum = currFrameNbr

                    if currFrameNbr > self.frameNbr:
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))

            except:
                if self.playEvent.isSet():
                    break
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()
        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkinter.messagebox.showwarning('Connection Failed',
                                           'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # ── SETUP ──────────────────────────────────────────────────────────────
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            self.rtspSeq += 1
            request = ('SETUP ' + self.fileName + ' RTSP/1.0\n'
                       'CSeq: ' + str(self.rtspSeq) + '\n'
                       'Transport: RTP/UDP; client_port= ' + str(self.rtpPort))
            self.requestSent = self.SETUP

        # ── PLAY ───────────────────────────────────────────────────────────────
        elif requestCode == self.PLAY and self.state == self.READY:
            self.rtspSeq += 1
            request = ('PLAY ' + self.fileName + ' RTSP/1.0\n'
                       'CSeq: ' + str(self.rtspSeq) + '\n'
                       'Session: ' + str(self.sessionId))
            self.requestSent = self.PLAY

        # ── PAUSE ──────────────────────────────────────────────────────────────
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.rtspSeq += 1
            request = ('PAUSE ' + self.fileName + ' RTSP/1.0\n'
                       'CSeq: ' + str(self.rtspSeq) + '\n'
                       'Session: ' + str(self.sessionId))
            self.requestSent = self.PAUSE

        # ── TEARDOWN ───────────────────────────────────────────────────────────
        elif requestCode == self.TEARDOWN and self.state != self.INIT:
            self.rtspSeq += 1
            request = ('TEARDOWN ' + self.fileName + ' RTSP/1.0\n'
                       'CSeq: ' + str(self.rtspSeq) + '\n'
                       'Session: ' + str(self.sessionId))
            self.requestSent = self.TEARDOWN
        else:
            return

        self.rtspSocket.send(request.encode())
        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)
            if reply:
                self.parseRtspReply(reply.decode("utf-8"))
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = str(data).split('\n')
        seqNum = int(lines[1].split(' ')[1])

        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            if self.sessionId == 0:
                self.sessionId = session

            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        self.state = self.READY
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        self.teardownAcked = 1

    def openRtpPort(self):
        """Open RTP socket bound to the specified port."""
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        try:
            self.rtpSocket.bind(("", self.rtpPort))
        except:
            tkinter.messagebox.showwarning('Unable to Bind',
                                           'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:
            self.playMovie()


# ── ClientLauncher ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        serverAddr = sys.argv[1]
        serverPort = sys.argv[2]
        rtpPort    = sys.argv[3]
        fileName   = sys.argv[4]
    except IndexError:
        print("Usage: python Client.py <server_host> <server_port> <rtp_port> <video_file>")
        sys.exit(1)

    root = Tk()
    root.title("RTPClient")
    app = Client(root, serverAddr, serverPort, rtpPort, fileName)
    root.mainloop()
