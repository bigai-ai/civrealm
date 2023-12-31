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
import logging
import filelock

from civrealm.freeciv.civ_controller import CivController
import civrealm.freeciv.map.map_const as map_const
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option

from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs.logging_config import LOGGING_CONFIG


def configure_test_logger():
    # Close and remove all old handlers and add a new one with the test name
    logger_filename = LOGGING_CONFIG['handlers']['civrealmFileHandler']['filename']
    log_dir = os.path.join(os.path.dirname(logger_filename), 'tests')
    with filelock.FileLock('/tmp/civrealm_test_logger_setup.lock',mode=0o666):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    basename, ext = os.path.splitext(os.path.basename(logger_filename))
    logger_filename = os.path.join(
        log_dir, f"{basename}_{fc_args['username']}{ext}")
    file_handler_with_id = logging.FileHandler(logger_filename, 'w')
    formatter = logging.Formatter(
        LOGGING_CONFIG['formatters']['standard']['format'])
    file_handler_with_id.setFormatter(formatter)

    for handler in fc_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        fc_logger.removeHandler(handler)
    fc_logger.addHandler(file_handler_with_id)


def test_move_to(controller):
    configure_test_logger()
    fc_logger.info("test_move_to")
    _, options = get_first_observation_option(controller, 6001)
    # Class: UnitActions
    unit_opt = options['unit']
    print(unit_opt.unit_ctrl.units.keys())


def main():
    fc_args['username'] = 'demoplayer2'
    controller = CivController(fc_args['username'])
    test_move_to(controller)
    # # Delete gamesave saved in handle_begin_turn
    # controller.handle_end_turn(None)
    # controller.end_game()
    # controller.close()


if __name__ == '__main__':
    main()
