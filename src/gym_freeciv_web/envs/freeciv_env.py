'''
Created on 19.12.2018

@author: christian
'''

import os, subprocess, time, signal
import gym
from time import sleep
from gym import error, spaces
from gym import utils
from gym.utils import seeding

try:
    from freecivbot.civclient import CivClient
    from freecivbot.connectivity.clinet import CivConnection
    from freecivbot.bot.base_bot import BaseBot
    from freecivbot import init_server

    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys

except ImportError as e:
    raise error.DependencyNotInstalled("{}. (HINT: you can install Freeciv dependencies with 'pip install gym[freeciv].)'".format(e))

import logging
logger = logging.getLogger(__name__)
init_server.init_freeciv_docker()

class GymBot(BaseBot):
    def __init__(self, gym_env):
        BaseBot.__init__(self)
        self._env = gym_env
        self._last_action = None
        self._driver = None

    def conduct_turn(self, pplayer, info_controls, end_turn_hook):
        BaseBot.conduct_turn(self, pplayer, info_controls, end_turn_hook)
        if self.turn == 1:
            """
            self._driver = webdriver.Firefox()
            self._driver.get("http://localhost/game/list?v=singleplayer")
            elem = self._driver.find_element_by_class_name("label-success")
            print(elem.get_attribute("href"))
            print(elem.get_attribute("title"))
            """
            """
            elem = driver.find_element_by_name("q")
            elem.clear()
            elem.send_keys("pycon")
            elem.send_keys(Keys.RETURN)
            assert "No results found." not in driver.page_source
            driver.close()
            """
            #self.getState(True)
    
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

    def _configure_environment(self):
        """
        Provides a chance for subclasses to override this method and supply
        a different server configuration. By default, we initialize one
        offense agent against no defenders.
        """
        pass

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
        self.my_civ_client = CivClient(self.my_bot, "chrisrocks", client_port=6004)
        self.civ_conn = CivConnection(self.my_civ_client, 'http://localhost')

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
