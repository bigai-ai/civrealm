# Copyright (C) 2023  The Freeciv-gym project
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
import logging
import pytest
import filelock
from freeciv_gym.configs import fc_args
fc_args['username'] = 'testcontroller'


test_dir = os.path.dirname(__file__)
subprocess.call(
    f'docker cp {test_dir}/game_save/testcontroller freeciv-web:/var/lib/tomcat10/webapps/data/savegames/',
    shell=True, executable='/bin/bash')
subprocess.call(
    f'docker cp {test_dir}/game_save/tutorial freeciv-web:/var/lib/tomcat10/webapps/data/savegames/',
    shell=True, executable='/bin/bash')


def pytest_configure(config):
    # This function will be called once by each worker
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")


def configure_test_logger(item):
    # Close and remove all old handlers and add a new one with the test name

    # NOTE: these imports are here to make sure fc_args is initialized first
    from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
    from freeciv_gym.configs.logging_config import LOGGING_CONFIG

    logger_filename = LOGGING_CONFIG['handlers']['freecivFileHandler']['filename']
    log_dir = os.path.join(os.path.dirname(logger_filename), 'tests')
    with filelock.FileLock('/tmp/freeciv-gym_test_logger_setup.lock'):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    basename, ext = os.path.splitext(os.path.basename(logger_filename))
    logger_filename = os.path.join(log_dir, f'{basename}_{item.name}{ext}')
    file_handler_with_id = logging.FileHandler(logger_filename, 'w')
    formatter = logging.Formatter(LOGGING_CONFIG['formatters']['standard']['format'])
    file_handler_with_id.setFormatter(formatter)

    for handler in fc_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        fc_logger.removeHandler(handler)
    fc_logger.addHandler(file_handler_with_id)


@pytest.hookimpl
def pytest_runtest_call(item):
    configure_test_logger(item)
