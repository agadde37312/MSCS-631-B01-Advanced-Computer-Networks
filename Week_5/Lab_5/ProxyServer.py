from socket import *
import sys

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n'
          '[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)

# Fill in start.
# Allow address reuse so we can restart quickly without "Address already in use" error
tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
# Bind to the proxy server IP and port 8888
tcpSerSock.bind((sys.argv[1], 8888))
# Start listening; allow up to 5 queued connections
tcpSerSock.listen(5)
# Fill in end.

while 1:
    # Start receiving data from the client
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('Received a connection from:', addr)

    # Fill in start.
    # Receive the HTTP request from the client (up to 4096 bytes)
    message = tcpCliSock.recv(4096).decode('utf-8', errors='ignore')
    # Fill in end.

    print(message)

    # Extract the filename (URL) from the GET request line
    # e.g. "GET http://localhost:8888/www.google.com HTTP/1.1"
    # message.split()[1] gives "/www.google.com"
    # .partition("/")[2] strips the leading slash → "www.google.com"
    print(message.split()[1])
    filename = message.split()[1].partition("/")[2]
    print(filename)

    fileExist = "false"
    filetouse = "/" + filename
    print(filetouse)

    try:
        # Check whether the file exists in the cache
        f = open(filetouse[1:], "r")
        outputdata = f.readlines()
        fileExist = "true"

        # Proxy finds a cache hit → send cached response to client
        tcpCliSock.send("HTTP/1.0 200 OK\r\n".encode())
        tcpCliSock.send("Content-Type:text/html\r\n\r\n".encode())

        # Fill in start.
        # Send each cached line back to the client
        for line in outputdata:
            tcpCliSock.send(line.encode())
        # Fill in end.

        print('Read from cache')

    # Error handling for file not found in cache
    except IOError:
        if fileExist == "false":
            # Fill in start.
            # Create a new TCP socket to connect to the origin web server
            c = socket(AF_INET, SOCK_STREAM)
            # Fill in end.

            hostn = filename.replace("www.", "", 1)
            print(hostn)

            try:
                # Fill in start.
                # Connect to the origin web server on port 80
                c.connect((hostn, 80))
                # Fill in end.

                # Build and send the HTTP GET request to the origin server
                request = "GET http://" + filename + " HTTP/1.0\r\nHost: " + hostn + "\r\n\r\n"
                c.sendall(request.encode())

                # Fill in start.
                # Read the full response from the origin server into a buffer
                buffer = b""
                while True:
                    chunk = c.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                # Fill in end.

                # Save the response to the local cache file
                tmpFile = open("./" + filename, "wb")

                # Fill in start.
                # Write the response to the cache file and send it to the client
                tmpFile.write(buffer)
                tmpFile.close()
                tcpCliSock.sendall(buffer)
                # Fill in end.

            except Exception as e:
                print("Illegal request:", e)

        else:
            # Fill in start.
            # Send HTTP 404 Not Found response if file not in cache and fetch failed
            tcpCliSock.send("HTTP/1.0 404 Not Found\r\n".encode())
            tcpCliSock.send("Content-Type:text/html\r\n\r\n".encode())
            tcpCliSock.send(b"<html><body><h1>404 Not Found</h1></body></html>")
            # Fill in end.

    # Close the client socket
    tcpCliSock.close()

    # Fill in start.
    # (Server socket stays open to accept more connections)
    # Uncomment the line below only if you want a single-request server:
    # tcpSerSock.close()
    # Fill in end.
