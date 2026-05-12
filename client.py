# client.py

import tkinter as tk
from tkinter import scrolledtext
import threading
import json
import mmw

# ---------------- USERNAME ----------------
username_window = tk.Tk()
username_window.title("Username")
username_window.geometry("300x100")

username_var = tk.StringVar()

tk.Label(username_window, text="Enter username").pack(pady=5)
entry = tk.Entry(username_window, textvariable=username_var)
entry.pack(pady=5)

done = False

def submit_username():
    global done
    done = True
    username_window.destroy()

tk.Button(
    username_window,
    text="Connect",
    command=submit_username
).pack(pady=5)

username_window.mainloop()

username = username_var.get().strip()

if username == "":
    username = "Anonymous"

# ---------------- MMW ----------------
mmw.initialize("127.0.0.1", 5000)
mmw.set_log_level(mmw.MmwLogLevel.MMW_LOG_LEVEL_OFF)

mmw.create_publisher("chat_message")

# ---------------- GUI ----------------
root = tk.Tk()
root.title(f"MMW Chat - {username}")
root.geometry("700x500")

chat_box = scrolledtext.ScrolledText(
    root,
    state='disabled',
    wrap=tk.WORD,
    font=("Consolas", 11)
)

chat_box.pack(
    padx=10,
    pady=10,
    fill=tk.BOTH,
    expand=True
)

bottom_frame = tk.Frame(root)
bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

message_entry = tk.Entry(
    bottom_frame,
    font=("Consolas", 11)
)

message_entry.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True,
    padx=(0, 10)
)

# ---------------- MESSAGE DISPLAY ----------------
def append_message(text):
    chat_box.configure(state='normal')
    chat_box.insert(tk.END, text + "\n")
    chat_box.configure(state='disabled')
    chat_box.yview(tk.END)

# ---------------- RECEIVE CALLBACK ----------------
def on_chat_message(topic, message):
    data = json.loads(message)

    text = (
        f"[{data['timestamp']}] "
        f"{data['username']}: "
        f"{data['message']}"
    )

    root.after(0, append_message, text)

chat_sub = mmw.create_subscriber(
    "chat_broadcast",
    on_chat_message
)

# ---------------- SEND ----------------
def send_message(event=None):
    text = message_entry.get().strip()

    if text == "":
        return

    payload = {
        "username": username,
        "message": text
    }

    mmw.publish(
        "chat_message",
        json.dumps(payload),
        mmw.MmwReliability.MMW_RELIABLE
    )

    message_entry.delete(0, tk.END)

send_button = tk.Button(
    bottom_frame,
    text="Send",
    width=10,
    command=send_message
)

send_button.pack(side=tk.RIGHT)

message_entry.bind("<Return>", send_message)

# ---------------- CLEANUP ----------------
def on_close():
    mmw.cleanup()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

append_message("Connected to server")

root.mainloop()
