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
from enum import Enum, unique

DEFAULT_TASK = "minitask"
PATTERN_MINITASK_TYPE = r"minitask_T\d+_task_([a-z]+)_.*"

def get_files(cmd):
    pi = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    sav_files = pi.stdout.read().decode("utf8").strip().replace("\r", '').split("\n")
    sav_files = [sav.strip().split(".sav")[0] for sav in sav_files if sav.endswith("sav")]
    return sav_files

class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

@unique
class MinitaskType(ExtendedEnum):
    MT_BUILD_CITY = "buildcity"
    MT_BATTLE = "battle"
    MT_ATTACK_CITY = "attackcity"
    MT_DEFEND_CITY = "defendcity"
    MT_TRADE_TECH = "tradetech"
    MT_DEVELOPMENT = "development"

@unique
class MinitaskGameStatus(ExtendedEnum):
    MGS_END_GAME = 1
    MGS_IN_GAME = 0

@unique
class MinitaskPlayerStatus(ExtendedEnum):
    MPS_SUCCESS = 1
    MPS_FAIL = 0
    MPS_UNKNOWN = -1

class FreecivMinitaskEnv(FreecivBaseEnv):
    """ Freeciv gym environment for minitasks. """

    def __init__(self, username: str = DEFAULT_TASK, client_port: int = fc_args['client_port']):
        super().__init__(username=username, client_port=client_port)
        fc_args['username'] = username
        set_logging_file('.', username)
        self.filename = None
        self.task_type = None
        fc_args['debug.autosave'] = False
        self._last_minitask_score = 0

    @staticmethod
    def get_minitask(name, 
                     docker_image='freeciv-web', 
                     docker_sav_path='/var/lib/tomcat10/webapps/data/savegames/',
                     minitask_pattern=None):
        """ Get Minitask Sav File Randomly. """
        minitasks = get_files(f"docker exec -it {docker_image} ls {docker_sav_path}{name}")
        if minitask_pattern is not None:
            minitasks = [task for task in minitasks if re.match('.*'+minitask_pattern+'.*', task)]
            if len(minitasks) == 0:
                raise ValueError(f"Not supported pattern like {minitask_pattern}. The suppported list is {MinitaskType.list()}!")
        minitask = random.choice(minitasks)
        fc_logger.debug(f"Discovered {len(minitasks)} minitasks for {name}, randomly selected {minitask}!")
        return minitask
    
    def _get_info_and_observation(self):
        info, observation = super()._get_info_and_observation()
        # Remove player action from available actions. This is to prevent the agent from making pacts (peace, alliance, etc.) with other players in battle minitasks.
        if 'player' in info['available_actions'] and self.task_type in [MinitaskType.MT_BATTLE.value, 
                                                                        MinitaskType.MT_ATTACK_CITY.value, 
                                                                        MinitaskType.MT_DEFEND_CITY.value]:
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
        self.task_type = re.match(PATTERN_MINITASK_TYPE, minitask)[1]
        self.civ_controller.set_parameter('debug.load_game', minitask)
        return

    def minitask_has_terminated(self):
        """ Judge whether the minitask is terminated. """
        minitask_info = self.civ_controller.get_turn_message()
        if any([msg.get("status") == MinitaskGameStatus.MGS_END_GAME.value for msg in minitask_info]):
            return True
        return False
    
    def _get_terminated(self):
        return self.civ_controller.game_has_terminated() or self.minitask_has_terminated()

    def _get_reward(self):
        minitask_results = self.civ_controller.get_turn_message()
        current_score = 0.0
        for msg in minitask_results[::-1]:
            if 'metrics' in msg and 'mini_score' in msg['metrics'][-1]:
                current_score = msg['metrics'][-1]['mini_score'] - self._last_minitask_score
                self._last_minitask_score = msg['metrics'][-1]['mini_score']
        return current_score

    def _get_game_status(self):
        minitask_results = self.civ_controller.get_turn_message()
        for msg in minitask_results[::-1]:
            if 'status' in msg:
                return msg['status']
        return MinitaskGameStatus.MGS_IN_GAME.value

    def _get_success(self):
        minitask_results = self.civ_controller.get_turn_message()
        for msg in minitask_results[::-1]:
            if 'metrics' in msg and 'is_minitask_success' in msg['metrics'][-1]:
                return msg['metrics'][-1]['is_minitask_success']
        return MinitaskPlayerStatus.MPS_UNKNOWN.value

    def _get_detail(self):
        minitask_results = self.civ_controller.get_turn_message()
        detail = dict()
        for msg in minitask_results[::-1]:
            if 'metrics' in msg:
                if 'mini_goal' in msg['metrics'][-1]:
                    detail['goal'] = msg['metrics'][-1]['mini_goal']
                if 'max_turn' in msg['metrics'][-1]:
                    detail['max_turn'] = msg['metrics'][-1]['max_turn']
        return detail

    def step(self, action):
        observation, reward, terminated, truncated, info = super().step(action)
        info['minitask'] = {
            'status': self._get_game_status(),
            'success': self._get_success(),
        }
        info['minitask'].update(self._get_detail())
        return observation, reward, terminated, truncated, info

    def get_game_results(self):
        """ Merge game result and minitask. """
        game_results = self.civ_controller.game_ctrl.game_results
        minitask_results = self.civ_controller.get_turn_message()
        results = dict(sorted(game_results.items()))
        results.update({"minitask_sav": self.filename})
        results.update({"minitask_type": self.task_type})
        results.update(dict(minitask=minitask_results))
        return results
