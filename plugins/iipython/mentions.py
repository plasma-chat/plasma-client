# Copyright 2022 iiPython

# Modules
import re

# Initialization
mention_regex = re.compile(r"@[A-z1-9_-]{1,16}")

# Plugin class
class MentionPlugin(object):
    def __init__(self, eventmgr) -> None:
        self.meta = {
            "name": "Mentions",
            "author": "iiPython",
            "id": "mentions"
        }
        self.eventmgr = eventmgr

    def highlight(self, text: str) -> str:
        for match in re.findall(mention_regex, text):
            if match[1:] in [u["username"] for u in self.eventmgr.shared["server"]["users"]]:
                tags = self.config.get("tags", ["yellow"])
                text = text.replace(match, f"{''.join(f'[{t}]' for t in tags)}{match}{'[/]' * len(tags)}")

        return text

    def on_msg(self, text: str) -> str:
        return self.highlight(text)
