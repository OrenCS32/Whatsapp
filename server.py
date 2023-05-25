import socket
import select

MAX_MSG_LENGTH = 1024
SERVER_PORT = 5555
SERVER_IP = "0.0.0.0"

SOCKET_ACCEPT_SOCKET_ARG = 0

NOT_MANAGER = 0
MANAGER = 1

TIMEOUT_TIME = 0.05

NAME_LEN_SIZE = 1
MSG_LEN_SIZE = 3

MSG_TYPE_LEN = 1

ALL_CHAT_TYPE = "1"
MAKE_OWNER_TYPE = "2"
KICK_TYPE = "3"
MUTE_TYPE = "4"
PRIVATE_CHAT_TYPE = "5"

CLIENT_SOCKET = 0
CLIENT_MESSAGE_QUEUE = 1
CLIENT_IS_OWNER = 2
clients = dict()
socket_to_name = dict()

client_sockets = set()
non_named_sockets = set()


def general_message(name, sock):
    msg_len: str = sock.recv(MSG_LEN_SIZE).decode()

    if not msg_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    client_msg = sock.recv(int(msg_len)).decode()

    output_msg = f"{len(name)}{name}{ALL_CHAT_TYPE}{msg_len}{client_msg}"

    for client in clients.values():
        if client[CLIENT_SOCKET] == sock:
            continue
        client[CLIENT_MESSAGE_QUEUE].append(output_msg)


MESSAGE_TYPES = {ALL_CHAT_TYPE: general_message}


def manage_new_clients():
    name_len: str
    name: str
    if not non_named_sockets:
        return
    rlist, wlist, xlist = select.select(non_named_sockets, [], [], TIMEOUT_TIME)
    for current_socket in rlist:
        name_len = current_socket.recv(NAME_LEN_SIZE).decode()

        if not name_len.isdigit():
            non_named_sockets.remove(current_socket)
            current_socket.close()
            continue

        name = current_socket.recv(int(name_len)).decode()
        non_named_sockets.remove(current_socket)
        clients[name] = [current_socket, [], NOT_MANAGER]
        socket_to_name[current_socket] = name
        client_sockets.add(current_socket)
        print(f"Added {name}")


def manage_clients():
    name_len: str
    name: str
    msg_type: str
    if not client_sockets:
        return
    rlist, wlist, xlist = select.select(client_sockets, client_sockets, [], TIMEOUT_TIME)
    for current_socket in rlist:
        name_len = current_socket.recv(NAME_LEN_SIZE).decode()

        if not name_len.isdigit():
            non_named_sockets.remove(current_socket)
            current_socket.close()
            continue

        name = current_socket.recv(int(name_len)).decode()

        msg_type = current_socket.recv(MSG_TYPE_LEN).decode()
        if not msg_type in MESSAGE_TYPES:
            print("wahgh")
            continue

        MESSAGE_TYPES[msg_type](name, current_socket)

    for current_socket in wlist:
        name = socket_to_name[current_socket]
        for msg in clients[name][CLIENT_MESSAGE_QUEUE]:
            current_socket.send(msg.encode())

        clients[name][CLIENT_MESSAGE_QUEUE].clear()


def receive_new_connection(server_socket):
    rlist, wlist, xlist = select.select([server_socket], [], [], TIMEOUT_TIME)
    while rlist:
        new_socket = server_socket.accept()[SOCKET_ACCEPT_SOCKET_ARG]
        non_named_sockets.add(new_socket)
        rlist, wlist, xlist = select.select([server_socket], [], [], TIMEOUT_TIME)


def manage_server(server_socket):
    while True:
        manage_new_clients()
        manage_clients()
        receive_new_connection(server_socket)


def main():
    print("Setting up server...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen()
    print("Listening for clients...")
    manage_server(server_socket)


if __name__ == "__main__":
    main()
