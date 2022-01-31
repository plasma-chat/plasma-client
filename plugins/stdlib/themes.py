# Copyright 2022 iiPython

# Plugin class
class PluginManager(object):
    def __init__(self, eventmgr) -> None:
        self.eventmgr = eventmgr
        self.commands = {
            "help": self.help, "list": self.list_themes, "use": self.use_theme
        }

        # Load meta last so we include our custom hinting
        self.meta = {
            "name": "Themes",
            "author": "iiPython",
            "id": "themes",
            "hints": self.commands.keys()
        }

    def help(self, args: list) -> None:
        return self.print(f"usage: /themes [{'/'.join(self.commands.keys())}]")

    def list_themes(self, args: list) -> None:
        self.print("[yellow][Available Themes]")
        for theme in self.eventmgr.themes.themes["schemes"]:
            self.print(f"{theme} {'[cyan](active)' if theme == self.eventmgr.themes.active else ''}")

    def use_theme(self, args: list) -> None:
        if not args:
            return self.print("usage: /themes use <theme>")

        theme = args[0]
        try:
            self.eventmgr.themes.load_theme(theme)
            if self.config.get("overwrite_config_on_change", True):
                self.eventmgr.shared["config"].data["themes"]["active"] = theme
                self.eventmgr.shared["config"].save()

            return self.print(f"Switched to [yellow]{theme}[/] theme.")

        except RuntimeError:
            return self.print("No such theme exists in [yellow]config.json[/].")

    def on_call(self, args: list) -> None:
        if not args:
            return self.help([])

        cmd, args = args[0], args[1:]
        if cmd not in self.commands:
            return self.print(f"unknown command: '{cmd}'")

        self.commands[cmd](args)
