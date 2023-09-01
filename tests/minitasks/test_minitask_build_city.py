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

import time
import random
import subprocess
from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option
import freeciv_gym.freeciv.utils.fc_types as fc_types
from freeciv_gym.configs.logging_config import LOGGING_CONFIG
from freeciv_gym.freeciv.build_server import run_bash_command


def test_build_city(controller):
    # configure_test_logger()
    fc_logger.info("test_build_city")
    steps = 0
    _, options = get_first_observation_option(controller, 6001)
    unit_opt = options['unit']
    while steps < 3:
        print(" ----------- STEPS ------------ ", steps)
        start = time.time()
        # Class: UnitActions

        # for unit_id in unit_opt.unit_data.keys():
        #     print("UNIT_ID: ", unit_id)
        print("REWARD: ", controller.get_reward())
        # Get unit new state and check
        options = controller.turn_manager.turn_actions
        print("turn_manager.turn_actions wasted time: ", time.time() - start)
        info, observation = controller.get_info_and_observation()
        print("info: ", info)
        print("observation: ", observation)
        # unit_opt = options['unit']
        steps += 1
        print("get_info_and_observation wasted time: ", time.time() - start)
        controller.send_end_turn()
        print("send_end_turn wasted time: ", time.time() - start)
        controller.handle_end_turn(None)
        print("handle_end_turn wasted time: ", time.time() - start)


def run_command(cmd):
    pi = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return [sav.strip().split(".sav")[0] for sav in pi.stdout.read().decode("utf8").strip().split("\n")]


def get_minitask(name, docker_image='freeciv-web', docker_sav_path='/var/lib/tomcat10/webapps/data/savegames/'):
    """ Get Minitask Sav File. """
    minitasks = run_command(f"docker exec -it {docker_image} ls {docker_sav_path}{name}")
    task_size = len(minitasks)
    minitask = random.choice(minitasks)
    print(f"GETTING {task_size} MINITASKS FOR {name},  {minitask} IS CHOSEN!")
    return minitask


def main(username):
    fc_args['username'] = "myagent"  # username
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'myagent_T1_task_build_city')  # get_minitask(fc_args['username'])
    test_build_city(controller)
    # controller.send_end_turn()
    # controller.handle_end_turn(None)


if __name__ == '__main__':
    main('minitaskbuildcity')
