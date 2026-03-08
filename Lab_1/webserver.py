# Web Server Lab - Python Socket Programming
# Lab 1: TCP Web Server Implementation
# Advanced Computer Networks

# Import socket module
from socket import *
import sys  # In order to terminate the program

# Create a TCP server socket (AF_INET = IPv4, SOCK_STREAM = TCP)
serverSocket = socket(AF_INET, SOCK_STREAM)

# Prepare a server socket
# Fill in start
serverSocket.bind(('', 6789))   # Bind to all interfaces on port 6789
serverSocket.listen(1)          # Listen for incoming connections (queue of 1)
# Fill in end

while True:
    # Establish the connection
    print('Ready to serve...')
    connectionSocket, addr = serverSocket.accept()  # Fill in start / Fill in end

    try:
        message = connectionSocket.recv(1024).decode()  # Fill in start / Fill in end
        filename = message.split()[1]
        f = open(filename[1:])
        outputdata = f.read()   # Fill in start / Fill in end

        # Send one HTTP header line into socket
        # Fill in start
        connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
        connectionSocket.send("Content-Type: text/html\r\n".encode())
        connectionSocket.send("\r\n".encode())
        # Fill in end

        # Send the content of the requested file to the client
        for i in range(0, len(outputdata)):
            connectionSocket.send(outputdata[i].encode())
        connectionSocket.send("\r\n".encode())
        connectionSocket.close()

    except IOError:
        # Send response message for file not found
        # Fill in start
        connectionSocket.send("HTTP/1.1 404 Not Found\r\n".encode())
        connectionSocket.send("Content-Type: text/html\r\n".encode())
        connectionSocket.send("\r\n".encode())
        connectionSocket.send("<html><body><h1>404 Not Found</h1><p>The requested file was not found on this server.</p></body></html>\r\n".encode())
        # Fill in end

        # Close client socket
        # Fill in start
        connectionSocket.close()
        # Fill in end

serverSocket.close()
sys.exit()  # Terminate the program after sending the corresponding data
