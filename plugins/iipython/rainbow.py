# Copyright 2022 iiPython

# Plugin class
class RainbowPlugin(object):
    def __init__(self, eventmgr) -> None:
        self.meta = {
            "name": "Rainbow",
            "author": "iiPython",
            "id": "rainbow"
        }
        self.eventmgr = eventmgr
        self.colors = ["red", "yellow", "green", "blue"]

    def rainbowify(self, text: str) -> str:
        new, idx = "", 0
        for c in text:
            if idx > len(self.colors) - 1:
                idx = 0

            new += f"[{self.colors[idx]}]{c}"
            idx += 1

        return new

    def on_call(self, args: list) -> None:
        return self.rainbowify(" ".join(args))
