import socket
import tkinter as tk
import tkinter.messagebox as msgbox

from network import SERVER_PORT, connect, login, send_chat_message


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
        clear(root)
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


def main():
    root = get_root()
    clear(root)

    login_page(root)

    root.mainloop()


if __name__ == "__main__":
    main()
