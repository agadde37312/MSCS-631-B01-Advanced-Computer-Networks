from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8

def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = string[count+1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Fill in start
        # Fetch the ICMP header from the IP packet
        # IP header = 20 bytes, ICMP header starts at byte 20
        icmpHeader = recPacket[20:28]
        icmpType, icmpCode, icmpChecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if packetID == ID:
            # Data payload starts at byte 28 (after IP + ICMP headers)
            dataPayload = recPacket[28:]
            timeSent = struct.unpack("d", dataPayload[:8])[0]
            rtt = (timeReceived - timeSent) * 1000  # convert to ms
            ttl = struct.unpack("B", recPacket[8:9])[0]
            return "Reply from %s: bytes=%d time=%.3fms TTL=%d" % (
                addr[0], len(dataPayload), rtt, ttl)
        # Fill in end

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0

    # Make a dummy header with a 0 checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the dummy header.
    # FIX: pass bytes directly, not str() — avoids checksum mismatch
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    # SOCK_RAW is a powerful socket type.
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    # FIX: set a socket-level timeout as a safety net
    mySocket.settimeout(timeout + 1)

    myID = os.getpid() & 0xFFFF  # Return the current process ID
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")

    rtts = []
    for i in range(10):
        delay = doOnePing(dest, timeout)
        print(delay)
        if "timed out" not in delay:
            rtt = float(delay.split("time=")[1].split("ms")[0])
            rtts.append(rtt)
        time.sleep(1)

    # Summary
    print("")
    print("--- Ping Statistics ---")
    print("Sent: 10  Received: %d  Lost: %d" % (len(rtts), 10 - len(rtts)))
    if rtts:
        print("Min: %.3fms  Max: %.3fms  Avg: %.3fms" % (
            min(rtts), max(rtts), sum(rtts)/len(rtts)))

ping("google.com")
