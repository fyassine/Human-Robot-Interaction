import socket
 
# Setup socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("192.168.9.2", 8085))  # IP and port to listen on
 
print("Listening for UDP packets on 192.168.9.2:8085...")
while True:
    data, addr = sock.recvfrom(1024)  # buffer size in bytes
    print(f"Received from {addr}: {data.decode(errors='ignore')}")