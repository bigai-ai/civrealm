# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# # Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License
# for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import logging
import filelock
import time

from freeciv_gym.freeciv.civ_controller import CivController
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs.logging_config import LOGGING_CONFIG




def configure_test_logger():
    # Close and remove all old handlers and add a new one with the test name
    logger_filename = LOGGING_CONFIG['handlers']['freecivFileHandler']['filename']
    log_dir = os.path.join(os.path.dirname(logger_filename), 'tests')
    with filelock.FileLock('/tmp/freeciv-gym_test_logger_setup.lock'):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    basename, ext = os.path.splitext(os.path.basename(logger_filename))
    logger_filename = os.path.join(log_dir, f"{basename}_{fc_args['username']}{ext}")
    file_handler_with_id = logging.FileHandler(logger_filename, 'w')
    formatter = logging.Formatter(LOGGING_CONFIG['formatters']['standard']['format'])
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

    # sleep for 10 seconds between the observation and agent action, provide enough time to observe actions
    time.sleep(10)

    # action control
    test_action_list = []
    origin_position = {}
    stay_units_list = [110]
    for unit_id in unit_opt.unit_ctrl.units.keys():
        # stay units
        if unit_id in stay_units_list:
            continue
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
        origin_position[unit_id] = (unit_tile['x'], unit_tile['y'])
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 108:
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_NORTH}'])
        elif unit_id == 107:
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_NORTH}'])
        elif unit_id == 102:
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_NORTH}'])
    
    # Perform goto action for each unit
    for action in test_action_list:
        action.trigger_action(controller.ws_client)

    # Get unit new state
    options = controller.get_info()['available_actions']
    controller.get_observation()
    unit_opt = options['unit']
    for unit_id in unit_opt.unit_ctrl.units.keys():
        # stay units
        if unit_id in stay_units_list:
            continue

        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        old_position = origin_position[unit_id]
        new_position = (unit_tile['x'], unit_tile['y'])
        print(f"Unit id: {unit_id}, old_position: {old_position}, new_position: {new_position}, move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
        origin_position[unit_id] = (unit_tile['x'], unit_tile['y'])
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f"Unit id: {unit_id}, valid_actions: {valid_actions}")
        assert (valid_actions != {})
        assert (unit_opt.unit_ctrl.get_unit_moves_left(punit) != '0')

        if unit_id == 108:
            # EAST
            assert (new_position[1] == old_position[1]-1)
        elif unit_id == 107:
            # NORTHWEST
            assert (new_position[1] == old_position[1]-1)
        elif unit_id == 102:
            # SOUTH
            assert (new_position[1] == old_position[1]-1)


def main():
    fc_args['username'] = 'myagent'
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'myagent_T8_2023-08-07-08_11')#
    controller.set_parameter('minp', '2')
    test_move_to(controller)
    # Delete gamesave saved in handle_begin_turn
    controller.send_end_turn()
    controller.handle_end_turn(None)
    # controller.end_game()
    # controller.close()


if __name__ == '__main__':
    main()
