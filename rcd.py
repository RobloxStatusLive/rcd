#!/usr/bin/env python3

# Copyright 2022 iiPython

# Modules
import os
import sys
import json
import shutil
import subprocess

which = shutil.which  # Because I already used it before fully importing shutil and I'm very lazy

# Initialization
is_linux = os.name == "posix"
if not is_linux and "--no-linux" not in sys.argv:
    print("RCD and RSL components are currently linux-only.")
    print("If you wish to ignore this message, relaunch RCD with the --no-linux flag.")
    exit(1)

elif not which("systemctl"):
    print("RCD relies on systemd, which does not seem to be installed.")
    exit(1)

python_executable = which("python3.10") or sys.executable
def calculate_compat_python_version(pexec: str) -> bool:
    try:
        vi = subprocess.run([pexec, "-V"], stdout = subprocess.PIPE).stdout.decode("utf-8").split(" ")[1].split(".")
        return int(vi[0]) == 3 and int(vi[1]) >= 10

    except FileNotFoundError:
        return False

while not calculate_compat_python_version(python_executable):
    print("RSL Nebula requires Python 3.10+, however it was not detected.")
    python_executable = input("Enter Python 3.10+ binary path: ")

pip_check = bool(subprocess.run([python_executable, "-m", "pip", "-V"], stdout = subprocess.PIPE, stderr = subprocess.PIPE).stdout)
if not pip_check:
    print("Python 3.10+ was detected, however pip is not available.")
    print("Please install pip for the correct Python version and try again.")
    exit(1)

pm = which("apt") or which("dnf")
if pm is None:
    print("No suitable package manager was found.")
    exit(1)

elif not which("node"):
    print(f"NodeJS is not installed, would you like to install it ({'rpm' if 'dnf' in pm else 'apt'})?")
    if (input("(y/N) > ") or "n").lower() != "y":
        print("\nWarehouse requires NodeJS to be installed.")
        exit(1)

    elif "dnf" in pm:  # Fedora way of installing NodeJS
        os.system("sudo dnf install -y curl")
        os.system("curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -")
        os.system("sudo dnf install -y nodejs")

    else:  # Debian way of installing NodeJS
        os.system("sudo apt update && sudo apt install -y curl")
        os.system("curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -")
        os.system("sudo apt install -y nodejs")

# Command handler
class CommandHandler(object):
    def __init__(self) -> None:
        self.command_map = {
            "help": self.show_help,
            "install": self.install_rsl,
            "uninstall": self.uninstall_rsl,
            "update": self.update,
            "up": self.start,
            "down": self.stop
        }

        # Parse arguments
        self.argv = sys.argv[1:]
        if not self.argv:
            exit(self.command_map["help"]([]))

        try:
            exit(self.command_map.get(self.argv[0], lambda x: 1)(self.argv[1:]))

        except KeyboardInterrupt:
            exit(1)

    def show_help(self, args: list) -> int:
        print("\n".join([_.split("~")[1].replace(" ", "", 1) for _ in f"""
        ~ RCD
        ~ The Roblox Status Live Control Daemon
        ~
        ~ Usage:
        ~   rcd [{'/'.join(self.command_map.keys())}] [...]
        ~
        ~ Available commands:
        ~   rcd help                Shows this message and exits
        ~   rcd install             Installs all RSL components
        ~   rcd uninstall           Removes all RSL components
        ~   rcd update              Updates all RSL components
        ~   rcd up [service]        Launches all RSL services; or if provided, the one specified
        ~   rcd down [service]      Stops all RSL services; or if provided, the one specified
        """.split("\n") if _.strip()]))
        return 0

    def install_rsl(self, args: list) -> int:
        try:
            destination = input("Install location (def. /home/rsl): ")
            if not os.path.isdir(destination):
                os.makedirs(destination)

            os.chdir(destination)

        except Exception as e:
            print(f"Failed to create destination directory: {e}")
            return 1

        # --  Begin installation (Warehouse)  -- #
        self.run_with_perms("git clone https://github.com/RobloxStatusLive/warehouse && cd warehouse")
        self.run_with_perms("npm i")

        # Configuration
        shutil.copyfile("config/config.ex.json", "config/config.json")
        with open("config/config.json", "r") as fh:
            wh_config = json.loads(fh.read())

        wh_config["warehouse.webServerPort"] = int(input("Warehouse Server Port: "))
        wh_config["warehouse.disableLogging"] = (input("Enable Warehouse Logging for systemd [y/N]? ") or "n").lower() == "n"
        with open("config/config.json", "w") as fh:
            fh.write(json.dumps(wh_config, indent = 4))

        # --  Begin installation (Nebula)  -- #
        os.chdir("../nebula")
        self.run_with_perms(f"{python_executable} -m pip install -r reqs.txt")

        # Configuration
        shutil.copyfile("config.ex.json", "config.json")
        with open("config.json", "r") as fh:
            neb_config = json.loads(fh.read())

        neb_config["nebula.upsteam"] = f"localhost:{wh_config['warehouse.webServerPort']}"
        neb_config["nebula.protocol"] = "http"
        neb_config["nebula.enable_memcache"] = (input("Enable Nebula Memcache (RECOMMENDED) [Y/n]? ") or "y").lower() == "y"
        with open("config.json", "w") as fh:
            fh.write(json.dumps(neb_config, indent = 4))

        return 0

    def uninstall_rsl(self, args: list) -> int:
        return 0

    def update(self, args: list) -> int:
        return 0

    def start(self, args: list) -> int:
        return 0

    def stop(self, args: list) -> int:
        return 0

    def run_with_perms(self, command: str) -> None:
        if not hasattr(self, "_sudocheck"):
            try:
                os.system("touch _ && rm _")
                self._sudocheck = False

            except Exception:
                self._sudocheck = True

        os.system(f"{'sudo ' if self._sudocheck else ''}{command}")

CommandHandler()
