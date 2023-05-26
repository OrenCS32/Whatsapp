import socket
import tkinter as tk

from network import login, send_chat_message


def get_root() -> tk.Tk:
    root = tk.Tk()

    return root


def clear(root: tk.Tk):
    for widget in root.winfo_children():
        widget.destroy()


def main():
    root = get_root()
    clear(root)
    root.mainloop()


if __name__ == "__main__":
    main()
