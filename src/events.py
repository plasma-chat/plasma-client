# Copyright 2022 iiPython

# Modules
import os
import time
import tempfile
from copy import copy
from typing import Tuple
from threading import Thread
from datetime import datetime
from types import FunctionType
from iipython import keys, readchar, clear, color, Socket

from .config import config
from .themes import ThemeManager
from .plugins import PluginManager
try:
    from src.vendor.termimg.image import TermImage

except ImportError:
    TermImage = None

# Initialization
def scale_bytes(size: int) -> str:
    for unit in ["", "K", "M", "G"]:
        if abs(size) < 1024:
            return f"{size:3.1f}{unit}B"

        size /= 1024

    return f"{size:.1f}TB"

def truncate(text: str, length: int) -> str:
    oldlen, text = len(text), text[:length]
    if len(text) != oldlen:
        text += "..."

    return text

# Context
class EventContext(object):
    def __init__(self, data: dict, in_history: bool = False) -> None:
        self.raw = data
        self.type = data["type"]
        self.data = data["data"]
        self.server = data["server"]
        self.timestamp = data["ts"]
        self.in_history = in_history

# Event Manager
class EventManager(object):
    def __init__(self) -> None:
        self.sock, self.pluginmgr = None, None
        self.events, self.themes = {}, ThemeManager()

        # Shared data (for use by plugins)
        self.shared = {"input": "", "spacer": " " * os.get_terminal_size()[0], "history": [], "config": config}

        # Formatters
        self.data_formatters = {
            "m.msg": lambda d: (d.data["author"]["username"], self.pluginmgr.on_msg(d.data["content"])),
            "m.bin": self.format_bin,
            "u.join": lambda d: ("System", f"[blue]{d.data['username']} [green]has joined the server."),
            "u.leave": lambda d: ("System", f"[blue]{d.data['username']} [red]has left the server.")
        }
        self.time_formatters = {
            "12h": lambda ts: datetime.fromtimestamp(ts).strftime("%I:%M %p"),
            "24h": lambda ts: datetime.fromtimestamp(ts).strftime("%H:%M"),
            "utc12h": lambda ts: datetime.utcfromtimestamp(ts).strftime("%I:%M %p"),
            "utc24h": lambda ts: datetime.utcfromtimestamp(ts).strftime("%H:%M")
        }

    def format_bin(self, d: EventContext) -> tuple:
        def print_image(data: EventContext) -> None:
            file = tempfile.NamedTemporaryFile(delete = False, suffix = "." + d.data["filename"].split(".")[-1])
            file.write(bytes.fromhex(data.data["binary"]))
            d.data["content"] = str(TermImage.from_file(file.name))
            d.type = "m.msg"
            self.print_event(d)
            try:
                os.remove(file.name)

            except Exception:
                pass

        if d.data["filename"].split(".")[-1] in ["png", "jpg", "jpeg", "ico"] and TermImage is not None and not d.in_history:
            self.hook_event("onimagerecv", print_image)
            self.sock.sendjson({"type": "d.file", "data": {"id": d.data["id"], "callback": "onimagerecv"}})

        return (
            d.data["author"]["username"],
            f"{truncate(d.data['filename'], 16)} ({scale_bytes(d.data['size'])})\nDownload with [yellow]/files down {d.data['id']}[/]"
        )

    def send_loop(self) -> None:
        history = {"entries": [], "index": -1, "store": None}
        while True:
            render = f"{color(self.themes.data['prompt'])}{self.shared['input']}"
            if len(render) == len(self.shared["spacer"]):
                self.shared["input"] = self.shared["input"][:-1]

            if self.shared["input"].startswith("/"):
                hint_guess = None
                guesses = sorted([p for p in self.pluginmgr.plugins if p.startswith(self.shared["input"][1:].split(" ")[0])], key = len)
                if guesses:
                    if " " not in self.shared["input"]:
                        render += color(f"[lblack]{guesses[0][len(self.shared['input']) - 1:]}")

                    elif self.shared["input"].count(" ") == 1:
                        last = self.shared["input"].split(" ")[1]
                        hint_guess = sorted([h for h in self.pluginmgr.plugins[guesses[0]]["hints"] if h.startswith(last)], key = len)
                        if hint_guess:
                            render += color(f"[lblack]{hint_guess[0][len(last):]}")

                if self.shared["input"].count(" ") > 1:
                    guesses = None

            print(f"\r{self.shared['spacer']}\r{render}", end = "")

            # Keypress handler
            kp = readchar()
            if kp in ["\t", 9] and self.shared["input"].startswith("/"):  # 9 = tab on windows
                if not guesses:
                    continue

                elif hint_guess is not None:
                    if hint_guess:
                        self.shared["input"] = " ".join(self.shared["input"].split(" ")[:-1] + [hint_guess[0]])

                else:
                    self.shared["input"] = "/" + guesses[0]

            elif isinstance(kp, str):
                self.shared["input"] += kp
                history["index"] = -1
                history["store"] = None

            elif kp == keys.ENTER and self.shared["input"]:
                history_entry = copy(self.shared["input"])
                if self.shared["input"][0] == "/":
                    data = self.shared["input"][1:].split(" ")[0]
                    if data in self.pluginmgr.plugins.keys():
                        self.shared["input"] = self.pluginmgr.on_call(self.shared["input"])

                if self.shared["input"] is not None:
                    self.sock.sendjson({"type": "m.msg", "data": {"content": self.shared["input"]}})

                history["entries"] = [history_entry] + history["entries"]
                self.shared["input"] = ""

            elif kp == keys.UP:
                if history["store"] is None:
                    history["store"] = copy(self.shared["input"])

                try:
                    history["index"] += 1
                    self.shared["input"] = history["entries"][history["index"]]

                except IndexError:
                    history["index"] -= 1

            elif kp == keys.DOWN:
                history["index"] -= 1
                if history["index"] < 0:
                    if history["store"] is not None:
                        self.shared["input"] = copy(history["store"])

                    history["store"], history["index"] = None, -1
                    continue

                self.shared["input"] = history["entries"][history["index"]]

            elif kp == keys.BACKSPACE and self.shared["input"]:
                self.shared["input"] = self.shared["input"][:-1]

            elif kp == keys.CTRL_C:
                os._exit(0)  # We need to stop the receive process

    def loop_recv(self, conn: Socket) -> None:
        self.sock = conn
        Thread(target = self.send_loop).start()

        clear()
        self.pluginmgr = PluginManager(self)

        # Receive loop
        while True:
            for event in conn.recvjson():
                event = EventContext(event)
                self.shared["server"] = event.server
                if event.type[0] == "e":
                    self.print_event(event, ("System", "[red]" + event.data["error"]))
                    continue

                elif event.type == "m.history":
                    if config.data.get("show_history", True):
                        for item in event.data["items"]:
                            self.print_event(EventContext(item, in_history = True))

                    self.print_event(EventContext({
                        "type": "m.msg",
                        "data": {
                            "author": {"username": "System"},
                            "content": f"[lblue]Welcome to [yellow]{event.data['items'][-1]['server']['name']}[/].[/]"
                        },
                        "ts": time.time(),
                        "server": event.data["items"][-1]["server"]
                    }))
                    continue

                elif "callback" in event.data:
                    cb = event.data["callback"]
                    if cb in self.events:
                        self.events[cb](event)
                        del self.events[cb]

                    continue

                self.print_event(event)

    def hook_event(self, event: str, callback: FunctionType) -> None:
        self.events[event] = callback

    def print_line(self, text: str) -> None:
        print(color(f"\r{self.shared['spacer']}\r{text}[bgreset][reset]") + "\n\r" + color(self.themes.data["prompt"]) + self.shared["input"], end = "")

    def print_event(self, data: EventContext, body_data: Tuple[str, str] = None) -> None:
        if data.type in self.data_formatters and body_data is None:
            body_data = self.data_formatters[data.type](data)

        dt = self.time_formatters.get(config.data.get("time_format", "12h"), self.time_formatters["12h"])(data.timestamp)
        prefix = f"[{self.themes.elems['time']}]{dt}[/] [{self.themes.elems['name']}]{body_data[0]}[/] "
        for i, line in enumerate(body_data[1].split("\n")):
            body = f"{prefix if not i else ' ' * len(color(prefix, dry = True))}[{self.themes.elems['sep']}]|[/] {color(line)}"
            self.print_line(body)
