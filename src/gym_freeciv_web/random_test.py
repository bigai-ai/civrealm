'''
Created on 19.12.2018

@author: christian
'''

import gym_freeciv_web
import gym
from gym import wrappers, logger
import random

class RandomAgent(object):
    """The world's simplest agent!"""
    def __init__(self, action_space):
        self.action_space = action_space

    def act(self, observation, reward, done):
        state = observation[0]
        action_opts = observation[1]
        print(observation[0]["unit"])
        for actor_id in action_opts["unit"].get_actors():
            print("Trying Moving units or build city: %s" % actor_id)
            if action_opts["unit"]._can_actor_act(actor_id):
                pos_acts = action_opts["unit"].get_actions(actor_id, valid_only=True)
                if "build" in pos_acts.keys() and random.random() > 0.5:
                    return action_opts["unit"], pos_acts["build"]
                move_action = random.choice([key for key in pos_acts.keys() if "goto" in key])
                print("in direction %s" % move_action)
                return action_opts["unit"], pos_acts[move_action]
        else:
            return None
        return None
        #return self.action_space.sample()

    def perform_episode(self, env):
        env.gym_agent = self
        return env.reset()    

def main():
    # You can set the level to logger.DEBUG or logger.WARN if you
    # want to change the amount of output.
    logger.set_level(logger.INFO)

    env = gym.make("Freeciv-v0")
    

    # You provide the directory to write to (can be an existing
    # directory, including one with existing data -- all monitor files
    # will be namespaced). You can also dump to a tempdir if you'd
    # like: tempfile.mkdtemp().
    outdir = '/tmp/random-agent-results'
    env = wrappers.Monitor(env, directory=outdir, force=True)
    env.seed(0)
    
    agent = RandomAgent(env.action_space)
    env.env.gym_agent = agent

    episode_count = 100
    try:
        for i in range(episode_count):
            reward, done  = agent.perform_episode(env)
        # Close the env and write monitor result info to disk
    finally:
        env.close()

if __name__ == '__main__':
    main()
