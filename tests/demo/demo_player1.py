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
import time
from civrealm.freeciv.civ_controller import CivController
import civrealm.freeciv.map.map_const as map_const
import civrealm.freeciv.units.unit_helpers as unit_helpers
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
    # print(unit_opt.unit_ctrl.units.keys())
    test_action_list = []
    origin_position = {}
    # action delay
    time.sleep(10)
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        origin_position[unit_id] = (unit_tile['x'], unit_tile['y'])
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 140:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_EAST}'])
            # goto_south is not a valid action for this unit.
            assert (f'goto_{map_const.DIR8_SOUTH}' not in valid_actions)
        elif unit_id == 166:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_NORTHWEST}'])
        elif unit_id == 185:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_SOUTH}'])
        elif unit_id == 158:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_SOUTHWEST}'])
        elif unit_id == 156:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_WEST}'])
        elif unit_id == 138:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_NORTH}'])
        elif unit_id == 137:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_NORTHEAST}'])
        elif unit_id == 139:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_SOUTHEAST}'])
        else:
            pass

    # Perform goto action for each unit
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.get_info_and_observation()
    options = controller.turn_manager.turn_actions
    unit_opt = options['unit']
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        old_position = origin_position[unit_id]
        new_position = (unit_tile['x'], unit_tile['y'])
        print(f"Unit id: {unit_id}, old_position: {old_position}, new_position: {new_position}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        origin_position[unit_id] = (unit_tile['x'], unit_tile['y'])
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 140 or unit_id == 189:
            assert (valid_actions != {})
            assert (unit_helpers.get_unit_moves_left(
                unit_opt.rule_ctrl, punit) != 0)
        else:
            assert (valid_actions == {})
            assert (unit_helpers.get_unit_moves_left(
                unit_opt.rule_ctrl, punit) == 0)

        if unit_id == 140:
            # EAST
            assert (new_position[0] == old_position[0]+1)
        elif unit_id == 166:
            # NORTHWEST
            assert (new_position[0] == old_position[0] -
                    1 and new_position[1] == old_position[1]-1)
        elif unit_id == 185:
            # SOUTH
            assert (new_position[1] == old_position[1]+1)
        elif unit_id == 158:
            # SOUTHWEST
            assert (new_position[0] == old_position[0] -
                    1 and new_position[1] == old_position[1]+1)
        elif unit_id == 156:
            # WEST
            assert (new_position[0] == old_position[0]-1)
        elif unit_id == 138:
            # NORTH
            assert (new_position[1] == old_position[1]-1)
        elif unit_id == 137:
            # NORTHEAST
            assert (new_position[0] == old_position[0] +
                    1 and new_position[1] == old_position[1]-1)
        elif unit_id == 139:
            # SOUTHEAST
            assert (new_position[0] == old_position[0] +
                    1 and new_position[1] == old_position[1]+1)
        else:
            pass


def main():
    fc_args['username'] = 'demoplayer1'
    controller = CivController(fc_args['username'])
    controller.set_parameter(
        'debug.load_game', 'demoplayer1_T27_2023-07-10-05_23')
    controller.set_parameter('minp', '2')
    test_move_to(controller)
    # Delete gamesave saved in handle_begin_turn
    controller.send_end_turn()
    controller.handle_end_turn(None)
    # controller.end_game()
    # controller.close()


if __name__ == '__main__':
    main()
