'''
Created on 19.12.2018

@author: christian
'''

import random
import json
import numpy

import gym
from gym import wrappers
import gym_freeciv_web

from freecivbot.utils.freeciv_logging import logger


class RandomAgent(object):
    """The world's simplest agent!"""

    def __init__(self, action_space):
        self.action_space = action_space
        self._num_actions = None

    def act(self, observation, reward, done, save_history=False):
        self._num_actions += 1
        state = observation[0]
        action_opts = observation[1]

        if save_history:
            base_name = "../../examples/observation_turn{turn:02d}_agentAct{act:04d}".format(
                turn=state["player"]["my_turns_alive"], act=self._num_actions)

            with open(base_name + "_state.json", "w") as f:
                json.dump(state, f, skipkeys=True, default=lambda x: "not serializable", sort_keys=True)

            for key in state["map"]:
                numpy.save(base_name + "_map_%s.npy" % key, state["map"][key])

        next_action = {"unit_id": None, "action_id": None}

        for actor_id in action_opts["unit"].get_actors():
            logger.info("Trying Moving units or build city: %s" % actor_id)
            if action_opts["unit"]._can_actor_act(actor_id):
                pos_acts = action_opts["unit"].get_actions(actor_id, valid_only=True)

                next_action["unit_id"] = actor_id
                if "build" in pos_acts.keys() and random.random() > 0.5:
                    next_action["action_id"] = "build"
                    break
                move_action = random.choice([key for key in pos_acts.keys() if "goto" in key])
                logger.info("in direction %s" % move_action)
                next_action["action_id"] = move_action
                break

        if save_history:
            with open(base_name + "_actions.json", "w") as f:
                json.dump(action_opts, f, skipkeys=True, default=lambda x: x.json_struct(), sort_keys=True)

            with open(base_name + "_nextAction.json", "w") as f:
                json.dump(next_action, f, sort_keys=True)

        if next_action["action_id"] is None:
            return None  # Send None indicating end of turn
        else:
            return action_opts["unit"], pos_acts[next_action["action_id"]]

    def perform_episode(self, env):
        self._num_actions = 0
        env.env.gym_agent = self
        observation, done = env.reset()
        self.reset_after_episode()
        return

    def reset_after_episode(self):
        # Reset model parameters after episode has finished
        pass


def test_random_action(env):
    observation, info = env.reset()
    for _ in range(1000):
        action = env.action_space.sample()
        observation, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            observation, info = env.reset()
    env.close()


def test_random_agent(env):
    # TODO: to be deprecated
    agent = RandomAgent(env.action_space)
    episode_count = 1
    try:
        for episode_i in range(episode_count):
            logger.info("Starting episode %i" % episode_i)
            agent.perform_episode(env)
        # Close the env and write monitor result info to disk
    finally:
        env.close()


def main():
    # You provide the directory to write to (can be an existing
    # directory, including one with existing data -- all monitor files
    # will be namespaced). You can also dump to a tempdir if you'd
    # like: tempfile.mkdtemp().
    # TODO: specify output directory in config file
    outdir = '../../logs/random-agent-results'

    env = gym.make("freeciv-v0")
    env = wrappers.Monitor(env, directory=outdir, force=True)
    test_random_action(env)

    env = gym.make("LunarLander-v2", render_mode="human")



if __name__ == '__main__':
    main()
