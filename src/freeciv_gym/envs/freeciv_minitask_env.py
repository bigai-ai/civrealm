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
import random
from gymnasium import utils
from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger, set_logging_file
from freeciv_gym.configs import fc_args
from enum import Enum, unique

class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

@unique
class MinitaskType(ExtendedEnum):
    MT_DEVELOPMENT_BUILD_CITY = "development_build_city"
    MT_DEVELOPMENT_CITYTILE_WONDER = "development_citytile_wonder"
    MT_BATTLE_ANCIENT = "battle_ancient_era"
    MT_BATTLE_INDUSTRY = "battle_industry_era"
    MT_BATTLE_INFO = "battle_info_era"
    MT_BATTLE_MEDIEVAL = "battle_medieval"
    MT_BATTLE_MODERN = "battle_modern_era"
    MT_BATTLE_NAVAL_MODERN = "battle_naval_modern"
    MT_BATTLE_NAVAL = "battle_naval"
    MT_BATTLE_ATTACK_CITY = "battle_attack_city"
    MT_BATTLE_DEFEND_CITY = "battle_defend_city"
    MT_DIPLOMACY_TRADE_TECH = "diplomacy_trade_tech"

@unique
class MinitaskGameStatus(ExtendedEnum):
    MGS_END_GAME = 1
    MGS_IN_GAME = 0

@unique
class MinitaskPlayerStatus(ExtendedEnum):
    MPS_SUCCESS = 1
    MPS_FAIL = 0
    MPS_UNKNOWN = -1

@unique
class MinitaskDifficulty(ExtendedEnum):
    MD_EASY = 'easy'
    MD_NORMAL = 'normal'
    MD_HARD = 'hard'

DEFAULT_TASK = "minitask"
MAX_ID = 999
BATTLE_MINITASK_LIST = [_minitask for _minitask in MinitaskType.list() if _minitask.startswith("battle")]

class FreecivMinitaskEnv(FreecivBaseEnv):
    """ Freeciv gym environment for minitasks. """

    def __init__(self, username: str = DEFAULT_TASK, client_port: int = fc_args['client_port']):
        super().__init__(username=username, client_port=client_port)
        fc_args['username'] = username
        set_logging_file('.', username)
        self.filename = None
        self.task_type = None
        fc_args['debug.autosave'] = False
        self._last_minitask_score = None
        self.overall_mini_score = 0

    @staticmethod
    def get_minitask(name, minitask_pattern, max_id):
        """ Get Minitask Sav File Randomly. """
        if not isinstance(minitask_pattern, dict):
            minitask_pattern = dict()

        minitask_id = minitask_pattern.get('id', random.randint(0, MAX_ID))
        minitask_level = minitask_pattern.get('level', random.choice(MinitaskDifficulty.list()))
        minitask_type = minitask_pattern.get('type', random.choice(MinitaskType.list()))

        if minitask_type not in MinitaskType.list():
            raise ValueError(f"Not supported type as {minitask_pattern}. The suppported list is {MinitaskType.list()}!")
        if minitask_id > MAX_ID or minitask_id < 0:
            raise ValueError(f"Not supported id as {minitask_id}. The suppported range is [0, {MAX_ID}]!")
        if minitask_level not in MinitaskDifficulty.list():
            raise ValueError(f"Not supported diffculty as {minitask_level}. The suppported list is {MinitaskDifficulty.list()}!")

        minitask = '{}_T1_task_{}_level_{}_id_{}'.format(name, minitask_type, minitask_level, minitask_id)
        fc_logger.debug(f"Randomly selected minitask {minitask}!")
        return minitask

    def _get_info_and_observation(self):
        info, observation = super()._get_info_and_observation()
        # Remove player action from available actions. This is to prevent the agent from making pacts (peace, alliance, etc.) with other players in battle minitasks.
        if 'player' in info['available_actions'] and self.task_type in BATTLE_MINITASK_LIST:
            del info['available_actions']['player']
        return info, observation
    
    def _set_minitask_info(self, info):
        info['minitask'] = {
            'status': self._get_game_status(),
            'success': self._get_success(),
        }
        info['minitask'].update(self._get_detail())
        return
    
    def reset(self, seed=None, options=None, minitask_pattern=None, max_id=MAX_ID):
        self.set_minitask(seed, minitask_pattern, max_id)
        observations, info = super().reset(seed, options)
        self._set_minitask_info(info)
        return observations, info

    def set_minitask(self, seed, minitask_pattern, max_id):
        """ Set Minitask. """
        random.seed(seed)
        minitask = self.get_minitask(fc_args['username'], minitask_pattern, max_id)
        self.filename = minitask
        self.task_type = re.match(r"{}_T\d+_task_([a-z]+)_.*".format(fc_args['username']), minitask)[1]
        self.civ_controller.set_parameter('debug.load_game', minitask)
        return

    def minitask_has_terminated(self):
        """ Judge whether the minitask is terminated. """
        minitask_info = self.civ_controller.get_turn_message()
        if any([msg.get("status") == MinitaskGameStatus.MGS_END_GAME.value for msg in minitask_info]):
            return True
        return False
    
    def _get_terminated(self):
        return self.civ_controller.game_has_terminated(is_mini_game=True) or self.minitask_has_terminated()

    def _get_reward(self):
        minitask_results = self.civ_controller.get_turn_message()
        current_score = 0.0
        for msg in minitask_results[::-1]:
            if 'metrics' in msg and 'mini_score' in msg['metrics'][-1]:
                if self._last_minitask_score is None:
                    self._last_minitask_score = msg['metrics'][-1]['mini_score']
                current_score = msg['metrics'][-1]['mini_score'] - self._last_minitask_score
                self._last_minitask_score = msg['metrics'][-1]['mini_score']
                self.overall_mini_score = msg['metrics'][-1]['mini_score']
                return current_score
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
                for field in ['mini_goal', 'max_turn', 'mini_score']:
                    if field in msg['metrics'][-1]:
                        detail[field] = msg['metrics'][-1][field]
                return detail
        return detail

    def step(self, action):
        observation, reward, terminated, truncated, info = super().step(action)
        self._set_minitask_info(info)
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
    
    def _get_info_and_observation(self):
        info, observation = self.civ_controller.get_info_and_observation(is_mini_game=True)
        self._record_observation(observation)
        return info, observation

    def get_final_score(self):
        score = {}
        score['mini_score'] = self.overall_mini_score
        return score