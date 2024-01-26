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
import os
import subprocess
from civrealm.configs import fc_web_args, fc_args

# Change this to 'fciv-net' if you are using fciv-net
docker_image_name = 'freeciv-web'


def run_bash_command(cmd):
    subprocess.call(cmd, shell=True, executable='/bin/bash')


def check_container_exists(service_name=fc_args['service']):
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format={{.Names}}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if service_name in result.stdout.split("\n"):
            return True
        return False

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while checking for container: {e.stderr}")
        return False


def download_freeciv_web_image(image_version='latest'):
    # pull image
    pull_command = f"docker pull civrealm/freeciv-web:{image_version}"
    subprocess.run(pull_command, shell=True, check=True)

    # rename image
    tag_command = f"docker tag civrealm/freeciv-web:{image_version} freeciv/freeciv-web:{image_version}"
    subprocess.run(tag_command, shell=True, check=True)

    return


def stop_freeciv_web_service(service_name=fc_args['service']):
    if check_container_exists(service_name):
        print(f"Stop service container: {service_name}")
        stop_service_command = f"docker stop {service_name}"
        subprocess.run(stop_service_command, shell=True, check=True)
    return


def start_freeciv_web_service(image_version='latest'):
    client = docker.from_env()

    # start container
    try:
        container = client.containers.run(
            f'freeciv/{docker_image_name}:{image_version}',
            "sleep infinity",
            user="docker",
            name=fc_args['service'],
            ports=fc_web_args['port_map'],
            detach=True,
            auto_remove=True,
        )
        print(f"Container {container.id} is running.")
    except docker.errors.ContainerError as e:
        print(f"Failed to start container: {e}")

    client.close()
    return


def build_freeciv_web_service(service_name=fc_args['service'], image_version='latest'):
    stop_freeciv_web_service(service_name)
    download_freeciv_web_image(image_version)
    start_freeciv_web_service(image_version)
    return


def build_docker_img():
    client = docker.from_env()
    print("Start building freeciv-web server. Take some coffee and relax. Takes up to 20minutes")
    cli = docker.APIClient(base_url='unix://var/run/docker.sock')
    for line in cli.build(path="https://github.com/freeciv/freeciv-web.git#develop", tag="freeciv-web"):
        if not "Downloading" in line.decode('utf-8'):
            print(line)


def update_docker_image():
    """Update the docker image with the modified server code.
    To debug, use `docker exec -it freeciv-web bash` to enter the docker container.
    """

    print('Updating docker image...')
    freeciv_dir = os.path.dirname(__file__)
    modified_code_dir = os.path.join(
        freeciv_dir, 'misc', 'modified_server_code')

    # Add more ports for multiplayer mode to enable parallel training and testing.
    run_bash_command(
        f'docker exec -t {docker_image_name} sh -c "rm /docker/publite2/*longturn*"')

    # Customize the civ2civ3 ruleset to allow building settlers with population cost 1
    run_bash_command(
        f'docker cp {modified_code_dir}/units.ruleset {docker_image_name}:/home/docker/freeciv/share/freeciv/civ2civ3/units.ruleset')

    # Add more ports for multiplayer mode to enable parallel training and testing.
    # Replace the `settings.ini` and `publite2.py` file in `/docker/publite2/`
    run_bash_command(
        f'docker cp {modified_code_dir}/settings.ini {docker_image_name}:/docker/publite2/settings.ini')
    run_bash_command(
        f'docker cp {modified_code_dir}/publite2.py {docker_image_name}:/docker/publite2/publite2.py')

    # Set the command level of client to hack to allow running all commands for debugging
    # Replace the `pubscript_multiplayer.serv` and `pubscript_singleplayer.serv` file in `/docker/publite2/`
    run_bash_command(
        f'docker cp {modified_code_dir}/pubscript_singleplayer.serv {docker_image_name}:/docker/publite2/pubscript_singleplayer.serv')
    run_bash_command(
        f'docker cp {modified_code_dir}/pubscript_multiplayer.serv {docker_image_name}:/docker/publite2/pubscript_multiplayer.serv')

    # # Custom freeciv-web to save game files for debugging
    # Replace the `DeleteSaveGame.java` and `ListSaveGames` file in `freeciv-web/src/main/java/org/freeciv/servlet`:
    run_bash_command(
        f'docker cp {modified_code_dir}/DeleteSaveGame.java {docker_image_name}:/docker/freeciv-web/src/main/java/org/freeciv/servlet/DeleteSaveGame.java')
    run_bash_command(
        f'docker cp {modified_code_dir}/ListSaveGames.java {docker_image_name}:/docker/freeciv-web/src/main/java/org/freeciv/servlet/ListSaveGames.java')

    # Customize the civ2civ3 ruleset to allow building settlers with population cost 1
    run_bash_command(
        f'docker cp {modified_code_dir}/units.ruleset {docker_image_name}:/home/docker/freeciv/share/freeciv/civ2civ3/units.ruleset')

    # Rebuild the web server
    run_bash_command(
        f'docker exec -it {docker_image_name} bash -c "cd /docker/freeciv-web/; source build.sh"')

    # Commit the modified docker image
    run_bash_command(
        f'docker commit {docker_image_name} freeciv/{docker_image_name}')


def update_javascript_for_clean_screenshot():
    print('Updating docker image...')
    freeciv_dir = os.path.dirname(__file__)
    modified_code_dir = os.path.join(
        freeciv_dir, 'misc', 'modified_javascript_for_screenshot')

    # Copy modified javascript to docker image
    run_bash_command(
        f'docker cp {modified_code_dir}/javascript {docker_image_name}:/docker/freeciv-web/src/main/webapp/')

    # Rebuild the web server
    run_bash_command(
        f'docker exec -it {docker_image_name} bash -c "cd /docker/freeciv-web/; source build.sh"')
