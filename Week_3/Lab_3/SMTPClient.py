# SMTPClient.py
# Lab 3: SMTP Mail Client
# Advanced Computer Networks
# Implements SMTP protocol manually using raw TCP sockets (no smtplib)

from socket import *
import base64

# ── Email configuration ────────────────────────────────────────────────────────
# Gmail SMTP with TLS upgrade (STARTTLS on port 587)
# NOTE: Use an App Password (not your Gmail password).
# Generate at: myaccount.google.com → Security → App Passwords
SENDER    = 'arungadde0@gmail.com'         # Replace with your Gmail address
RECIPIENT = 'agadde37312@ucumberlands.edu'       # Replace with the recipient's address
USERNAME  = 'arungadde0@gmail.com'         # Same as SENDER
PASSWORD  = 'xxxxxxxxxxxx'      # 16-char Gmail App Password (no spaces)

msg    = "\r\n I love computer networks!"
endmsg = "\r\n.\r\n"

# ── Choose a mail server ───────────────────────────────────────────────────────
# Fill in start
mailserver = ('smtp.gmail.com', 587)      # Gmail SMTP server, port 587 (STARTTLS)
# Fill in end

# ── Create socket and establish TCP connection with mail server ────────────────
# Fill in start
clientSocket = socket(AF_INET, SOCK_STREAM)   # Create TCP socket
clientSocket.connect(mailserver)              # Connect to Gmail SMTP server
# Fill in end

# Receive server greeting (should start with 220)
recv = clientSocket.recv(1024).decode()
print(f"[S] {recv.strip()}")
if recv[:3] != '220':
    print('220 reply not received from server.')

# ── HELO — Introduce ourselves to the server ───────────────────────────────────
heloCommand = 'HELO Alice\r\n'
clientSocket.send(heloCommand.encode())
recv1 = clientSocket.recv(1024).decode()
print(f"[C] HELO Alice")
print(f"[S] {recv1.strip()}")
if recv1[:3] != '250':
    print('250 reply not received from server.')

# ── STARTTLS — Upgrade plain TCP to encrypted TLS connection ──────────────────
# Fill in start
clientSocket.send('STARTTLS\r\n'.encode())
recvTLS = clientSocket.recv(1024).decode()
print(f"[C] STARTTLS")
print(f"[S] {recvTLS.strip()}")

# Wrap the plain TCP socket in TLS encryption
import ssl
context = ssl.create_default_context()
clientSocket = context.wrap_socket(clientSocket, server_hostname='smtp.gmail.com')
print("[INFO] TLS handshake complete — connection is now encrypted")

# Re-introduce ourselves after TLS upgrade (required by RFC 3207)
clientSocket.send('EHLO Alice\r\n'.encode())
recvEHLO = clientSocket.recv(1024).decode()
print(f"[C] EHLO Alice")
print(f"[S] {recvEHLO.strip()}")
# Fill in end

# ── AUTH LOGIN — Authenticate with Base64-encoded credentials ─────────────────
# Fill in start
clientSocket.send('AUTH LOGIN\r\n'.encode())
recvAuth = clientSocket.recv(1024).decode()
print(f"[C] AUTH LOGIN")
print(f"[S] {recvAuth.strip()}")

# Send Base64-encoded username
b64_user = base64.b64encode(USERNAME.encode()).decode()
clientSocket.send((b64_user + '\r\n').encode())
recvUser = clientSocket.recv(1024).decode()
print(f"[C] <username base64>")
print(f"[S] {recvUser.strip()}")

# Send Base64-encoded password (App Password — NOT your Gmail login password)
b64_pass = base64.b64encode(PASSWORD.encode()).decode()
clientSocket.send((b64_pass + '\r\n').encode())
recvPass = clientSocket.recv(1024).decode()
print(f"[C] <password base64>")
print(f"[S] {recvPass.strip()}")
if recvPass[:3] != '235':
    print('Authentication failed. Check App Password and username.')
# Fill in end

# ── MAIL FROM — Tell the server who is sending the email ──────────────────────
# Fill in start
mailFromCommand = f'MAIL FROM:<{SENDER}>\r\n'
clientSocket.send(mailFromCommand.encode())
recv2 = clientSocket.recv(1024).decode()
print(f"[C] MAIL FROM:<{SENDER}>")
print(f"[S] {recv2.strip()}")
if recv2[:3] != '250':
    print('250 reply not received from server.')
# Fill in end

# ── RCPT TO — Tell the server who will receive the email ──────────────────────
# Fill in start
rcptToCommand = f'RCPT TO:<{RECIPIENT}>\r\n'
clientSocket.send(rcptToCommand.encode())
recv3 = clientSocket.recv(1024).decode()
print(f"[C] RCPT TO:<{RECIPIENT}>")
print(f"[S] {recv3.strip()}")
if recv3[:3] != '250':
    print('250 reply not received from server.')
# Fill in end

# ── DATA — Signal that the email body is about to be sent ────────────────────
# Fill in start
clientSocket.send('DATA\r\n'.encode())
recv4 = clientSocket.recv(1024).decode()
print(f"[C] DATA")
print(f"[S] {recv4.strip()}")
if recv4[:3] != '354':
    print('354 reply not received from server.')
# Fill in end

# ── Send the email headers and body ───────────────────────────────────────────
# Fill in start
email_headers = (
    f"From: {SENDER}\r\n"
    f"To: {RECIPIENT}\r\n"
    f"Subject: Lab 3 SMTP Test — Python Mail Client\r\n"
    f"MIME-Version: 1.0\r\n"
    f"Content-Type: text/plain; charset=UTF-8\r\n"
    f"\r\n"
)
clientSocket.send(email_headers.encode())
clientSocket.send(msg.encode())
print(f"[C] <email headers + body>")
# Fill in end

# ── End the message with a single period on its own line ──────────────────────
# Fill in start
clientSocket.send(endmsg.encode())
recv5 = clientSocket.recv(1024).decode()
print(f"[C] <CRLF>.<CRLF>  (end of message)")
print(f"[S] {recv5.strip()}")
if recv5[:3] != '250':
    print('250 reply not received from server.')
# Fill in end

# ── QUIT — Close the SMTP session ─────────────────────────────────────────────
# Fill in start
clientSocket.send('QUIT\r\n'.encode())
recv6 = clientSocket.recv(1024).decode()
print(f"[C] QUIT")
print(f"[S] {recv6.strip()}")
if recv6[:3] != '221':
    print('221 reply not received from server.')
# Fill in end

clientSocket.close()
print("\n[INFO] Email sent successfully. Check your inbox (or spam folder).")
