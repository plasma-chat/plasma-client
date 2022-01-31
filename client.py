# Copyright 2022 iiPython

# Modules
import os
from src.config import config
from src.events import EventManager
from iipython import keypress_prompt, clear, cprint, Socket

# Initialization
address = config.get("address", prompt = "[cyan]Enter server address: ")
username = config.get("username", prompt = "[cyan]Choose a username: ")
if config.prompted:
    clear()
    cprint("[yellow]Would you like to save these changes to config.json?[/]\n[green][Y]es[/] [red][N]o[/]")
    if keypress_prompt(["y", "n"]) == "y":
        config.save()

# Start our connection
eventmgr = EventManager()
try:
    conn = Socket()
    conn.connect(config.parse_address(address))
    conn.sendjson({
        "type": "u.identify",
        "data": {"username": username}
    })
    eventmgr.loop_recv(conn)

except Exception as err:
    message = ""
    if isinstance(err, (OSError, ConnectionError)):
        message = "[red]TCP Socket Error[/]\n[yellow]Ensure the server is online, you're connected to the internet,\nand your firewall allows Plasma.[/]",

    elif isinstance(err, KeyboardInterrupt):
        pass

    else:
        raise err

    # Print message
    clear()
    cprint(message.replace("\n", "\n\r"))  # Thread causes printing errors without carriage returns

    # Stop process
    os._exit(0)
