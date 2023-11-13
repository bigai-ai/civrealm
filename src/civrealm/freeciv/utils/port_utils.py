import os
import re
import tempfile
import time
import urllib.request
from copy import copy
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

from filelock import FileLock

TEMP_DIR = tempfile.gettempdir()


class PortStatus:
    """
    A class used to represent the status of ports.

    Attributes
    ----------
    status_parser : PortStatusParser
        An instance of PortStatusParser used to parse the status of ports.
    dev_ports : list
        A list of development ports.
    lock_file : str
        The path to the lock file.
    occupied_ports_file : str
        The path to the occupied ports file

    """

    def __init__(
        self,
        host_url="http://localhost:8080",
        status_url="pubstatus",
        dev_ports=[6001],
        lock_file=os.path.join(TEMP_DIR, "civrealm.lock"),
        occupied_ports_file=os.path.join(TEMP_DIR, "civrealm_occupied_ports.txt"),
    ):
        self.status_parser = PortStatusParser(host_url, status_url)
        self.status_parser.update()
        self.dev_ports = dev_ports
        self.lock_file = lock_file
        self.occupied_ports_file = occupied_ports_file
        self._cache = {}
        with FileLock(self.lock_file):
            if not os.path.exists(self.occupied_ports_file):
                # Create the file
                with open(self.occupied_ports_file, "w", encoding="utf-8") as _:
                    pass  # Do nothing, just create an empty file

    def __iter__(self):
        return self

    def __next__(self):
        return self.get()

    @property
    def status(self) -> dict:
        """
        the current status of all ports.
        """
        self.status_parser.update()
        data = self.status_parser.data
        if self._cache != {}:
            for port, subdict in data.items():
                # if (
                #     abs(subdict["birth"] - self._cache.get(port, {"birth": 0})["birth"])
                #     < 3
                # ):
                if (
                    subdict["restart"]
                    == self._cache.get(port, {"restart": -1})["restart"]
                ):
                    subdict["user"] = max(self._cache[port]["user"], subdict["user"])
        self._cache = copy(data)

        return data

    @property
    def nondev_status(self) -> dict:
        """
        the current status of all non-development ports.
        """
        return {
            port: val
            for port, val in self.status.items()
            if (port not in self.dev_ports)
        }

    @property
    def single(self):
        """
        the current status of all singleplayer ports.
        """
        return {
            port: val
            for port, val in self.nondev_status.items()
            if (val.get("type", None) == "singleplayer")
        }

    @property
    def multi(self):
        """
        the current status of all multiplayer ports.
        """
        return {
            port: val
            for port, val in self.nondev_status.items()
            if (val.get("type", None) == "multiplayer")
        }

    @property
    def _idles(self):
        return [
            port
            for port, val in self.nondev_status.items()
            if (
                (val.get("type", None) == "multiplayer")
                and (val["user"] == 0)
                and (val["status"] == "OK")
                and (val["uptime"] > 20)
            )
        ]

    @property
    def empties(self):
        """
        the current status of all empty multiplayer ports.
        """
        with FileLock(self.lock_file):
            with open(self.occupied_ports_file, "r", encoding="utf-8") as file:
                lines = file.readlines()
                occupied_ports = [int(line.strip().split()[0]) for line in lines]
        return [port for port in self._idles if port not in occupied_ports]

    def _check_release(self, occupied_ports):
        # delete from occupied if port birth time is updated.
        status = self.status
        for id, [port, _, restart, user] in enumerate(occupied_ports):
            if port not in status:
                continue
            if user != status[port]["user"] and restart == status[port]["restart"]:
                occupied_ports[id][3] = max(user, status[port]["user"])

        occupied_ports = list(
            filter(
                # delete ports that has been restarted
                lambda x: status.get(int(x[0]), {"restart": x[2]})["restart"] == x[2],
                occupied_ports,
            )
        )
        # delete from occupied if port stay for idle more than 30s.
        occupied_ports = list(
            filter(
                lambda x: not (
                    ((status.get(int(x[0]), {"uptime": 0})["uptime"] - x[1]) > 30)
                    and x[3] == 0
                ),
                occupied_ports,
            )
        )
        return occupied_ports

    def get(self, port=None):
        """
        get the specified port or the next empty port (port=None) in a thread-safe way.
        """
        with FileLock(self.lock_file):
            with open(self.occupied_ports_file, "r", encoding="utf-8") as file:
                lines = file.readlines()
                ports_data = [list(map(int, line.strip().split())) for line in lines]

            empties = []
            while True:
                time.sleep(0.05)
                ports_data = self._check_release(ports_data)
                occupied_ports = [int(data[0]) for data in ports_data]
                empties = [p for p in sorted(self._idles) if p not in occupied_ports]
                if port is not None and port in empties:
                    result = port
                    break
                if port is None and len(empties) > 0:
                    # choose the port with minimal restart number
                    status = self.status
                    result = min(empties, key=lambda port: status[port]["restart"])
                    break

            status = self.status
            ports_data.append(
                (result, status[result]["uptime"], status[result]["restart"], 0)
            )
            occupied_ports_lines = [
                f"{int(p)} {int(uptime)} {int(restart)} {int(user)}\n"
                for [p, uptime, restart, user] in ports_data
            ]
            with open(self.occupied_ports_file, "w", encoding="utf-8") as file:
                file.writelines(occupied_ports_lines)
        return result

    def clear(self):
        """
        delete lock file and occupied ports file
        """
        with open(self.occupied_ports_file, "w", encoding="utf-8") as _:
            pass  # Do nothing, just create an empty file
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)


class PortStatusParser(HTMLParser):
    def __init__(self, host_url, status_url):
        super().__init__()
        self.host_url = host_url
        self.status_purl = status_url
        self.data = {}
        self.current_port = None
        self.current_link = ""
        self.within_tag = []
        self.after_date = False
        self.port_parser = re.compile(
            r".*Process status: (?P<status>[a-zA-Z]+).*Process Uptime: (?P<uptime>\d+).*count (?P<user>\d+).*"
        )

    def update(self):
        self.data = {}
        with urllib.request.urlopen(
            urljoin(self.host_url, self.status_purl)
        ) as response:
            html = response.read()
        self.feed(str(html))

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    assert isinstance(attr[1], str)
                    self.current_link = attr[1].split("\\'")[1]
        self.within_tag.append(tag)

    def handle_data(self, data):
        if len(self.within_tag) == 0:
            return
        if self.within_tag[-1] == "a" and data.isdigit():
            self.current_port = int(data)
        elif self.current_port and data in ["singleplayer", "multiplayer"]:
            self.data[self.current_port]["type"] = data
        if self.after_date:
            self.after_date = False
            if self.current_port:
                self.data[self.current_port]["restart"] = int(data)
        if ":" in data:
            try:
                _ = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
                self.after_date = True
            except ValueError:
                pass

    def handle_endtag(self, tag):
        if tag == "a":
            if self.current_port:
                try:
                    self.data[self.current_port] = self.parse_port_html(
                        self.current_link
                    )
                except Exception:
                    self.current_link = ""
                    self.current_port = None
        if tag == "tr":
            self.current_link = ""
            self.current_port = None
        self.within_tag.pop()

    def parse_port_html(self, port_url):
        now = time.time()
        with urllib.request.urlopen(self.host_url + port_url) as response:
            html = response.read()
        result = self.port_parser.match(str(html))
        if result is None:
            return {}
        result = result.groupdict()
        result["user"] = int(result["user"])
        result["uptime"] = int(result["uptime"])
        result["birth"] = int(now - result["uptime"])
        return result

    def error(self, message):
        print(message)


Ports = PortStatus()
