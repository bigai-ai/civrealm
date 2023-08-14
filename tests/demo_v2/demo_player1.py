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

PORT = 6001
FILE = 'myagent_T50_2023-08-09-08_30_02'
SCRIPT_LIST = [
    # 旁白：路途中间有非常多的敌方建筑物。三个机器人士兵分别对当前的情况生成自己的方案。
    "TARGET_CITY_DISCOVERY", 
    # 旁白：突然出现了敌方的隐形飞机（突如其来的敌军伏兵）。这时士兵灵活的进行战略的调整。【体现灵活性与可靠性】
    "TARGET_PLANE_DISCOVERY",
    # 旁白：消灭敌军之后，发现前方有平原和森林两种地形，3个士兵提出各自方案。
    "TARGET_GOAL_DESTROY",
]
MOVE_UNITS_LIST = [102, 107, 108]
UNITS_TRACK = {
    # rightmost
    102: {
        # 机器人3：我希望摧毁敌方建筑物，因为其中可能有我们需要的资源
        "TARGET_CITY_DISCOVERY": [f'goto_{map_const.DIR8_NORTH}', f'goto_{map_const.DIR8_EAST}']*2+[f'goto_{map_const.DIR8_EAST}'],
        # 机器人3：我希望进攻敌方单位，因为我们应该消灭尽可能多的敌人
        "TARGET_PLANE_DISCOVERY": [f'goto_{map_const.DIR8_NORTHWEST}']*5+[f'goto_{map_const.DIR8_NORTH}']*3+[f'goto_{map_const.DIR8_WEST}']*3,
        # 机器人3：我希望通过平原前往目标，因为敌人已消灭，可以安全前进。
        "TARGET_GOAL_DESTROY": [f'goto_{map_const.DIR8_NORTH}']+[f'goto_{map_const.DIR8_NORTHEAST}']+[f'goto_{map_const.DIR8_NORTH}']*4+[f'goto_{map_const.DIR8_NORTHWEST}']*4+[f'goto_{map_const.DIR8_NORTH}']
    }, 
    # leftmost x, y = 24, 25
    108: {
        # 机器人2：我希望往更远的未知区域探索，因为提供更多已知信息可能会对后续任务有益
        "TARGET_CITY_DISCOVERY": [f'goto_{map_const.DIR8_NORTH}']*3+[f'goto_{map_const.DIR8_EAST}']+[f'goto_{map_const.DIR8_NORTH}'],
        # 机器人2：我希望进攻敌方单位，因为若是不消灭敌军我们无法安全继续前进抵达目标(指挥官选择【机器人 2】，因为战略不但需要根据情况灵活变化，而且2号机器人的方案符合指挥官意图。)
        "TARGET_PLANE_DISCOVERY": [f'goto_{map_const.DIR8_SOUTHWEST}']+[f'goto_{map_const.DIR8_NORTH}']+[f'goto_{map_const.DIR8_NORTHWEST}']+\
                    [f'goto_{map_const.DIR8_NORTH}']*2+[f'goto_{map_const.DIR8_EAST}']*5+[f'goto_{map_const.DIR8_NORTHEAST}'],
        # 机器人2：我希望通过平原前往目标，尽快抵达目的地；
        "TARGET_GOAL_DESTROY": [f'goto_{map_const.DIR8_NORTHEAST}']*2+[f'goto_{map_const.DIR8_NORTH}']*4+[f'goto_{map_const.DIR8_NORTHWEST}']*4+[f'goto_{map_const.DIR8_NORTH}']
    },
    # centor
    107: {
        # 机器人1：我希望直接冲入敌军，因为我们应当尽快到达目标位置
        "TARGET_CITY_DISCOVERY": [f'goto_{map_const.DIR8_NORTH}']*5,
        # 机器人1：我希望进攻敌方单位，因为若是不消灭敌军我们无法安全继续前进抵达目标(指挥官选择【机器人 1】，因为战略不但需要根据情况灵活变化，而且1号机器人的方案符合指挥官意图。)
        "TARGET_PLANE_DISCOVERY": [f'goto_{map_const.DIR8_EAST}']+[f'goto_{map_const.DIR8_NORTH}']*2+[f'goto_{map_const.DIR8_WEST}']+[f'goto_{map_const.DIR8_NORTH}']*3+[f'goto_{map_const.DIR8_WEST}'],
        # 机器人1：我希望通过森林抵达目标，隐蔽行动，即使牺牲一些时间；
        "TARGET_GOAL_DESTROY": [f'goto_{map_const.DIR8_NORTHEAST}']*2+[f'goto_{map_const.DIR8_NORTH}']*4+[f'goto_{map_const.DIR8_NORTHWEST}']*4+[f'goto_{map_const.DIR8_NORTH}']
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
    _, options = get_first_observation_option(controller, PORT)
    # Class: UnitActions
    unit_opt = options['unit']

    # sleep for 5 seconds between the observation and agent action, provide enough time to observe actions
    time.sleep(5)

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
                if unit_id not in MOVE_UNITS_LIST:
                    continue
                print(f"---------------\nUnit id: {unit_id}")

                punit = unit_opt.unit_ctrl.units[unit_id]
                unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
                step = unit_step_pointer[unit_id]

                # Avoid out of index
                if step >= len(UNITS_TRACK[unit_id][script]):
                    continue

                # Get valid actions
                try:
                    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
                except Exception as ex:
                    print("Exception : \n", ex)
                    continue

                print(f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}, step: {step}.")

                action = UNITS_TRACK[unit_id][script][step]

                print(f"Unit id: {unit_id}, expect action: {action}, valid_actions: {valid_actions}")

                # Append action
                test_action_list.append(valid_actions[action])
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
        
            time.sleep(0.5)
        time.sleep(5)

def main():
    fc_args['username'] = 'myagent'
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', FILE)#
    controller.set_parameter('minp', '2')
    test_move_to(controller)
    # Delete gamesave saved in handle_begin_turn
    controller.send_end_turn()
    controller.handle_end_turn(None)
    # controller.end_game()
    # controller.close()


if __name__ == '__main__':
    main()
