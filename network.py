import socket

NAME_LEN_SIZE = 4
MSG_LEN_SIZE = 3

ALL_CHAT_TYPE = 1
MAKE_OWNER_TYPE = 2
KICK_TYPE = 3
MUTE_TYPE = 4
PRIVATE_CHAT_TYPE = 5


def send_message(sock: socket.socket, username: str, message_type: int, data: bytes):
    username_length = len(username)
    sock.send(
        f"{str(username_length).zfill(NAME_LEN_SIZE)}{username}{message_type}".encode() + data
    )


def send_chat_message(sock: socket.socket, username: str, message: str):
    return send_message(sock, username, ALL_CHAT_TYPE, f"{str(len(message)).zfill(MSG_LEN_SIZE)}{message}".encode())


def appoint_owner(sock: socket.socket, username: str, owner_name: str):
    return send_message(sock, username, MAKE_OWNER_TYPE, f"{str(len(owner_name)).zfill(NAME_LEN_SIZE)}{owner_name}".encode())


def send_kick_user(sock: socket.socket, username: str, kicked_name: str):
    return send_message(sock, username, KICK_TYPE, f"{str(len(kicked_name)).zfill(NAME_LEN_SIZE)}{kicked_name}".encode())


def send_mute_user(sock: socket.socket, username: str, muted_name: str):
    return send_message(sock, username, MUTE_TYPE, f"{str(len(muted_name)).zfill(NAME_LEN_SIZE)}{muted_name}".encode())


def send_private_message(sock: socket.socket, username: str, target: str, message: str):
    return send_message(
        sock,
        username,
        KICK_TYPE,
        f"{str(len(target)).zfill(NAME_LEN_SIZE)}{target}{str(len(message)).zfill(MSG_LEN_SIZE)}{message}".encode()
    )
