# Copyright 2022 iiPython

# Modules
import os

# Plugin class
class FilePlugin(object):
    def __init__(self, eventmgr) -> None:
        self.eventmgr = eventmgr
        self.commands = {
            "help": self.help, "confirm": self.confirm,
            "up": self.upload, "down": self.download,
            "pwd": self.pwd, "cwd": self.cwd
        }
        self.working_dir = os.getcwd()
        self.awaiting_confirm = None

        # Load meta last so we include our custom hinting
        self.meta = {
            "name": "Files",
            "author": "iiPython",
            "id": "files",
            "hints": self.commands.keys()
        }

    def pwd(self, args: list) -> None:
        return self.print(self.working_dir)

    def cwd(self, args: list) -> None:
        if not args:
            return self.print("usage: /files cwd <path>")

        path = args[0]
        if not os.path.isdir(path):
            return self.print("No such directory exists.")

        self.working_dir = path
        return self.print(f"Moved to [yellow]{path}[/]")

    def help(self, args: list) -> None:
        return self.print(f"usage: /files [{'/'.join(self.commands.keys())}]")

    def upload(self, args: list) -> None:
        if not args:
            return self.print("usage: /files up <path>")

        filepath = args[0].replace("\\", "/")
        if not os.path.isfile(filepath):
            return self.print("No such file exists.")

        elif os.path.getsize(filepath) > 5 * (1024 ** 2):
            return self.print("File is larger than 5mb.")

        with open(filepath, "rb") as f:
            filedata = f.read().hex()

        filename = filepath.split("/")[-1]
        self.eventmgr.sock.sendjson({"type": "m.bin", "data": {"filename": filename, "binary": filedata}})

    def download(self, args: list) -> None:
        if not args:
            return self.print("usage: /files down <id>")

        self.eventmgr.sock.sendjson({"type": "d.file", "data": {"id": args[0], "callback": "filedown"}})
        self.eventmgr.hook_event("filedown", self.on_file_recv)

    def confirm(self, args: list) -> None:
        if not self.awaiting_confirm:
            return self.print("Nothing awaiting confirmation.")

        self.awaiting_confirm[0](*self.awaiting_confirm[1:])
        self.awaiting_confirm = None

    def on_file_recv(self, data, overwrite: bool = False) -> None:
        filename = data.data["filename"]
        filepath = os.path.join(self.working_dir, filename)
        if os.path.isfile(filepath) and not overwrite:
            self.awaiting_confirm = [self.on_file_recv, data, True]
            return self.print("File already exists locally, run [yellow]/files confirm[/] to overwrite.")

        with open(filepath, "wb") as f:
            f.write(bytes.fromhex(data.data["binary"]))

        self.print(f"[yellow]{filename}[/] was downloaded successfully.")

    def on_call(self, args: list) -> None:
        if not args:
            return self.help([])

        cmd, args = args[0], args[1:]
        if cmd not in self.commands:
            return self.print(f"unknown command: '{cmd}'")

        self.commands[cmd](args)
