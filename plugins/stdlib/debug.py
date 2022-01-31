# Copyright 2022 iiPython

# Modules
import time

# Plugin class
class DebugPlugin(object):
    def __init__(self, eventmgr) -> None:
        self.eventmgr = eventmgr
        self.commands = {
            "help": self.help, "ping": self.ping
        }

        # Load meta last so we include our custom hinting
        self.meta = {
            "name": "Debug",
            "author": "iiPython",
            "id": "debug",
            "hints": self.commands.keys()
        }

    def ping(self, args: list) -> None:
        self.eventmgr.sock.sendjson({"type": "_.ping", "data": {"callback": "ping"}})
        self.eventmgr.hook_event("ping", self.on_ping_recv)

    def on_ping_recv(self, data) -> None:
        return self.print("Pong! Server -> client ping: ~" + str(round((time.time() - data.timestamp) * 1000, 2)) + "ms")

    def help(self, args: list) -> None:
        return self.print(f"usage: /debug [{'/'.join(self.commands.keys())}]")

    def on_call(self, args: list) -> None:
        if not args:
            return self.help([])

        cmd, args = args[0], args[1:]
        if cmd not in self.commands:
            return self.print(f"unknown command: '{cmd}'")

        self.commands[cmd](args)
