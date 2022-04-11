_author__ = "Alex Li"
import socket
client = socket.socket()

#client.connect(('192.168.16.200',9999))
client.connect(('localhost',9999))

while True:
    cmd = input(">>:").strip()
    if len(cmd) == 0: continue
    if cmd.startswith("get"):
       client.send(cmd.encode())
       server_response = client.recv(1024)
       print("servr response:",server_response)
       client.send(b"ready to recv file")
       file_total_size = int(server_response.decode())
       received_size = 0
       filename = cmd.split()[1]
       f = open(filename + ".new","wb")
       while received_size < file_total_size:
         data = client.recv(1024)
         received_size += len(data)
         f.write(data)
         #print(file_total_size,received_size)
       else:
         print("file recv done", received_size,file_total_size)
         f.close()


client.close()

