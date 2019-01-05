'''
Created on 19.12.2018

@author: christian
'''

import os, time, signal
import gym
from gym import error
from gym import utils
import json

try:
    from freecivbot.civclient import CivClient
    from freecivbot.connectivity.clinet import CivConnection
    from freecivbot.bot.base_bot import BaseBot
    
except ImportError as e:
    raise error.DependencyNotInstalled("{}. (HINT: you can install Freeciv dependencies with 'pip install gym[freeciv].)'".format(e))

import logging
logger = logging.getLogger(__name__)

class GymBot(BaseBot):
    def __init__(self, gym_env):
        BaseBot.__init__(self)
        self._env = gym_env
        self._last_action = None

    def conduct_turn(self, pplayer, info_controls, end_turn_hook):
        BaseBot.conduct_turn(self, pplayer, info_controls, end_turn_hook)
    
    def calculate_next_move(self):
        if self._turn_active:
            obs, self._env.reward, self._env.done, _ = self._env.step(self._last_action)
            action = self._env.gym_agent.act(obs, self._env.reward, self._env.done)
            if action == None:
                time.sleep(3)
                self.end_turn()
                return
            else:
                self.take_action(action)
            
    def take_action(self, action):
        action_list = action[0]
        action_list.trigger_validated_action(action[1])

        self._last_action = action

    def getState(self, update=False):
        if update:
            self._acquire_state()
        return self._turn_state, self._turn_opts

    def get_reward(self):
        print(self._turn_state["player"])
        return self._turn_state["player"]["my_score"]

class FreecivEnv(gym.Env, utils.EzPickle):
    """ Basic Freeciv Web gym environment """
    metadata = {'render.modes': ['human']}

    def __init__(self, max_turns=1000):
        self.viewer = None
        self.status = None
        self.gym_agent = None
        self.max_turns = max_turns

    def __del__(self):
        pass
        """
        self.env.act(hfo_py.QUIT)
        self.env.step()
        os.kill(self.server_process.pid, signal.SIGINT)
        if self.viewer is not None:
            os.kill(self.viewer.pid, signal.SIGKILL)
        """

    def _reset_client(self, client_port=6004, username="civbot", max_turns=1000,
                      visualize=True):
        """
        Provides a chance for subclasses to override this method and supply
        a different server configuration. By default, we initialize one
        offense agent against no defenders.
        """
        self.max_turns = max_turns
        self.my_civ_client = CivClient(self.my_bot, username, client_port=client_port,
                                       visual_monitor=visualize)
        self.civ_conn = CivConnection(self.my_civ_client, 'http://localhost')

    def _start_viewer(self):
        """
        Starts the SoccerWindow visualizer. Note the viewer may also be
        used with a *.rcg logfile to replay a game. See details at
        https://github.com/LARG/HFO/blob/master/doc/manual.pdf.
        """
        pass

    def is_episode_over(self):#
        return False or self.my_bot.turn > self.max_turns
    
    def _step(self, action):
        ob = self.my_bot.getState(update=True)
        """
        if self.my_bot.turn == 15:
            f = open("/home/christian/example_observation_turn15_state.json", "w")
            json.dump(ob[0], f, skipkeys=True, default=lambda x: x.tolist(), sort_keys=True)
            f.close()
            f = open("/home/christian/example_observation_turn15_actions.json", "w")
            json.dump(ob[1], f, skipkeys=True, default=lambda x: x.json_struct(), sort_keys=True)
            f.close()
        """
        reward = self._get_reward()
        episode_over = self.is_episode_over()
        return ob, reward, episode_over, {}

    def _get_reward(self):
        """ Reward is given for scoring a goal. """
        return self.my_bot.get_reward()
        
    def _reset(self):
        """ Repeats NO-OP action until a new episode begins. """
        self.reward = 0
        self.done = False
        self.my_bot = GymBot(self)
        self._reset_client(client_port=6004, visualize=True)

    def _render(self, mode='human', close=False):
        """ Viewer only supports human mode currently. """
        if close:
            if self.viewer is not None:
                os.kill(self.viewer.pid, signal.SIGKILL)
        else:
            if self.viewer is None:
                self._start_viewer()

    def _seed(self, seed=None):
        pass