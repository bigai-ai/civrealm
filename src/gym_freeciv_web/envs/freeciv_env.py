# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
import gym
from gym import error
from gym import utils

try:
    from freecivbot.civ_controller import CivController
    from freecivbot.utils.freeciv_logging import logger
    from gym_freeciv_web.configs import args
except ImportError as e:
    raise error.DependencyNotInstalled(
        "{}. (HINT: you can install Freeciv dependencies with 'pip install gym[freeciv].)'".format(e))


class FreecivEnv(gym.Env, utils.EzPickle):
    """ Basic Freeciv Web gym environment """
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.civ_controller = CivController(username=args['username'])

        # For recording purposes. self.record_step_count only increases when recording is enabled.
        self._record_step_count = 0
        self._recording_dir = os.path.join(os.path.dirname(logger.handlers[0].baseFilename), 'recordings')
        os.makedirs(self._recording_dir, exist_ok=True)

    def record(self, observations):
        if args['record'] is False:
            return

        with open(os.path.join(self._recording_dir, f'turn_{self._record_step_count:04d}_state.json'), 'w') as f:
            json.dump(observations[0], f, skipkeys=True, default=lambda x: x.tolist(), sort_keys=True)
        with open(os.path.join(self._recording_dir, f'turn_{self._record_step_count:04d}_action.json'), 'w') as f:
            json.dump(observations[1], f, skipkeys=True, default=lambda x: x.json_struct(), sort_keys=True)
        self._record_step_count += 1

    def _get_observations(self):
        observations = self.civ_controller.get_observations()
        self.record(observations)
        return observations

    def _get_reward(self):
        return self.civ_controller.get_reward()

    def _get_terminated(self):
        return self.civ_controller.game_has_terminated()

    def _get_info(self):
        return self.civ_controller.get_info()

    def step(self, action):
        self.civ_controller.perform_action(action)

        observation = self._get_observations()
        reward = self._get_reward()
        terminated = self._get_terminated()
        info = self._get_info()

        return observation, reward, terminated, info

    def reset(self):
        self.civ_controller.init_network()
        observation = self._get_observations()
        info = self._get_info()

        return observation, info

    def render(self):
        """Render the environment based on freeciv-web.
        """
        # TODO: To be implemented. Consider using CivMonitor in CivController.
        pass

    def close(self):
        self.civ_controller.close()
