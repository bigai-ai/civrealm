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
import filelock

import logging
import logging.config

from freeciv_gym.configs.logging_config import LOGGING_CONFIG

# # You can set the level to logging.DEBUG or logging.WARN if you want to change the amount of output.
logging.config.dictConfig(LOGGING_CONFIG)
fc_logger = logging.getLogger('freecivGym')


def set_parallel_logging(log_dir_name, log_file_suffix):
    logger_filename = LOGGING_CONFIG['handlers']['freecivFileHandler']['filename']
    log_dir = os.path.join(os.path.dirname(logger_filename), log_dir_name)
    with filelock.FileLock(f'/tmp/freeciv-gym_{log_dir_name}_logger_setup.lock'):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    basename, ext = os.path.splitext(os.path.basename(logger_filename))
    logger_filename = os.path.join(log_dir, f'{basename}_{log_file_suffix}{ext}')
    file_handler_with_suffix = logging.FileHandler(logger_filename, 'w')
    formatter = logging.Formatter(LOGGING_CONFIG['formatters']['standard']['format'])
    file_handler_with_suffix.setFormatter(formatter)

    for handler in fc_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        fc_logger.removeHandler(handler)
    fc_logger.addHandler(file_handler_with_suffix)


def logger_setup():
    print(f'reset_logger in pid: {os.getpid()}')
    set_parallel_logging('parallel', os.getpid())
    return fc_logger


# class DummyLogger():
#     def __init__(self) -> None:
#         self.handlers = [DummyFolderName()]
#     def info(self, msg):
#         pass
#     def debug(self, msg):
#         pass
#     def warning(self, msg):
#         pass
#     def error(self, msg):
#         pass

# class DummyFolderName():
#     def __init__(self) -> None:
#         self.baseFilename = 'logs'

# fc_logger = DummyLogger()
