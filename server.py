# server.py

import mmw
import json
import signal
import sys
from datetime import datetime

running = True

def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)

mmw.initialize("127.0.0.1", 5000)
mmw.set_log_level(mmw.MmwLogLevel.MMW_LOG_LEVEL_OFF)

mmw.create_publisher("chat_broadcast")

def on_chat_message(topic, message):
    data = json.loads(message)

    payload = {
        "username": data["username"],
        "message": data["message"],
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

    print(
        f"[{payload['timestamp']}] "
        f"{payload['username']}: "
        f"{payload['message']}"
    )

    mmw.publish(
        "chat_broadcast",
        json.dumps(payload),
        mmw.MmwReliability.MMW_RELIABLE
    )

chat_sub = mmw.create_subscriber(
    "chat_message",
    on_chat_message
)

print("Chat server running")

while running:
    pass

mmw.cleanup()
sys.exit(0)
