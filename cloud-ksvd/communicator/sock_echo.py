import socket
import time

HOST = ''
PORT = 9001


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((HOST, PORT))
print("Listening for Datagrams on port " + str(PORT))
while 1:
    data, addr = s.recvfrom(1024)
    print("Received: " + data)    