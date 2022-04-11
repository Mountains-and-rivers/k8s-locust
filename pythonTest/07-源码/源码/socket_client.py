__author__ = "Alex Li"
#客户端
import socket

client = socket.socket() #声明socket类型，同时生成socket连接对象
client.connect(('localhost',6969))

while True:
    msg = input(">>:").strip()
    if len(msg) == 0:continue
    client.send(msg.encode("utf-8"))
    data = client.recv(10240)
    print("recv:",data.decode())

client.close()
