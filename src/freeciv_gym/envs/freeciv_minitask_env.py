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

import re
import subprocess
import random
from gymnasium import utils
from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger, set_logging_file
from freeciv_gym.configs import fc_args

DEFAULT_TASK = "minitask"


def get_files(cmd):
    pi = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    sav_files = pi.stdout.read().decode("utf8").strip().replace("\r", '').split("\n")
    sav_files = [sav.strip().split(".sav")[0] for sav in sav_files if sav.endswith("sav")]
    return sav_files


class FreecivMinitaskEnv(FreecivBaseEnv):
    """ Freeciv gym environment for minitasks. """

    def __init__(self, username: str = DEFAULT_TASK, client_port: int = fc_args['client_port']):
        super().__init__(username=username, client_port=client_port)
        fc_args['username'] = username
        set_logging_file('.', username)
        self.filename = None
        fc_args['debug.autosave'] = False

    @staticmethod
    def get_minitask(name, 
                     docker_image='freeciv-web', 
                     docker_sav_path='/var/lib/tomcat10/webapps/data/savegames/',
                     minitask_pattern=None):
        """ Get Minitask Sav File Randomly. """
        minitasks = get_files(f"docker exec -it {docker_image} ls {docker_sav_path}{name}")
        if minitask_pattern is not None:
            minitasks = [task for task in minitasks if re.match('.*'+minitask_pattern+'.*', task)]
        minitask = random.choice(minitasks)
        fc_logger.debug(f"Discovered {len(minitasks)} minitasks for {name}, randomly selected {minitask}!")
        return minitask
    
    def _get_info_and_observation(self):
        info, observation = super()._get_info_and_observation()
        # Remove player action from available actions. This is to prevent the agent from making pacts (peace, alliance, etc.) with other players in battle minitasks.
        if 'player' in info['available_actions']:
            del info['available_actions']['player']
        return info, observation
    
    def reset(self, seed=None, options=None, minitask_pattern=None):
        self.set_minitask(seed, minitask_pattern)
        return super().reset(seed, options)

    def set_minitask(self, seed, minitask_pattern):
        """ Set Minitask. """
        random.seed(seed)
        minitask = self.get_minitask(fc_args['username'], minitask_pattern=minitask_pattern)
        self.filename = minitask
        self.civ_controller.set_parameter('debug.load_game', minitask)
        return

    def minitask_has_terminated(self):
        """ Judge whether the minitask is terminated. """
        minitask_info = self.civ_controller.get_turn_message()
        if any([msg.get("status") for msg in minitask_info]):
            return True
        return False

    def _get_terminated(self):
        return self.civ_controller.game_has_terminated() or self.minitask_has_terminated()

    def get_game_results(self):
        """ Merge game result and minitask. """
        game_results = self.civ_controller.game_ctrl.game_results
        minitask_results = self.civ_controller.get_turn_message()
        results = dict(sorted(game_results.items()))
        results.update({"minitask_sav": self.filename})
        results.update(dict(minitask=minitask_results))
        return results
