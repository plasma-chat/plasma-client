# Copyright 2022 iiPython

# Modules
from .config import config
from iipython import colormap, to_ansi

# Theme manager
class ThemeManager(object):
    def __init__(self) -> None:
        self._default = {
            "elements": {
                "time": "cyan",
                "name": "lblue",
                "sep": "lblack"
            },
            "prompt": "[yellow]>[/] "
        }
        self.elems = {}

        # Load themes
        self.themes = config.data.get("themes", {"active": "default"})
        if "schemes" not in self.themes:
            self.themes["schemes"] = {"default": self._default}

        self.themes["schemes"]["default"] = self._default

        # Load current theme
        self.active = None
        self.load_theme(self.themes.get("active", "default"))

    def load_theme(self, name: str) -> None:
        if name not in self.themes["schemes"]:
            raise RuntimeError(f"no such theme: {name}!")

        self.active = name
        self.elems = self.themes["schemes"][name].get("elements", {})
        for elem, color in self._default["elements"].items():
            if elem not in self.elems:
                self.elems[elem] = self._default["elements"][elem]

        for color, hex_ in self.themes["schemes"][name].get("colors", {}).items():
            r, g, b = tuple(int(hex_.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
            colormap[color] = to_ansi(f"38;2;{r};{g};{b}")

        self.data = self.themes["schemes"][name]
        for key in ["prompt"]:
            if key not in self.data:
                self.data[key] = self._default[key]
