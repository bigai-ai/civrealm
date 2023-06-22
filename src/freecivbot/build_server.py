# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Build freeciv-web from latest repo """
import docker
import os


def build_docker_img():
    client = docker.from_env()
    print("Start building freeciv-web server. Take some coffee and relax. Takes up to 20minutes")
    cli = docker.APIClient(base_url='unix://var/run/docker.sock')
    for line in cli.build(path="https://github.com/freeciv/freeciv-web.git#develop", tag="freeciv-web"):
        if not "Downloading" in line.decode('utf-8'):
            print(line)
