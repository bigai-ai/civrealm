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

import subprocess
import random
from gymnasium import utils
from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args

DEFAULT_TASK = "minitaskbuildcity"

def get_files(cmd):
    pi = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    sav_files = pi.stdout.read().decode("utf8").strip().replace("\r", '').split("\n")
    sav_files = [sav.strip().split(".sav")[0] for sav in sav_files if sav.endswith("sav")]
    return sav_files

class FreecivMinitaskEnv(FreecivBaseEnv):
    """ Freeciv gym environment for minitasks. """

    def __init__(self, client_port: int = fc_args['client_port']):
        fc_args['username'] = DEFAULT_TASK
        self.civ_controller = CivController(username=DEFAULT_TASK, client_port=client_port)
        self._action_space = self.civ_controller.action_space
        self._observation_space = self.civ_controller.observation_space
        self.set_up_recording()
        utils.EzPickle.__init__(self, client_port)
        self.file = None
        self.set_minitask()

    @staticmethod
    def get_minitask(name, docker_image='freeciv-web', docker_sav_path='/var/lib/tomcat10/webapps/data/savegames/'):
        """ Get Minitask Sav File Randomly. """
        minitasks = get_files(f"docker exec -it {docker_image} ls {docker_sav_path}{name}")
        minitask = random.choice(minitasks)
        print(f"Discovered {len(minitasks)} minitasks for {name}, randomly selected {minitask}!")
        return minitask

    def set_minitask(self):
        """ Set Minitask. """
        minitask = self.get_minitask(fc_args['username'])
        self.file = minitask
        self.civ_controller.set_parameter('debug.load_game', minitask)
        return

    def minitask_has_terminated(self):
        """ Judge whether the minitask is terminated. """
        minitask_info = self.civ_controller.turn_manager.turn_message
        if len(minitask_info) > 0 and minitask_info[-1]["status"]:
            return True
        return False

    def _get_terminated(self):
        return self.civ_controller.game_has_terminated() or self.minitask_has_terminated()

    def get_game_results(self):
        """ Merge game result and minitask. """
        game_results = self.civ_controller.game_ctrl.game_results
        minitask_results = self.civ_controller.turn_manager.turn_message
        results = dict(sorted(game_results.items()))
        if len(minitask_results) > 0:
            metrics = minitask_results[-1]
            metrics.update({"file": self.file})
            results.update(dict(minitask=metrics))
        return results
