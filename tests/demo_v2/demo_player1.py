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

########################################
#### Initial Information
# myagent(OUR)
# Unit id: 108, position: (30, 26)
# Unit id: 107, position: (31, 26)
# Unit id: 102, position: (32, 26)
#### Next Location: Target City Discovery
# Unit id: 108, position: (30, 23)
# Unit id: 107, position: (31, 23)
# Unit id: 102, position: (32, 23)
#### Next Location: Target Plane Discovery
#### Next Location: Target Leader of Enemy Discovery
########################################
SCRIPT_LIST = ["TARGET_CITY_DISCOVERY", "TARGET_PLANE_DISCOVERY"]
STAY_UNITS_LIST = [110]
MOVE_UNITS_LIST = [102, 107, 108]
UNITS_TRACK = {
    108: {
        "TARGET_CITY_DISCOVERY": [f'goto_{map_const.DIR8_NORTH}']*5,
        "TARGET_PLANE_DISCOVERY": [f'goto_{map_const.DIR8_EAST}']*3,
    },
    107: {
        "TARGET_CITY_DISCOVERY": [f'goto_{map_const.DIR8_NORTH}']*5,
        "TARGET_PLANE_DISCOVERY": [f'goto_{map_const.DIR8_EAST}']*3,
    },
    102: {
        "TARGET_CITY_DISCOVERY": [f'goto_{map_const.DIR8_NORTH}']*5,
        "TARGET_PLANE_DISCOVERY": [f'goto_{map_const.DIR8_EAST}']*3,
    }
}

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

    # loop for scripts
    for script in SCRIPT_LIST:
        print(f"LOADING SCRIPT: {script}")
        unit_step_pointer = {i: 0 for i in MOVE_UNITS_LIST}
        while True:
            # Append action for each unit
            test_action_list = []
            for unit_id in unit_opt.unit_ctrl.units.keys():
                # Stay units
                if unit_id in STAY_UNITS_LIST:
                    continue
                
                punit = unit_opt.unit_ctrl.units[unit_id]
                unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
                print(
                    f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
                # Get valid actions
                valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
                step = unit_step_pointer[unit_id]
                # Avoid out of index
                if step >= len(UNITS_TRACK[unit_id][script]):
                    continue
                # Append action
                test_action_list.append(valid_actions[UNITS_TRACK[unit_id][script][step]])
                unit_step_pointer[unit_id] += 1
            
            # Break Loop if not valid actions
            if len(test_action_list) == 0:
                break

            # Perform goto action for each unit
            for action in test_action_list:
                action.trigger_action(controller.ws_client)

            # Get unit new state and check
            options = controller.get_info()['available_actions']
            controller.get_observation()
            unit_opt = options['unit']
        
            time.sleep(1)

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
