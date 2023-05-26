import socket

from network import login, send_chat_message

client = socket.socket()

client.connect(("127.0.0.1", 5555))

username = input("username: ")
login(client, username)

send_chat_message(client, username, "hello there")

while True:
    print(client.recv(1024))
