# UDPPingerServer.py
# Lab 2: UDP Pinger Lab — Server (provided, do not modify)

import random
from socket import *

# Create a UDP socket
serverSocket = socket(AF_INET, SOCK_DGRAM)

# Assign IP address and port number to socket
serverSocket.bind(('', 12000))

print("UDP Ping Server running on port 12000...")

while True:
    # Generate random number in the range of 0 to 10
    rand = random.randint(0, 10)

    # Receive the client packet along with the address it is coming from
    message, address = serverSocket.recvfrom(1024)

    # Capitalize the message from the client
    message = message.upper()

    # If rand < 4, simulate packet loss (30% loss rate)
    if rand < 4:
        continue

    # Otherwise, send the capitalized message back to the client
    serverSocket.sendto(message, address)
