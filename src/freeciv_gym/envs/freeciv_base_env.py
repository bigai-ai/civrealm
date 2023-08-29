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
import matplotlib.pyplot as plt

import gymnasium
from gymnasium import utils

from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.freeciv.utils.eval_tags import EVALUATION_TAGS
from freeciv_gym.configs import fc_args


class FreecivBaseEnv(gymnasium.Env, utils.EzPickle):
    """ Basic Freeciv Web gym environment """
    metadata = {'render_modes': ['human']}

    def __init__(self, client_port: int = fc_args['client_port']):
        self.civ_controller = CivController(client_port=client_port)
        self._action_space = self.civ_controller.action_space
        self._observation_space = self.civ_controller.observation_space
        self.set_up_recording()
        utils.EzPickle.__init__(self, client_port)

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
        '''
        We put _get_info() before _get_observation() because the actions of new units will be initialized in 
        _get_info() and we need to get the probabilities of some actions (e.g., attack). We will trigger the 
        corresponding get_probability (e.g., GetAttack) actions in _get_info() to query the probabilities from 
        server. Therefore, we call _get_observation() after that to receive the action probabilities from server.        
        '''
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

    def get_game_results(self):
        game_results = self.civ_controller.game_ctrl.game_results
        return dict(sorted(game_results.items()))

    def evaluate_game(self):
        game_scores = self.civ_controller.request_scorelog()
        return self.civ_controller.game_ctrl.get_game_scores(game_scores)

    def plot_game_scores(self):
        plot_game_scores_folder = 'plot_game_scores'
        if not os.path.exists(plot_game_scores_folder):
            os.mkdir(plot_game_scores_folder)

        players, tags, turns, evaluations = self.evaluate_game()
        player_colors = self.civ_controller.player_ctrl.get_player_colors()
        for ptag in EVALUATION_TAGS:
            plt.figure()
            for player_id in evaluations[ptag].keys():
                scores = evaluations[ptag][player_id]
                x_1 = players[player_id]['start_turn']
                x_axis = range(x_1 + x_1 + len(scores))
                plt.plot(x_axis, scores, color=player_colors[player_id], label='player' + '_' + str(player_id))

            plt.legend()
            pfile = os.path.join(plot_game_scores_folder, ptag + '.png')
            plt.savefig(pfile)
            plt.close()

    def render(self):
        """Render the environment based on freeciv-web.
        """
        # TODO: To be implemented. Consider using CivMonitor in CivController.
        pass

    def close(self):
        self.civ_controller.close()


# Only for testing purpose
# @ray.remote
# class FreecivDummyEnv(FreecivBaseEnv):
#     def __init__(self, port):
#         super().__init__(port)
#         self.port = port
#         # self.num = 0
    
#     def step(self, action):
#         self.num += (self.port % 6300)
#         import time
#         if self.port == 6301:
#             time.sleep(1)
#         if self.port == 6303:
#             time.sleep(2)
#         return self.num, self.num, self.num, False, self.num
    
#     def reset(self):
#         self.num = 1
#         return self.num, self.num

#     def close(self):
#         pass

#     def get_port(self):
#         return self.port