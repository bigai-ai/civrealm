import time
import gym

from freecivbot.civ_controller import CivController
from freecivbot.bot.base_bot import BaseBot


class TurnController(BaseBot):
    def __init__(self, gym_env):
        BaseBot.__init__(self)
        self._env = gym_env
        self._last_action = None

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


class BaseEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, username: str = 'civ_agent', max_turns: int = 500, visualize: bool = False):
        self._username = username
        self._max_turns = max_turns
        self._visualize = visualize

        self.civ_controller = None

        self.bot = TurnController(self)

    def _get_obs(self):
        pass

    def _get_info(self):
        pass

    def _get_reward(self):
        pass

    def step(self, action):
        reward = 0
        done = False

        # Check if the packets 

        observation = self._get_obs()
        info = self._get_info()

        return observation, reward, done, False, info

    def reset(self, seed: int = None):
        # super().reset(seed=seed)

        self.civ_controller = CivController(self.bot, username=self._username, visualize=self._visualize)

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def render(self, mode='human', close=False):
        pass

    def close(self):
        return super().close()
