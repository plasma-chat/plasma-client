# Copyright 2022 iiPython

# Modules
import os
import inspect
import tempfile
import importlib.util
from .config import config
from typing import Any, List

# Grab plugin config
plugin_config = config.get("plugins", {})

# Plugin manager
class PluginManager(object):
    def __init__(self, eventmgr) -> None:
        self.eventmgr = eventmgr
        self.plugin_dir = os.path.join(os.path.dirname(__file__), "../plugins")

        self.load_plugins()

    def load_plugin_objs(self, path: str) -> List[object]:
        path = path.replace("\\", "/")  # Windows to unix
        pluginspec = importlib.util.spec_from_file_location(path.split("/")[-1][:-3], path)
        module = importlib.util.module_from_spec(pluginspec)
        pluginspec.loader.exec_module(module)

        # Locate plugin class
        plugins = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            try:
                plugins.append(obj(eventmgr = self.eventmgr))

            except Exception:
                pass

        if not plugins:
            raise RuntimeError("no plugin class found!")

        return plugins

    def load_plugin_path(self, path: str) -> None:
        temp_path = tempfile.NamedTemporaryFile(suffix = ".py", delete = False).name
        open(temp_path, "w+").write(open(path, "r").read())
        for plugin_class in self.load_plugin_objs(temp_path):
            self.plugins[plugin_class.meta["id"]] = {
                "name": plugin_class.meta["name"], "author": plugin_class.meta["author"],
                "class": plugin_class, "path": path, "hints": plugin_class.meta.get("hints", [])
            }

            class PrintManager(object):
                def __init__(self, eventmgr, name: str) -> None:
                    self.eventmgr = eventmgr
                    self.name = name

                def print(self, text: str) -> None:
                    self.eventmgr.print_line(f"[lcyan]{self.name}[/] [lblack]|[/] {text}")

            pm = PrintManager(self.eventmgr, plugin_class.meta["name"])
            plugin_class.print = pm.print
            plugin_class.config = plugin_config.get(f"{plugin_class.meta['author']}.{plugin_class.meta['id']}", {})

        try:
            os.remove(temp_path)

        except Exception:
            pass  # It's a temp file, what do you expect?

    def load_plugins(self) -> None:
        self.plugins = {}
        for path, _, files in os.walk(self.plugin_dir):
            for plugin in files:
                if plugin[-3:] == ".py" and plugin[0] != "_":
                    try:
                        fpath = os.path.abspath(os.path.join(path, plugin))
                        self.load_plugin_path(fpath)

                    except Exception as e:
                        print("Failed to load plugin", plugin, "with error", e)

    def parse_call(self, line: str) -> list:
        data = {"val": "", "flags": [], "line": []}
        for idx, char in enumerate(line):
            if char == " " and "qt" not in data["flags"]:
                if not data["val"]:
                    continue

                data["line"].append(data["val"])
                data["val"] = ""

            elif char == "\"":
                if "qt" in data["flags"]:
                    data["line"].append(data["val"])
                    data["val"] = ""
                    data["flags"].remove("qt")

                else:
                    data["flags"].append("qt")

            else:
                data["val"] += char

        if data["val"]:
            data["line"].append(data["val"])
            data["val"] = ""

        return data["line"]

    def on_call(self, raw: str) -> Any:
        calldata = raw[1:].split(" ")
        plugin, args = self.plugins[[p for p in self.plugins if p == calldata[0]][0]]["class"], self.parse_call(" ".join(calldata[1:]))
        return plugin.on_call(args) if hasattr(plugin, "on_call") else None

    def on_msg(self, text: str) -> str:
        new = text
        for pid, plugin in self.plugins.items():
            plugin = plugin["class"]
            if hasattr(plugin, "on_msg"):
                new = plugin.on_msg(new)

        return new
