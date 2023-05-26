import socket
from threading import Thread
import tkinter as tk
import tkinter.messagebox as msgbox
from typing import Callable, List, Optional

from network import SERVER_PORT, appoint_owner, connect, login, send_chat_message, send_mute_user, send_private_message
from scrollable_frame import ScrollableFrame


def get_root() -> tk.Tk:
    root = tk.Tk()

    return root


def clear(root: tk.Tk):
    for widget in root.winfo_children():
        widget.destroy()


def on_login(root: tk.Tk, ip: str, port: int, username: str):
    if not username or not ip:
        return

    try:
        client = connect(ip, port)
        login(client, username)
        root.title(username)
        main_page(root, client, username)
    except ConnectionError:
        msgbox.showerror(title="Error", message="Could not connect to server")


def login_page(root: tk.Tk):
    clear(root)

    ip_var = tk.StringVar(value="127.0.0.1")
    port_var = tk.IntVar(value=SERVER_PORT)
    username_var = tk.StringVar(value=socket.gethostname())

    tk.Label(root, text='Ip').grid()
    tk.Entry(root, textvariable=ip_var).grid(row=0, column=1)
    tk.Label(root, text='Port').grid(row=1)
    tk.Entry(root, textvariable=port_var).grid(column=1, row=1)
    tk.Label(root, text='Username').grid(row=2)
    tk.Entry(root, textvariable=username_var).grid(column=1, row=2)
    tk.Button(root, text='Connect', command=lambda: on_login(root, ip_var.get(), port_var.get(), username_var.get())).grid(
        row=3, columnspan=2)


def recv_thread(root: tk.Tk, client: socket.socket, username: str, messages: List[str]):
    message = client.recv(1024).decode()
    main_page(root, client, username, [*messages, message])
    exit(0)


def on_send_chat(client: socket.socket, username: str, message_var: tk.StringVar):
    send_chat_message(client, username, message_var.get())
    message_var.set("")


def get_user(root: tk.Tk, on_username: Callable[[str], None]):
    modal = tk.Toplevel(root)
    username_var = tk.StringVar()

    def on_click():
        if not username_var.get():
            return
        on_username(username_var.get())
        modal.destroy()
        modal.update()

    tk.Label(modal, text='Username').grid()
    tk.Entry(modal, textvariable=username_var).grid(row=0, column=1)
    tk.Button(modal, text='Choose Target User',
              command=on_click).grid(row=0, column=2)


def on_send_private(root: tk.Tk, client: socket.socket, username: str, message_var: tk.StringVar):
    message = message_var.get()
    message_var.set("")

    get_user(root,
             lambda target: send_private_message(
                 client, username, target, message)
             )


def on_mute(root: tk.Tk, client: socket.socket, username: str):
    get_user(root, lambda target: send_mute_user(client, username, target))


def on_appoint_owner(root: tk.Tk, client: socket.socket, username: str):
    get_user(root, lambda target: appoint_owner(client, username, target))


def on_kick(root: tk.Tk, client: socket.socket, username: str):
    get_user(root, lambda target: appoint_owner(client, username, target))


def main_page(root: tk.Tk, client: socket.socket, username: str,  messages: Optional[List[str]] = None):
    clear(root)

    if not messages:
        messages = []

    root.geometry("750x400")
    message_var = tk.StringVar()

    wrapper = tk.Frame()
    wrapper.place(relx=0.25)
    frame = ScrollableFrame(wrapper)
    frame.grid(columnspan=3)
    for message in messages:
        tk.Label(frame.scrollable_frame, text=message,
                 bg="white", anchor="w", width=550).pack()
    tk.Entry(wrapper, textvariable=message_var).grid(
        row=1, column=0, sticky="ew")
    tk.Button(wrapper, text='Send', command=lambda: on_send_chat(
        client, username, message_var)
    ).grid(row=1, column=1)
    tk.Button(wrapper, text='Send Private',
              command=lambda: on_send_private(
                  root, client, username, message_var)
              ).grid(row=1, column=2)

    tk.Button(wrapper, text='Mute', command=lambda: on_mute(
        root, client, username)
    ).grid(row=2, column=0)
    tk.Button(wrapper, text='Appoint manager', command=lambda: on_appoint_owner(
        root, client, username)
    ).grid(row=2, column=1)
    tk.Button(wrapper, text='Kick', command=lambda: on_kick(
        root, client, username)
    ).grid(row=2, column=2)

    Thread(target=recv_thread, args=(root, client,
           username, messages), daemon=True).start()


def main():
    root = get_root()
    clear(root)

    login_page(root)

    root.mainloop()


if __name__ == "__main__":
    main()
