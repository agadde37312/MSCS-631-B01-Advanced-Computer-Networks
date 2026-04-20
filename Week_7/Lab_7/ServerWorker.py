# ServerWorker.py
import threading
import random
import socket
import time

from VideoStream import VideoStream
from RtpPacket import RtpPacket


class ServerWorker(threading.Thread):
    # RTSP States
    INIT = 0
    READY = 1
    PLAYING = 2

    # RTSP Methods
    SETUP = "SETUP"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    TEARDOWN = "TEARDOWN"

    def __init__(self, clientInfo):
        threading.Thread.__init__(self)
        self.clientInfo = clientInfo
        self.state = self.INIT
        self.sessionId = random.randint(100000, 999999)
        self.videoStream = None
        self.rtpSocket = None
        self.rtpPort = None
        self.frameNbr = 0
        self.playEvent = threading.Event()

    def run(self):
        """Main RTSP request handler."""
        rtspSocket = self.clientInfo['rtspSocket']

        while True:
            data = rtspSocket.recv(1024)
            if not data:
                print("[SERVER] RTSP socket closed by client.")
                break

            request = data.decode("utf-8")
            print("========== RTSP REQUEST ==========")
            print(request)
            print("==================================")

            self.processRtspRequest(request)

    def processRtspRequest(self, request):
        """Parse RTSP request and act accordingly."""
        lines = request.split('\n')
        if len(lines) < 3:
            return

        requestLine = lines[0].split(' ')
        method = requestLine[0]

        seqLine = lines[1].split(' ')
        cseq = seqLine[1].strip()

        if method == self.SETUP:
            if self.state == self.INIT:
                filename = requestLine[1]
                self.clientInfo['fileName'] = filename

                try:
                    self.videoStream = VideoStream(filename)
                    print(f"[SERVER] Opened video file: {filename}")
                except IOError:
                    print("[SERVER] 404 NOT_FOUND")
                    self.replyRtsp(404, cseq)
                    return

                # Parse Transport header
                transport = lines[2]
                idx = transport.find("client_port=")
                self.rtpPort = int(transport[idx + len("client_port="):].strip())

                # Create RTP socket (UDP)
                self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                self.state = self.READY
                self.replyRtsp(200, cseq)
                print(f"[SERVER] State -> READY, Session={self.sessionId}, RTP Port={self.rtpPort}")

        elif method == self.PLAY:
            if self.state == self.READY:
                self.state = self.PLAYING
                self.replyRtsp(200, cseq)
                print("[SERVER] State -> PLAYING")

                self.playEvent.clear()
                threading.Thread(target=self.sendRtp).start()

        elif method == self.PAUSE:
            if self.state == self.PLAYING:
                self.state = self.READY
                self.playEvent.set()
                self.replyRtsp(200, cseq)
                print("[SERVER] State -> READY (PAUSED)")

        elif method == self.TEARDOWN:
            print("[SERVER] TEARDOWN received")
            self.replyRtsp(200, cseq)

            self.playEvent.set()
            time.sleep(0.1)

            if self.rtpSocket:
                self.rtpSocket.close()
                print("[SERVER] RTP socket closed.")

            self.clientInfo['rtspSocket'].close()
            print("[SERVER] RTSP socket closed. Session ended.")

            raise SystemExit

    def sendRtp(self):
        """Send RTP packets while PLAYING."""
        addr = self.clientInfo['rtspAddr'][0]

        while not self.playEvent.is_set():

            time.sleep(0.05)  # 20 FPS approx.

            if self.state != self.PLAYING:
                continue

            data = self.videoStream.nextFrame()
            if data is None:
                print("[RTP] End of video stream.")
                break

            self.frameNbr = self.videoStream.frameNbr()

            try:
                packet = self.makeRtp(self.frameNbr, data)
                self.rtpSocket.sendto(packet, (addr, self.rtpPort))
                print(f"[RTP] Sent packet SeqNum={self.frameNbr}")
            except Exception as e:
                print("[RTP] Failed to send packet:", e)
                break

    def makeRtp(self, frameNbr, payload):
        """Build and return an RTP packet."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26                     # MJPEG
        seqnum = frameNbr
        timestamp = int(time.time())  # Simple timestamp
        ssrc = 123456               # Server identifier

        rtpPacket = RtpPacket()
        rtpPacket.encode(
            version, padding, extension, cc,
            marker, pt, seqnum, timestamp, ssrc,
            payload
        )

        return rtpPacket.getPacket()

    def replyRtsp(self, code, cseq):
        """Send RTSP reply to client."""
        if code == 200:
            line1 = "RTSP/1.0 200 OK"
        elif code == 404:
            line1 = "RTSP/1.0 404 NOT_FOUND"
        else:
            line1 = f"RTSP/1.0 {code} ERROR"

        reply = f"{line1}\nCSeq: {cseq}\nSession: {self.sessionId}\n"
        self.clientInfo['rtspSocket'].send(reply.encode('utf-8'))

        print("========== RTSP REPLY ==========")
        print(reply)
        print("================================")
# End of ServerWorker.py
