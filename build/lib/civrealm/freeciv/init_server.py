# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import docker


def init_freeciv_docker():
    client = docker.from_env()
    port_map = {"8443/tcp": 8080, "80/tcp": 80, "7000/tcp": 7000,
                "7001/tcp": 7001, "7002/tcp": 7002, "6000/tcp": 6000,
                "6001/tcp": 6001, "6002/tcp": 6002}

    client.containers.run('freeciv/freeciv-web',
                          "sleep infinity",
                          ports=port_map,
                          user="docker",
                          tty=True,
                          detach=True,
                          auto_remove=True,
                          )
