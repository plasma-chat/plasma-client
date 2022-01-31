# Copyright 2022 iiPython

# Plugin class
class PluginManager(object):
    def __init__(self, eventmgr) -> None:
        self.eventmgr = eventmgr
        self.commands = {
            "help": self.help, "list": self.list_plugins, "reload": self.reload_plugin
        }

        # Load meta last so we include our custom hinting
        self.meta = {
            "name": "Plugins",
            "author": "iiPython",
            "id": "plugins",
            "hints": self.commands.keys()
        }

    def help(self, args: list) -> None:
        return self.print(f"usage: /plugins [{'/'.join(self.commands.keys())}]")

    def list_plugins(self, args: list) -> None:
        for pid, plugin in self.eventmgr.pluginmgr.plugins.items():
            self.print(f"{plugin['name']} ([yellow]by {plugin['author']}[/]{f' |[lblack] /{pid}[/]' if hasattr(plugin['class'], 'on_call') else ''})")

    def reload_plugin(self, args: list) -> None:
        if not args:
            return self.print("usage: /plugins reload <id>")

        try:
            plugin_path = self.eventmgr.pluginmgr.plugins[[p for p in self.eventmgr.pluginmgr.plugins if p == args[0]][0]]["path"]
            try:
                self.eventmgr.pluginmgr.load_plugin_path(plugin_path)
                self.print(f"plugin [yellow]{args[0]}[/] reloaded successfully")

            except Exception:
                return self.print("Failed to reload plugin.")

        except IndexError:
            return self.print("No loaded plugin has that ID.")

    def on_call(self, args: list) -> None:
        if not args:
            return self.help([])

        cmd, args = args[0], args[1:]
        if cmd not in self.commands:
            return self.print(f"unknown command: '{cmd}'")

        self.commands[cmd](args)
