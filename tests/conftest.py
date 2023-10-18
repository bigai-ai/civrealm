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

import os
import subprocess
import pytest
from civrealm.freeciv.build_server import docker_image_name
from civrealm.configs import fc_args
fc_args['username'] = 'testcontroller'
fc_args['ruleset'] = 'classic'
fc_args['pytest'] = True
fc_args['server_timeout'] = 5
fc_args['self_play'] = False


test_dir = os.path.dirname(__file__)
if docker_image_name == 'freeciv-web':
    tomcat_dir = 'tomcat10'
elif docker_image_name == 'fciv-net':
    tomcat_dir = 'tomcat9'
else:
    raise ValueError(f'Unknown docker image name: {docker_image_name}')

for username in next(os.walk(f'{test_dir}/game_save/'))[1]:
    subprocess.call(
        f'docker cp {test_dir}/game_save/{username} {docker_image_name}:/var/lib/{tomcat_dir}/webapps/data/savegames/',
        shell=True, executable='/bin/bash')


def pytest_configure(config):
    # This function will be called once by each worker
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")


@pytest.fixture(scope="module", autouse=True)
def restore_fc_args_username():
    # restore fc_args to 'testcontroller' after beeing overwritten by minitask
    # useful in multi-process testing
    if fc_args["username"] == "minitask":
        fc_args["username"] = "testcontroller"

def configure_test_logger(item):
    # Close and remove all old handlers and add a new one with the test name

    # NOTE: these imports are here to make sure fc_args is initialized and modified first
    from civrealm.freeciv.utils.freeciv_logging import set_logging_file
    set_logging_file('tests', item.name)


@pytest.hookimpl
def pytest_runtest_call(item):
    configure_test_logger(item)
