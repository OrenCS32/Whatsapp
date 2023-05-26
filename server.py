import socket
import select
import time

from network import ALL_CHAT_TYPE, KICK_TYPE, MAKE_OWNER_TYPE, MSG_LEN_SIZE, MUTE_TYPE, NAME_LEN_SIZE, \
    PRIVATE_CHAT_TYPE, is_socket_closed, VIEW_ALL_COMMAND

MAX_MSG_LENGTH = 1024
SERVER_PORT = 5555
SERVER_IP = "0.0.0.0"

MANAGER_PREFIX = '@'
USERNAME_TAKEN = "used"
USERNAME_OKAY = "okay"
USERNAME_EMPTY = "empt"
USERNAME_MANAGER = "nota"

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


def broadcast_message(msg):
    for name in clients.keys():
        clients[name][CLIENT_MESSAGE_QUEUE].append(msg)


def format_name(name):
    if clients[name][CLIENT_STATUS] & MANAGER:
        return MANAGER_PREFIX + name
    return name


def get_users() -> str:
    return ', '.join(clients.keys())


def general_message(name, sock):
    """ Send message to Every client """
    msg_len: str = sock.recv(MSG_LEN_SIZE).decode()

    if not msg_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    client_msg = sock.recv(int(msg_len)).decode()

    if clients[name][CLIENT_STATUS] & MUTED:
        print(f"{name} tried broadcasting {client_msg}")
        return

    output_msg = f"{format_name(name)}: {client_msg}"

    print(output_msg)
    broadcast_message(output_msg)

    if client_msg == VIEW_ALL_COMMAND:
        broadcast_message(f"All users: {get_users()}")


def private_message(name, sock):
    """ Send message to a specific client """
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

    if client_name not in clients:
        print(f"{name} tried to contact unknown user {client_name}")
        return

    name = format_name(name)

    output_msg = f"!{name}: {client_msg}"

    print(f"{name} -> {format_name(client_name)}: {client_msg}")
    clients[client_name][CLIENT_MESSAGE_QUEUE].append(output_msg)


def make_owner(name, sock):
    """ Make a user an owner """
    owner_name_len: str = sock.recv(NAME_LEN_SIZE).decode()

    if not owner_name_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    owner_name = sock.recv(int(owner_name_len)).decode()

    if not (clients[name][CLIENT_STATUS] & MANAGER):
        print(f"{name} tried to appoint {owner_name}, but he is not a manager")
        return

    if owner_name not in clients:
        print(f"{name} tried to appoint unknown user {owner_name}")
        return

    output_msg = f"{format_name(name)} made {format_name(owner_name)} an owner."
    print(output_msg)
    broadcast_message(output_msg)
    clients[owner_name][CLIENT_STATUS] |= MANAGER


def mute_user(name, sock):
    """ Mute a user """

    client_name_len: str = sock.recv(NAME_LEN_SIZE).decode()

    if not client_name_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    client_name = sock.recv(int(client_name_len)).decode()

    if not (clients[name][CLIENT_STATUS] & MANAGER):
        print(f"{name} tried to mute {client_name}, but he is not a manager")
        return

    if client_name not in clients:
        print(f"{name} tried to mute unknown user {client_name}")
        return

    clients[client_name][CLIENT_STATUS] |= MUTED
    output_msg = f"{format_name(name)} muted {format_name(client_name)}."
    print(output_msg)
    broadcast_message(output_msg)


def kick_user(name, sock):
    """ Kick a user """

    client_name_len: str = sock.recv(NAME_LEN_SIZE).decode()

    if not client_name_len.isnumeric():
        clients.pop(sock)
        client_sockets.remove(sock)
        sock.close()
        return

    client_name = sock.recv(int(client_name_len)).decode()

    if not (clients[name][CLIENT_STATUS] & MANAGER):
        print(f"{name} tried to kick {client_name}, but he is not a manager")
        return

    if client_name not in clients:
        print(f"{name} tried to kick unknown user {client_name}")
        return

    """ Remove user """
    client_socket = clients[client_name][CLIENT_SOCKET]
    clients.pop(client_name)
    socket_to_name.pop(client_socket)
    client_sockets.remove(client_socket)
    client_socket.close()

    output_msg = f"{format_name(name)} kicked {format_name(client_name)}."
    print(output_msg)
    broadcast_message(output_msg)


