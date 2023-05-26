import socket
import select

from network import ALL_CHAT_TYPE, KICK_TYPE, MAKE_OWNER_TYPE, MSG_LEN_SIZE, MUTE_TYPE, NAME_LEN_SIZE, PRIVATE_CHAT_TYPE, SERVER_PORT

MAX_MSG_LENGTH = 1024
SERVER_IP = "0.0.0.0"

SOCKET_ACCEPT_SOCKET_ARG = 0

MANAGER = 1
MUTED = 2

TIMEOUT_TIME = 0.05

MSG_TYPE_LEN = 1

CLIENT_SOCKET = 0
CLIENT_MESSAGE_QUEUE = 1
CLIENT_STATUS = 2
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

    output_msg = f"{name}: {client_msg}"

    for client in clients.values():
        if client[CLIENT_SOCKET] == sock:
            continue
        client[CLIENT_MESSAGE_QUEUE].append(output_msg)


def private_message(name, sock):
    name_len: str = sock.recv(NAME_LEN_SIZE).decode()

    if not name_len.isdigit():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    client_name = sock.recv(int(name_len)).decode()

    msg_len: str = sock.recv(MSG_LEN_SIZE).decode()

    if not msg_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    client_msg = sock.recv(int(msg_len)).decode()

    output_msg = f"!{name}: {client_msg}"

    clients[client_name][CLIENT_MESSAGE_QUEUE].append(output_msg)


def make_owner(name, sock):
    if not (clients[name][CLIENT_STATUS] & MANAGER):
        return

    owner_name_len: str = sock.recv(NAME_LEN_SIZE).decode()

    if not owner_name_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    owner_name = sock.recv(int(owner_name_len)).decode()

    clients[owner_name][CLIENT_STATUS] |= MANAGER


def mute_user(name, sock):
    if not (clients[name][CLIENT_STATUS] & MANAGER):
        return

    client_name_len: str = sock.recv(NAME_LEN_SIZE).decode()

    if not client_name_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    client_name = sock.recv(int(client_name_len)).decode()

    clients[client_name][CLIENT_STATUS] |= MUTED


def kick_user(name, sock):
    if not (clients[name][CLIENT_STATUS] & MANAGER):
        return

    client_name_len: str = sock.recv(NAME_LEN_SIZE).decode()

    if not client_name_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    client_name = sock.recv(int(client_name_len)).decode()

    client_socket = clients[client_name][CLIENT_SOCKET]
    clients.pop(client_name)
    socket_to_name.pop(client_socket)
    client_sockets.remove(client_socket)


MESSAGE_TYPES = {ALL_CHAT_TYPE: general_message, MAKE_OWNER_TYPE: make_owner,
                 KICK_TYPE: kick_user, MUTE_TYPE: mute_user, PRIVATE_CHAT_TYPE: private_message}


def manage_new_clients():
    name_len: str
    name: str
    if not non_named_sockets:
        return
    rlist, wlist, xlist = select.select(
        non_named_sockets, [], [], TIMEOUT_TIME)
    for current_socket in rlist:
        name_len = current_socket.recv(NAME_LEN_SIZE).decode()

        if not name_len.isdigit():
            non_named_sockets.remove(current_socket)
            current_socket.close()
            continue

        name = current_socket.recv(int(name_len)).decode()
        non_named_sockets.remove(current_socket)
        clients[name] = [current_socket, [], 0]
        socket_to_name[current_socket] = name
        client_sockets.add(current_socket)
        print(f"Added {name}")


def manage_clients():
    name_len: str
    name: str
    msg_type: int

    if not client_sockets:
        return
    rlist, wlist, xlist = select.select(
        client_sockets, client_sockets, [], TIMEOUT_TIME)
    for current_socket in rlist:
        name_len = current_socket.recv(NAME_LEN_SIZE).decode()

        if not name_len.isdigit():
            non_named_sockets.remove(current_socket)
            current_socket.close()
            continue

        name = current_socket.recv(int(name_len)).decode()

        msg_type = int(current_socket.recv(MSG_TYPE_LEN).decode())
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
        rlist, wlist, xlist = select.select(
            [server_socket], [], [], TIMEOUT_TIME)


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
