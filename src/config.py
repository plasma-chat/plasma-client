# Copyright 2022 iiPython

# Modules
import json
import socket
from typing import Any
from iipython import color, clear

# Configuration class
class Configuration(object):
    def __init__(self) -> None:
        self.data, self.prompted = {}, False
        try:
            with open("config.json", "r") as f:
                self.data = json.loads(f.read())

        except Exception:
            pass

    def get(self, key: str, prompt: str = None) -> Any:
        if key not in self.data:
            if prompt is not None:
                clear()
                self.prompted = True
                self.data[key] = input(color(prompt))

        return self.data.get(key)

    def save(self) -> None:
        with open("config.json", "w+") as f:
            f.write(json.dumps(self.data, indent = 4))

    def parse_address(self, addr: str) -> tuple:
        if addr == ":":
            host, port = "localhost", 42080

        elif addr.count(":") > 1:
            raise ValueError("address is invalid!")

        elif ":" not in addr:
            host, port = addr, 42080

        else:
            host, port = addr.split(":")
            if not (host.strip() and port.strip()):
                raise ValueError("address is invalid!")

        # Convert port
        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError("port is invalid!")

        except ValueError:
            raise ValueError("port is invalid!")

        # Convert domain names
        return socket.getaddrinfo(host, port)[0][4]

# Initialization
config = Configuration()
