# RCD
### RSL Control Daemon

---

### Installation

```sh
sudo wget https://github.com/RobloxStatusLive/rcd/blob/main/rcd.py -O /bin/rcd
```

### Commands

> rcd help
Gives a list of commands and general information about RCD.

> rcd install
Installs all components of RSL onto the current system.

> rcd uninstall
Removes all RSL components from the current system.

> rcd update
Updates all RSL components from GitHub

> rcd up [service]
Starts all RSL services via systemd; or (if specified), only the provided service.

> rcd down [service]
Stops all RSL services via systemd; or (if specified), only the provided service.
