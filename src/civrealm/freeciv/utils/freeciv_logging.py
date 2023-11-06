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
import filelock
import tempfile

import logging
import logging.config

from civrealm.configs.logging_config import LOGGING_CONFIG

# You can set the level to logging.DEBUG or logging.WARN if you want to change the amount of output.
log_dir = os.path.dirname(LOGGING_CONFIG['handlers']['civrealmFileHandler']['filename'])
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.config.dictConfig(LOGGING_CONFIG)
fc_logger = logging.getLogger('civrealm')


def set_logging_file(log_dir_name, log_file_suffix, remove_old_suffix=True):
    logger_filename = LOGGING_CONFIG['handlers']['civrealmFileHandler']['filename']
    log_dir = os.path.join(os.path.dirname(logger_filename), log_dir_name)
    with filelock.FileLock(os.path.join(tempfile.gettempdir(), f"civrealm_{log_dir_name}_logger_setup.lock")):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    basename, ext = os.path.splitext(os.path.basename(logger_filename))
    if remove_old_suffix:
        basename = basename.split('_')[0]
    logger_filename = os.path.normpath(os.path.join(log_dir, f'{basename}_{log_file_suffix}{ext}'))

    file_handler_with_suffix = logging.FileHandler(logger_filename, 'w')
    formatter = logging.Formatter(LOGGING_CONFIG['formatters']['standard']['format'])
    file_handler_with_suffix.setFormatter(formatter)

    for handler in fc_logger.handlers[:]:
        if handler.name == 'civrealmFileHandler':
            handler.close()
            fc_logger.removeHandler(handler)
    fc_logger.addHandler(file_handler_with_suffix)

    return fc_logger


def ray_logger_setup():
    return set_logging_file('parallel', os.getpid(), remove_old_suffix=False)


def update_logger(original_name, new_name):
    print('update logger')
    log_dir = os.path.dirname(LOGGING_CONFIG['handlers']['civrealmFileHandler']['filename'])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_name = LOGGING_CONFIG['handlers']['civrealmFileHandler']['filename']
    # Update log file name
    LOGGING_CONFIG['handlers']['civrealmFileHandler']['filename'] = log_file_name.replace(original_name, new_name)
    logging.config.dictConfig(LOGGING_CONFIG)
    global fc_logger
    fc_logger = logging.getLogger('civrealm')

