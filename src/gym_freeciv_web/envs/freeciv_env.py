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
import time
import signal
import gym
from gym import error
from gym import utils
import json

try:
    from freecivbot.civ_controller import CivController
    from gym_freeciv_web.configs import args
except ImportError as e:
    raise error.DependencyNotInstalled(
        "{}. (HINT: you can install Freeciv dependencies with 'pip install gym[freeciv].)'".format(e))

class FreecivEnv(gym.Env, utils.EzPickle):
    """ Basic Freeciv Web gym environment """
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.viewer = None
        self.status = None
        self.max_turns = None

        # Switch game ports to avoid conflicts when running multiple instances
        # to join the same multiplayer game, the port should be the same
        self.game_ports = [6000, 6004]
        self.current_port_id = 0
        client_port = self.game_ports[self.current_port_id]
        self.current_port_id = (self.current_port_id + 1) % len(self.game_ports)

        self.civ_controller = CivController(username=args['username'])
        self.turn_manager = self.civ_controller.turn_manager

    def __del__(self):
        pass
        """
        self.env.act(hfo_py.QUIT)
        self.env.step()
        os.kill(self.server_process.pid, signal.SIGINT)
        if self.viewer is not None:
            os.kill(self.viewer.pid, signal.SIGKILL)
        """

    def _start_viewer(self):
        """
        Starts the SoccerWindow visualizer. Note the viewer may also be
        used with a *.rcg logfile to replay a game. See details at
        https://github.com/LARG/HFO/blob/master/doc/manual.pdf.
        """
        pass

    def is_episode_over(self):
        return False or self.civ_controller.turn_manager._turn > self.max_turns

    def _take_snapshot(self, ob, base_dir):
        f = open(base_dir + "example_observation_turn15_state.json", "w")
        json.dump(ob[0], f, skipkeys=True, default=lambda x: x.tolist(), sort_keys=True)
        f.close()
        f = open(base_dir + "example_observation_turn15_actions.json", "w")
        json.dump(ob[1], f, skipkeys=True, default=lambda x: x.json_struct(), sort_keys=True)
        f.close()

    def step(self, action):
        ob = self.turn_manager.get_observation()
        episode_over = self.is_episode_over()
        if episode_over:
            # TODO: close game
            pass

        reward = 0
        return ob, reward, episode_over, {}

    def _get_observations(self):
        self.civ_controller.lock_control()

    def reset(self, max_turns=500, visualize=False):
        self.max_turns = max_turns
        self.civ_controller.init_network()

        obs = self._get_observations()
        info = None

        return obs, info
    
    def end_turn(self):
        self.civ_controller.send_end_turn()

    def render(self, mode='human', close=False):
        """ Viewer only supports human mode currently. """
        if close:
            if self.viewer is not None:
                os.kill(self.viewer.pid, signal.SIGKILL)
        else:
            if self.viewer is None:
                self._start_viewer()

    def seed(self, seed=None):
        pass
