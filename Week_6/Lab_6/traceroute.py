from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2


def checksum(string):
    # Compute the Internet checksum over the given bytes
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum += thisVal
        csum &= 0xffffffff
        count += 2
    if countTo < len(string):
        csum += string[len(string) - 1]
        csum &= 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum += (csum >> 16)
    answer = ~csum
    answer &= 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def build_packet():
    # Build an ICMP Echo Request packet (same structure as Ping lab)
    myChecksum = 0
    myID = os.getpid() & 0xFFFF

    # Step 1: Make a dummy header with checksum = 0
    # Header fields: type (b), code (b), checksum (H), id (H), sequence (H)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)

    # Step 2: Pack current timestamp as payload data
    data = struct.pack("d", time.time())

    # Step 3: Calculate real checksum over header + data
    myChecksum = checksum(header + data)

    # Step 4: Rebuild header with correct checksum (handle byte order)
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)

    # Step 5: Assemble final packet — do NOT send yet, just return it
    packet = header + data
    return packet


def get_route(hostname):
    timeLeft = TIMEOUT

    for ttl in range(1, MAX_HOPS):
        for tries in range(TRIES):
            destAddr = gethostbyname(hostname)

            # Fill in start
            # Create a raw ICMP socket
            mySocket = socket(AF_INET, SOCK_RAW, getprotobyname("icmp"))
            # Fill in end

            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)

            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t = time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)

                if whatReady[0] == []:  # Timeout
                    print(" * * * Request timed out.")
                    continue

                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft = timeLeft - howLongInSelect

                if timeLeft <= 0:
                    print(" * * * Request timed out.")
                    continue

            except timeout:
                continue

            else:
                # Fill in start
                # Fetch the ICMP type from the received IP packet.
                # The IP header is 20 bytes; ICMP header starts at byte 20.
                # ICMP type is the first byte of the ICMP header (byte 20).
                types = struct.unpack("b", recvPacket[20:21])[0]
                # Fill in end

                if types == 11:
                    # TTL Exceeded — intermediate router
                    bytes_sz = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes_sz])[0]
                    print(" %d  rtt=%.0f ms  %s" % (ttl, (timeReceived - t) * 1000, addr[0]))

                elif types == 3:
                    # Destination Unreachable
                    bytes_sz = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes_sz])[0]
                    print(" %d  rtt=%.0f ms  %s" % (ttl, (timeReceived - t) * 1000, addr[0]))

                elif types == 0:
                    # Echo Reply — destination reached
                    bytes_sz = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes_sz])[0]
                    print(" %d  rtt=%.0f ms  %s" % (ttl, (timeReceived - timeSent) * 1000, addr[0]))
                    return  # Destination reached — stop traceroute

                else:
                    print("error")

                break  # Move to next TTL after a successful reply

            finally:
                mySocket.close()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    targets = [
        "google.com",           # North America (USA)
        "bbc.co.uk",            # Europe (United Kingdom)
        "yahoo.co.jp",          # Asia (Japan)
        "uct.ac.za",            # Africa (South Africa)
    ]

    for host in targets:
        print(f"\ntraceroute to {host}, max {MAX_HOPS} hops\n")
        get_route(host)
        print()
