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

import docker
import os
import subprocess

def run_bash_command(cmd):
    subprocess.call(cmd, shell=True, executable='/bin/bash')

def build_docker_img():
    client = docker.from_env()
    print("Start building freeciv-web server. Take some coffee and relax. Takes up to 20minutes")
    cli = docker.APIClient(base_url='unix://var/run/docker.sock')
    for line in cli.build(path="https://github.com/freeciv/freeciv-web.git#develop", tag="freeciv-web"):
        if not "Downloading" in line.decode('utf-8'):
            print(line)

def update_docker_image():
    print('Updating docker image...')
    freeciv_dir = os.path.dirname(__file__)
    modified_code_dir = os.path.join(freeciv_dir, 'misc', 'modified_server_code')

    # Add more ports for multiplayer mode to enable parallel training and testing.
    # Replace the `settings.ini` and `publite2.py` file in `/docker/publite2/`
    run_bash_command(f'docker cp {modified_code_dir}/settings.ini freeciv-web:/docker/publite2/settings.ini')
    run_bash_command(f'docker cp {modified_code_dir}/publite2.py freeciv-web:/docker/publite2/publite2.py')

    # Set the command level of client to hack to allow running all commands for debugging
    # Replace the `pubscript_multiplayer.serv` and `pubscript_singleplayer.serv` file in `/docker/publite2/`
    run_bash_command(f'docker cp {modified_code_dir}/pubscript_multiplayer.serv freeciv-web:/docker/publite2/pubscript_multiplayer.serv')
    run_bash_command(f'docker cp {modified_code_dir}/pubscript_multiplayer.serv freeciv-web:/docker/publite2/pubscript_multiplayer.serv')
    
    # # Custom freeciv-web to save game files for debugging
    # Replace the `DeleteSaveGame.java` and `ListSaveGames` file in `freeciv-web/src/main/java/org/freeciv/servlet`:
    run_bash_command(f'docker cp {modified_code_dir}/DeleteSaveGame.java freeciv-web:/docker/freeciv-web/src/main/java/org/freeciv/servlet/DeleteSaveGame.java')
    run_bash_command(f'docker cp {modified_code_dir}/ListSaveGames.java freeciv-web:/docker/freeciv-web/src/main/java/org/freeciv/servlet/ListSaveGames.java')
