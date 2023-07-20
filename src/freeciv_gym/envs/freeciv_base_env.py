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

import os
import json

import gymnasium
from gymnasium import utils

from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args


class FreecivBaseEnv(gymnasium.Env, utils.EzPickle):
    """ Basic Freeciv Web gym environment """
    metadata = {'render_modes': ['human']}

    def __init__(self):
        self.civ_controller = CivController(username=fc_args['username'])
        self._action_space = self.civ_controller.action_space
        self._observation_space = self.civ_controller.observation_space
        self.set_up_recording()

    def set_up_recording(self):
        # For recording purposes. self.record_step_count only increases when recording is enabled.
        self._record_step_count = 0
        self.recording_dir = os.path.join(
            os.path.dirname(fc_logger.handlers[0].baseFilename),
            'recordings', fc_args['username'])
        os.makedirs(self.recording_dir, exist_ok=True)

    @property
    def action_space(self):
        self._action_space = self.civ_controller.action_space
        return self._action_space

    @property
    def observation_space(self):
        self._observation_space = self.civ_controller.observation_space
        return self._observation_space

    def _record_to_file(self, name, content, default_json_encoder=None):
        if fc_args['debug.record'] is False:
            return

        turn = self.civ_controller.get_turn()
        self._recording_base_filename = os.path.join(
            self.recording_dir, f'turn_{turn:03d}_step_{self._record_step_count:04d}')
        with open(f'{self._recording_base_filename}_{name}.json', 'w') as f:
            json.dump(content, f, skipkeys=True, sort_keys=True, default=default_json_encoder)

    def _record_observation(self, observations):
        self._record_to_file('state', observations, lambda x: x.tolist())

    def _record_action(self, available_actions, action):
        self._record_to_file('available_action', available_actions, lambda x: x.encode_to_json())
        if action:
            self._record_to_file('chosen_action', action, lambda x: x.encode_to_json())
        self._record_step_count += 1

    def _get_observation(self):
        observations = self.civ_controller.get_observation()
        self._record_observation(observations)
        return observations

    def _get_reward(self):
        return self.civ_controller.get_reward()

    def _get_terminated(self):
        return self.civ_controller.game_has_terminated()

    def _get_truncated(self):
        return self.civ_controller.game_has_truncated()

    def _get_info(self):
        return self.civ_controller.get_info()

    def step(self, action):
        self.civ_controller.perform_action(action)
        # We put _get_info() before _get_observation() because the actions of new units will be initialized in _get_info() and we need to get the probabilities of some actions (e.g., attack). We will trigger the corresponding get_probability (e.g., GetAttack) actions in _get_info() to query the probabilities from server. Therefore, we call _get_observation() after that to receive the action probabilities from server.        
        info = self._get_info()
        observation = self._get_observation()        
        reward = self._get_reward()
        terminated = self._get_terminated()
        truncated = self._get_truncated()
        
        available_actions = info['available_actions']
        self._record_action(available_actions, action)

        return observation, reward, terminated, truncated, info

    def reset(self):
        self.civ_controller.init_network()        
        info = self._get_info()
        observation = self._get_observation()        
        return observation, info

    def end_game(self):
        self.civ_controller.end_game()

    def render(self):
        """Render the environment based on freeciv-web.
        """
        # TODO: To be implemented. Consider using CivMonitor in CivController.
        pass

    def close(self):
        self.civ_controller.close()
