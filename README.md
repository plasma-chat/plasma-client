# Plasma Client

The default Plasma client. Follow up of [this README](https://github.com/plasma-chat/plasma).  
This guide assumes you already have a `plasma-client` folder and are in it.

### Configuration

The Plasma client comes with various configuration options.  
By default, these are prompted during runtime, unless explicitly specified in the config.

Some of the options include:
- `username` - The username you want to connect with
- `address` - An IP/domain to automatically connect to
- `time_format` - `12h`/`24h`/`utc12h`/`utc24h`, the time format used internally
- `show_history` - render history

An example config would look like so:
```json
{
    "username": "Benjamin",
    "address": ":",
    "time_format": "12h",
    "show_history": false
}
```
In this case, `:` refers to `localhost` (useful for development).  
If a `config.json` file is not present, the following will be asked:
- Server IP (required)
- Username (required)

All other config options are only present in `config.json`.

### Launching

To launch the client, simply run `client.py`.
