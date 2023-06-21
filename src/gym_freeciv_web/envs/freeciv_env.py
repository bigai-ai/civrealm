'''
Created on 19.12.2018

@author: christian
'''

import os
import time
import signal
import gym
from gym import error
from gym import utils
import json

try:
    from freecivbot.civ_controller import CivController
    from freecivbot.bot.base_bot import BaseBot

except ImportError as e:
    raise error.DependencyNotInstalled(
        "{}. (HINT: you can install Freeciv dependencies with 'pip install gym[freeciv].)'".format(e))

from gym_freeciv_web.configs import args

class GymBot(BaseBot):
    def __init__(self, gym_env, username, visualize):
        BaseBot.__init__(self)
        self._env = gym_env
        self._last_action = None

        self.civ_controller = CivController(username=username, visualize=visualize)
        self.civ_controller.set_begin_turn_callback(self.conduct_turn)
        self.civ_controller.set_move_callback(self.move)

    def init_env(self):
        # TODO: rename this function
        self.civ_controller.init_network()

    def move(self):
        self.calculate_next_move()
        if self.wants_to_end():
            self.civ_controller.close()

    def calculate_next_move(self):
        if self._turn_active:
            obs, self._env.reward, self._env.done, _ = self._env.step(self._last_action)
            if self._env.done:
                pass
            action = self._env.gym_agent.act(obs, self._env.reward, self._env.done)
            if action == None:
                time.sleep(2)
                self.end_turn()
                return
            else:
                self.take_action(action)

    def reset(self):
        self._env.gym_agent.reset()

    def take_action(self, action):
        action_list = action[0]
        action_list.trigger_validated_action(action[1])

        self._last_action = action

    def getState(self, update=False):
        if update:
            self._acquire_state()
        return self._turn_state, self._turn_opts

    def get_reward(self):
        return self._turn_state["player"]["my_score"]


class FreecivEnv(gym.Env, utils.EzPickle):
    """ Basic Freeciv Web gym environment """
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.viewer = None
        self.status = None
        self.gym_agent = None
        self.max_turns = None

        self.my_bot = None

        # Switch game ports to avoid conflicts when running multiple instances
        # to join the same multiplayer game, the port should be the same
        self.game_ports = [6000, 6004]
        self.current_port_id = 0
        client_port = self.game_ports[self.current_port_id]
        self.current_port_id = (self.current_port_id + 1) % len(self.game_ports)

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
        return False or self.my_bot.turn > self.max_turns

    def _take_snapshot(self, ob, base_dir):
        f = open(base_dir + "example_observation_turn15_state.json", "w")
        json.dump(ob[0], f, skipkeys=True, default=lambda x: x.tolist(), sort_keys=True)
        f.close()
        f = open(base_dir + "example_observation_turn15_actions.json", "w")
        json.dump(ob[1], f, skipkeys=True, default=lambda x: x.json_struct(), sort_keys=True)
        f.close()

    def step(self, action):
        ob = self.my_bot.getState(update=True)
        reward = self._get_reward()
        episode_over = self.is_episode_over()
        if episode_over:
            self.my_bot.close_game()
        return ob, reward, episode_over, {}

    def _get_reward(self):
        """ Reward is given for scoring a goal. """
        return self.my_bot.get_reward()

    def reset(self, username=args['username'], max_turns=500, visualize=False):
        self.reward = 0
        self.done = False

        self.max_turns = max_turns
        self.my_bot = GymBot(self, username, visualize=visualize)
        self.my_bot.init_env()

        return self.reward, self.done

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
