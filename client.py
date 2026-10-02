import socket
import struct

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 65432))

linger_enabled = 1
linger_time = 0
linger_struct = struct.pack("ii", linger_enabled, linger_time)

# Apply SO_LINGER at the SOL_SOCKET level
client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger_struct)

while True:
    msg = input("$ ")

    msg = msg.encode()

    client.sendall(msg)

    print(client.recv(1024).decode())
