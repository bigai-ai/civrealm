# Copyright (C) 2023  The CivRealm project
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
import time
import datetime
import matplotlib.pyplot as plt
from BitVector import BitVector

import gymnasium
from gymnasium import utils

from civrealm.freeciv.civ_controller import CivController
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.freeciv.utils.eval_tags import EVALUATION_TAGS
from civrealm.configs import fc_args
from civrealm.freeciv.utils.port_utils import Ports

class FreecivBaseEnv(gymnasium.Env, utils.EzPickle):
    """ Basic CivRealm environment """
    metadata = {'render_modes': ['human']}

    def __init__(
            self, username: str = fc_args['username'],
            client_port=None,
            is_minitask=False):
        self.username = username
        self.is_minitask = is_minitask
        # Record whether the env is currently running.
        self.running = False

        # Create dummy controller to retrieve action_space and observation_space.
        self.civ_controller = CivController(username=self.username,
                                            visualize=fc_args['debug.take_screenshot'],
                                            is_minitask=self.is_minitask)
        self._action_space = self.civ_controller.action_space
        self._observation_space = self.civ_controller.observation_space
        self.set_up_recording()
        utils.EzPickle.__init__(self, self.username, client_port, self.is_minitask)

    def set_up_screenshots(self):
        self._screenshot_step_count = 0
        curr_date_time = str(datetime.date.today()) + "_" + str(datetime.datetime.now().time().strftime('%H-%M-%S.%f'))
        self.screenshot_dir = os.path.join(
            os.path.dirname(fc_logger.handlers[0].baseFilename),
            'screenshots', self.username + "_" + str(self.get_port()) + "_" + curr_date_time)
        os.makedirs(self.screenshot_dir, exist_ok=True)

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

    def _take_screenshot(self):
        if fc_args['debug.take_screenshot'] is False:
            return
        turn = self.civ_controller.get_turn()
        screenshot_filename = os.path.join(
            self.screenshot_dir, f'turn_{turn:03d}_step_{self._screenshot_step_count:04d}.png')
        self.civ_controller.take_screenshot(screenshot_filename)
        self._screenshot_step_count += 1

    def _record_to_file(self, name, content, default_json_encoder=None):
        if fc_args['debug.record_action_and_observation'] is False:
            return

        turn = self.civ_controller.get_turn()
        self._recording_base_filename = os.path.join(
            self.recording_dir, f'turn_{turn:03d}_step_{self._record_step_count:04d}')
        with open(f'{self._recording_base_filename}_{name}.json', 'w') as f:
            json.dump(content, f, skipkeys=True, sort_keys=True, default=default_json_encoder)

    def _record_observation(self, observation):
        self._record_to_file('state', observation, lambda x: x.get_bitvector_in_ascii()
                             if isinstance(x, BitVector) else x.tolist())

    def _record_action(self, available_actions, action):
        self._record_to_file('available_action', available_actions, lambda x: x.encode_to_json())
        if action:
            self._record_to_file('chosen_action', action, lambda x: x.encode_to_json())
        self._record_step_count += 1

    def _get_info_and_observation(self):
        info, observation = self.civ_controller.get_info_and_observation()
        self._record_observation(observation)
        return info, observation

    def _get_reward(self):
        return self.civ_controller.get_reward()

    def _get_terminated(self):
        return self.civ_controller.game_has_terminated()

    def _get_truncated(self):
        return self.civ_controller.game_has_truncated()

    def step(self, action):
        self.civ_controller.perform_action(action)
        try:
            info, observation = self._get_info_and_observation()
            reward = self._get_reward()
            terminated = self._get_terminated()
            truncated = self._get_truncated()

            available_actions = info['available_actions']
            self._record_action(available_actions, action)
            self._take_screenshot()
        except Exception as e:
            fc_logger.error(repr(e))
            reward = 0
            info = None
            observation = None
            terminated = False
            truncated = True
        
        return observation, reward, terminated, truncated, info

    def get_port(self):
        return self.civ_controller.client_port

    def get_username(self):
        return self.civ_controller.clstate.username
    
    def get_playerid(self):
        return self.civ_controller.player_ctrl.my_player_id

    def reset(self, seed=None, options=None, client_port=None, **kwargs):
        # If call reset when the env is still running, we close it first.
        if self.running:
            print('Close running environment before reset.')
            self.close()
        if client_port is None:
            client_port = Ports.get()
        print(f'Reset with port: {client_port}')
        fc_logger.debug(f'Reset with port: {client_port}')
        # self.civ_controller = CivController(username=self.username, client_port=client_port, visualize=fc_args['debug.take_screenshot'], is_minitask=self.is_minitask)
        # self._action_space = self.civ_controller.action_space
        # self._observation_space = self.civ_controller.observation_space
        self.civ_controller.reset_civ_controller(client_port)

        self.set_up_screenshots()

        if seed is not None:
            fc_args['debug.randomly_generate_seeds'] = False
            fc_args['debug.mapseed'] = seed
            fc_args['debug.agentseed'] = seed
        
        # fc_logger.debug(f'begin_logged: {self.civ_controller.clstate.begin_logged}, turn_active: {self.civ_controller.turn_manager.turn_active}')
        # Log in and get the first info and observation
        self.civ_controller.init_network()
        info, observation = self._get_info_and_observation()
        # Log in success, set running as True
        self.running = True
        return observation, info

    def get_game_results(self):
        game_results = self.civ_controller.game_ctrl.game_results
        return dict(sorted(game_results.items()))

    def evaluate_game(self):
        game_scores = self.civ_controller.request_scorelog()
        return self.civ_controller.game_ctrl.get_game_scores(game_scores)

    def plot_game_scores(self):
        players, tags, turns, evaluations = self.evaluate_game()
        if evaluations is None:
            return

        plot_game_scores_folder = (f"plot_game_scores/{time.strftime('%Y-%m-%d-%H-%M-%S')}-"
                                   f"{self.civ_controller.client_port}")
        if not os.path.exists(plot_game_scores_folder):
            os.makedirs(plot_game_scores_folder)

        player_colors = self.civ_controller.player_ctrl.get_player_colors()
        for ptag in EVALUATION_TAGS:
            if ptag not in evaluations:
                continue

            plt.figure()
            for player_id in evaluations[ptag].keys():
                scores = evaluations[ptag][player_id]
                x_1 = players[player_id]['start_turn']
                x_axis = range(x_1, x_1 + len(scores))
                plt.plot(x_axis, scores, color=player_colors[player_id], label='player' + '_' + str(player_id))

            plt.legend()
            pfile = os.path.join(plot_game_scores_folder, ptag + '.png')
            plt.savefig(pfile)
            plt.close()

    def get_final_score(self):
        _, _, _, evaluations = self.evaluate_game()
        score = {}
        if evaluations != None:
            for tag in EVALUATION_TAGS:
                score[tag] = evaluations[tag][self.civ_controller.player_ctrl.my_player_id][-1]
        return score

    def render(self):
        """Render the environment based on freeciv-web.
        """
        pass

    def close(self):
        # fc_logger.info(f'Env port: {self.get_port()} closes ....')
        self.civ_controller.close()
        self.running = False


# TODO: maybe clean up this dummy env
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
