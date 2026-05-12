# server.py

import mmw
import json
import signal
import sys
from datetime import datetime

running = True
online_users = set()

def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)

mmw.initialize("127.0.0.1", 5000)
mmw.set_log_level(mmw.MmwLogLevel.MMW_LOG_LEVEL_OFF)

mmw.create_publisher("direct_message")
mmw.create_publisher("presence_update")

# ---------------- PRESENCE ----------------
def broadcast_presence():
    payload = {
        "users": sorted(list(online_users))
    }

    mmw.publish(
        "presence_update",
        json.dumps(payload),
        mmw.MmwReliability.MMW_RELIABLE
    )

def on_presence(topic, message):
    data = json.loads(message)

    username = data["username"]
    action = data["action"]

    changed = False

    if action == "join":
        if username not in online_users:
            online_users.add(username)
            changed = True

    elif action == "leave":
        if username in online_users:
            online_users.remove(username)
            changed = True

    if changed:
        print(f"{username} {action}ed")
        broadcast_presence()

# ---------------- DIRECT MESSAGE ----------------
def on_direct_message(topic, message):
    data = json.loads(message)

    payload = {
        "from": data["from"],
        "to": data["to"],
        "message": data["message"],
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

    print(
        f"[{payload['timestamp']}] "
        f"{payload['from']} -> "
        f"{payload['to']}: "
        f"{payload['message']}"
    )

    mmw.publish(
        "direct_message",
        json.dumps(payload),
        mmw.MmwReliability.MMW_RELIABLE
    )

presence_sub = mmw.create_subscriber(
    "presence",
    on_presence
)

dm_sub = mmw.create_subscriber(
    "send_direct_message",
    on_direct_message
)

print("MMW Messenger server running")

while running:
    pass

mmw.cleanup()
sys.exit(0)
