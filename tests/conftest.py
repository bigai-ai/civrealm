import os
import subprocess
import logging
import pytest
from freeciv_gym.configs import fc_args
fc_args['username'] = 'testcontroller'


test_dir = os.path.dirname(__file__)
subprocess.call(
    f'docker cp {test_dir}/game_save/testcontroller freeciv-web:/var/lib/tomcat10/webapps/data/savegames/',
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
    logger_filename = '{0}_{2}{1}'.format(*(os.path.splitext(logger_filename) + (item.name,)))
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
