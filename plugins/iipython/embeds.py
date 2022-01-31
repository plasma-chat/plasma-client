# Copyright 2022 iiPython

# Modules
import time

# Initialization
embed_size = 45

# Plugin class
class EmbedPlugins(object):
    def __init__(self, eventmgr) -> None:
        self.meta = {
            "name": "Embeds",
            "author": "iiPython",
            "id": "embeds"
        }
        self.eventmgr = eventmgr

    def center(self, line: str) -> str:
        padding = round((embed_size - len(line)) / 2)
        return (" " * padding) + line + (" " * padding)

    def normalize(self, lines: str, tags: str) -> str:
        new, longest = [], len(max(lines, key = len))
        for line in lines:
            new.append(f"{tags}" + line + (" " * (longest - len(line))))

        return new

    def on_call(self, args: list) -> str:
        try:
            title, body = args[0], args[1]

        except IndexError:
            return self.print("usage: /embeds <title> <body>")

        # Make footer
        footer = time.strftime("%I:%M %p · %Z")

        # Construct embed
        embed_lines = [self.center(line) for line in [title] + [body[i:i + (embed_size - 10)] for i in range(0, len(body), embed_size - 10)] + ["", footer]]
        return "\n".join(self.normalize(embed_lines, args[2] if len(args) > 2 else "[bglblack]"))