MESSAGE_TYPES = {ALL_CHAT_TYPE: general_message, MAKE_OWNER_TYPE: make_owner,
                 KICK_TYPE: kick_user, MUTE_TYPE: mute_user, PRIVATE_CHAT_TYPE: private_message}


def add_user(sock: socket.socket):
    name_len: str
    name: str
    name_len = sock.recv(NAME_LEN_SIZE).decode()

    if not name_len.isnumeric():
        non_named_sockets.remove(sock)
        sock.close()
        return

    if int(name_len) == 0:
        sock.send(USERNAME_EMPTY.encode())
        return

    """ Add the user """
    name = sock.recv(int(name_len)).decode()

    if name in clients:
        sock.send(USERNAME_TAKEN.encode())
        return

    if name[0] == MANAGER_PREFIX:
        sock.send(USERNAME_MANAGER.encode())
        return

    non_named_sockets.remove(sock)
    if name == "admin":
        clients[name] = [sock, [], MANAGER]
    else:
        clients[name] = [sock, [], 0]
    socket_to_name[sock] = name
    client_sockets.add(sock)
    sock.send(USERNAME_OKAY.encode())

    broadcast_message(f"{name} has joined the chat")
    print(f"Added {name}")


def manage_new_clients():
    """ Manage clients with no name """

    if not non_named_sockets:
        return

    rlist, _, _ = select.select(non_named_sockets, [], [], TIMEOUT_TIME)

    for current_socket in rlist:
        if is_socket_closed(current_socket):
            """ Remove the socket if it was closed """
            non_named_sockets.remove(current_socket)
            current_socket.close()

        add_user(current_socket)


def handle_incoming_data(sock: socket.socket):
    if is_socket_closed(sock):
        """ Remove socket if it is closed """
        name = socket_to_name.pop(sock)
        clients.pop(name)
        client_sockets.remove(sock)
        sock.close()

        broadcast_message(f"{name} has left the chat.")
        print(f"{name} has left the chat.")
        return

    name_len = sock.recv(NAME_LEN_SIZE).decode()

    if not name_len.isdigit():
        sock.recv(MSG_LEN_SIZE)
        return

    name = sock.recv(int(name_len)).decode()

    if name not in clients:
        print(f"Unknown name {name}")
        sock.recv(MAX_MSG_LENGTH)
        return

    msg_type = int(sock.recv(MSG_TYPE_LEN).decode())
    if msg_type not in MESSAGE_TYPES:
        print("Unknown message type")
        sock.recv(MAX_MSG_LENGTH)  # Clear messages from the socket
        return

    MESSAGE_TYPES[msg_type](name, sock)


def send_data(sock: socket.socket):
    name = socket_to_name[sock]
    for msg in clients[name][CLIENT_MESSAGE_QUEUE]:
        output = f"{time.asctime()} {msg}"
        msg_len = str(len(output)).rjust(MSG_LEN_SIZE, '0')
        sock.send(f"{msg_len}{output}".encode())

    clients[name][CLIENT_MESSAGE_QUEUE].clear()


def manage_clients():
    """ Manages all named clients """
    name_len: str
    name: str
    msg_type: int

    if not client_sockets:
        return

    rlist, _, _ = select.select(client_sockets, [], [], TIMEOUT_TIME)

    """ Receive all messages from the clients """
    for current_socket in rlist:
        handle_incoming_data(current_socket)

    """ Send all the messages """
    if not client_sockets:
        return

    _, wlist, _ = select.select([], client_sockets, [], TIMEOUT_TIME)
    for current_socket in wlist:
        send_data(current_socket)


def receive_new_connection(server_socket):
    """ Add new users to the server """
    rlist, _, _ = select.select([server_socket], [], [], TIMEOUT_TIME)
    while rlist:
        new_socket = server_socket.accept()[SOCKET_ACCEPT_SOCKET_ARG]
        non_named_sockets.add(new_socket)
        rlist, _, _ = select.select([server_socket], [], [], TIMEOUT_TIME)


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
