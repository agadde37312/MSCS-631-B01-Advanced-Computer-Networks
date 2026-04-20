# Server.py
import sys
import socket
from ServerWorker import ServerWorker

def main():
    if len(sys.argv) != 2:
        print("Usage: python Server.py <server_port>")
        sys.exit(1)

    serverPort = int(sys.argv[1])

    # Create the listening TCP socket for RTSP
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen(5)

    print(f"[SERVER] RTSP server listening on port {serverPort}...")

    while True:
        clientSocket, clientAddr = serverSocket.accept()
        print(f"[SERVER] New RTSP connection from {clientAddr}")

        clientInfo = {
            'rtspSocket': clientSocket,
            'rtspAddr': clientAddr
        }

        worker = ServerWorker(clientInfo)
        worker.start()

if __name__ == "__main__":
    main()
