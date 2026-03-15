# UDPPingerClient.py
# Author: Arun Bhaskar Gadde
# Lab 2: UDP Pinger Lab
# Advanced Computer Networks

from socket import *
import time

# Server address and port
serverName = '127.0.0.1'  # localhost for testing
serverPort = 12000

# Create a UDP socket
clientSocket = socket(AF_INET, SOCK_DGRAM)

# Set socket timeout to 1 second
clientSocket.settimeout(1)

# Counters for statistics
packets_sent = 0
packets_received = 0
rtt_list = []

print("=" * 55)
print("  UDP Pinger Client - Lab 2")
print(f"  Target: {serverName}:{serverPort}")
print("=" * 55)

# Send 10 ping messages
for sequence_number in range(1, 11):
    # Record the send time
    send_time = time.time()

    # Format the ping message: "Ping sequence_number time"
    message = f"Ping {sequence_number} {send_time}"

    packets_sent += 1

    try:
        # Send the UDP packet (no connection needed — connectionless)
        clientSocket.sendto(message.encode(), (serverName, serverPort))

        # Wait for reply (up to 1 second timeout)
        response, server_address = clientSocket.recvfrom(1024)

        # Calculate round-trip time
        rtt = time.time() - send_time

        packets_received += 1
        rtt_list.append(rtt)

        # Print the server response and RTT
        print(f"Ping {sequence_number}: Reply from {server_address[0]}  "
              f"msg={response.decode()}  RTT={rtt:.4f}s")

    except timeout:
        # No reply within 1 second — packet lost
        print(f"Ping {sequence_number}: Request timed out")

# Close the socket
clientSocket.close()

# Print statistics
print("=" * 55)
print("  Ping Statistics")
print("=" * 55)
packets_lost = packets_sent - packets_received
loss_rate = (packets_lost / packets_sent) * 100
print(f"  Packets Sent:     {packets_sent}")
print(f"  Packets Received: {packets_received}")
print(f"  Packets Lost:     {packets_lost}")
print(f"  Packet Loss Rate: {loss_rate:.1f}%")

if rtt_list:
    print(f"  Min RTT:  {min(rtt_list):.4f}s")
    print(f"  Max RTT:  {max(rtt_list):.4f}s")
    print(f"  Avg RTT:  {sum(rtt_list)/len(rtt_list):.4f}s")
print("=" * 55)
