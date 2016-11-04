import socket
import random

HOST = '172.27.205.193'    # The remote host
PORT = 9001              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
d = []
for x in range(100):
    d.append(int(300*random.random()))


msg = str(d)
s.sendto(msg, (HOST, PORT))        
print("Sent message")
s.close()
print("Closing and quitting")

