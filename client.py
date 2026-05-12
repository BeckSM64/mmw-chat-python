# client.py

import tkinter as tk
from tkinter import scrolledtext
import json
import mmw

# ---------------- LOGIN ----------------
login = tk.Tk()
login.title("MMW Messenger Login")
login.geometry("300x120")
login.resizable(False, False)

username_var = tk.StringVar()

tk.Label(
    login,
    text="Screen Name",
    font=("Tahoma", 11)
).pack(pady=(10, 5))

entry = tk.Entry(
    login,
    textvariable=username_var,
    font=("Tahoma", 11)
)

entry.pack(padx=20, fill=tk.X)
entry.focus()

def connect():
    login.destroy()

tk.Button(
    login,
    text="Connect",
    command=connect
).pack(pady=10)

login.bind("<Return>", lambda e: connect())

login.mainloop()

username = username_var.get().strip()

if username == "":
    username = "Anonymous"

# ---------------- MMW ----------------
mmw.initialize("127.0.0.1", 5000)
mmw.set_log_level(mmw.MmwLogLevel.MMW_LOG_LEVEL_OFF)

mmw.create_publisher("presence")
mmw.create_publisher("send_direct_message")

# ---------------- MAIN WINDOW ----------------
root = tk.Tk()
root.title(f"MMW Messenger - {username}")
root.geometry("1000x650")

# conversations:
# {
#   "alice": [
#       "[12:00] alice: hi"
#   ]
# }
conversations = {}

selected_buddy = None

# ---------------- LEFT SIDE ----------------
left_frame = tk.Frame(
    root,
    width=220,
    bg="#d4d0c8"
)

left_frame.pack(side=tk.LEFT, fill=tk.Y)
left_frame.pack_propagate(False)

buddy_title = tk.Label(
    left_frame,
    text="Buddy List",
    bg="#0a246a",
    fg="white",
    font=("Tahoma", 11, "bold"),
    pady=6
)

buddy_title.pack(fill=tk.X)

buddy_list = tk.Listbox(
    left_frame,
    font=("Tahoma", 10)
)

buddy_list.pack(
    fill=tk.BOTH,
    expand=True,
    padx=6,
    pady=6
)

# ---------------- RIGHT SIDE ----------------
right_frame = tk.Frame(root)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

chat_header = tk.Label(
    right_frame,
    text="No conversation selected",
    anchor="w",
    font=("Tahoma", 11, "bold"),
    padx=10,
    pady=8
)

chat_header.pack(fill=tk.X)

chat_box = scrolledtext.ScrolledText(
    right_frame,
    state='disabled',
    wrap=tk.WORD,
    font=("Tahoma", 10)
)

chat_box.pack(
    fill=tk.BOTH,
    expand=True,
    padx=10,
    pady=10
)

bottom_frame = tk.Frame(right_frame)
bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

message_entry = tk.Entry(
    bottom_frame,
    font=("Tahoma", 10)
)

message_entry.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True,
    padx=(0, 10)
)

# ---------------- CHAT FUNCTIONS ----------------
def redraw_chat():
    chat_box.configure(state='normal')
    chat_box.delete("1.0", tk.END)

    if selected_buddy is not None:
        for line in conversations.get(selected_buddy, []):
            chat_box.insert(tk.END, line + "\n")

    chat_box.configure(state='disabled')
    chat_box.yview(tk.END)

def append_conversation(user, line):

    if user not in conversations:
        conversations[user] = []

    conversations[user].append(line)

    if selected_buddy == user:
        redraw_chat()

# ---------------- SELECT BUDDY ----------------
def on_select_buddy(event):
    global selected_buddy

    selection = buddy_list.curselection()

    if not selection:
        return

    buddy = buddy_list.get(selection[0])

    selected_buddy = buddy

    chat_header.config(
        text=f"Conversation with {buddy}"
    )

    redraw_chat()

buddy_list.bind("<<ListboxSelect>>", on_select_buddy)

# ---------------- SEND MESSAGE ----------------
def send_message(event=None):

    if selected_buddy is None:
        return

    text = message_entry.get().strip()

    if text == "":
        return

    payload = {
        "from": username,
        "to": selected_buddy,
        "message": text
    }

    mmw.publish(
        "send_direct_message",
        json.dumps(payload),
        mmw.MmwReliability.MMW_RELIABLE
    )

    line = (
        f"[You]: {text}"
    )

    append_conversation(selected_buddy, line)

    message_entry.delete(0, tk.END)

send_button = tk.Button(
    bottom_frame,
    text="Send",
    width=10,
    command=send_message
)

send_button.pack(side=tk.RIGHT)

message_entry.bind("<Return>", send_message)

# ---------------- RECEIVE PRESENCE ----------------
def on_presence_update(topic, message):

    data = json.loads(message)

    current_selection = selected_buddy

    buddy_list.delete(0, tk.END)

    for user in data["users"]:

        if user == username:
            continue

        buddy_list.insert(tk.END, user)

    # restore selection if possible
    if current_selection is not None:
        users = data["users"]

        if current_selection in users:
            idx = users.index(current_selection)

            if username in users and idx > users.index(username):
                idx -= 1

            buddy_list.selection_set(idx)

presence_sub = mmw.create_subscriber(
    "presence_update",
    on_presence_update
)

# ---------------- RECEIVE DIRECT MESSAGE ----------------
def on_direct_message(topic, message):

    data = json.loads(message)

    sender = data["from"]
    recipient = data["to"]

    # only process if message involves us
    if sender != username and recipient != username:
        return

    other_user = sender if sender != username else recipient

    line = (
        f"[{data['timestamp']}] "
        f"{sender}: "
        f"{data['message']}"
    )

    root.after(
        0,
        append_conversation,
        other_user,
        line
    )

dm_sub = mmw.create_subscriber(
    "direct_message",
    on_direct_message
)

# ---------------- CONNECT ----------------
mmw.publish(
    "presence",
    json.dumps({
        "username": username,
        "action": "join"
    }),
    mmw.MmwReliability.MMW_RELIABLE
)

# ---------------- CLEANUP ----------------
def on_close():

    mmw.publish(
        "presence",
        json.dumps({
            "username": username,
            "action": "leave"
        }),
        mmw.MmwReliability.MMW_RELIABLE
    )

    mmw.cleanup()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
