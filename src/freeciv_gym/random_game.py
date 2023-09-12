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


from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.envs.freeciv_wrapper import LLMWrapper
from freeciv_gym.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent, RuleAgent, RandomLLMAgent
from freeciv_gym.configs import fc_args
import freeciv_gym
import gymnasium


def main():
    env = gymnasium.make('freeciv/FreecivBase-v0')
    # env = gymnasium.make('freeciv/FreecivMinitask-v0')

    # agent = ControllerAgent()

    env = LLMWrapper(env)
    agent = RandomLLMAgent()

    observations, info = env.reset(minitask_pattern=None)
    done = False
    step = 0
    while not done:
        try:
            action = agent.act(observations, info)
            observations, reward, terminated, truncated, info = env.step(action)
            print(
                f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}')
            step += 1
            done = terminated or truncated
        except Exception as e:
            fc_logger.error(repr(e))
            raise e
    env.close()

    '''
    players, tags, turns, evaluations = env.evaluate_game()
    '''
    env.plot_game_scores()
    game_results = env.get_game_results()
    print('game results:', game_results)


if __name__ == '__main__':
    main()
