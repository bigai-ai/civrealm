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

import time
import random
import json
import numpy

from freecivbot.utils.freeciv_logging import logger
from gym_freeciv_web.agents.base_agent import BaseAgent
from gym_freeciv_web.configs import args


class RandomAgent(BaseAgent):
    def __init__(self, gym_env):
        super().__init__()
        self._env = gym_env
        self._last_action = None
        self._num_actions = 0

    def calculate_next_move(self):
        obs, self._env.reward, self._env.done, _ = self._env.step(self._last_action)
        if self._env.done:
            pass
        action = self._env.gym_agent.act(obs, self._env.reward, self._env.done)
        if action == None:
            time.sleep(2)
            self._env.end_turn()
            return
        else:
            self.take_action(action)

    def reset(self):
        self._env.gym_agent.reset()

    def take_action(self, action):
        action_list = action[0]
        action_list.trigger_validated_action(action[1])

        self._last_action = action

    def act(self, observation, reward, done, save_history=False):
        self._num_actions += 1
        state = observation[0]
        action_opts = observation[1]

        if save_history:
            base_name = "../../examples/observation_turn{turn:02d}_agentAct{act:04d}".format(
                turn=state["player"]["my_turns_alive"], act=self._num_actions)

            with open(base_name + "_state.json", "w") as f:
                json.dump(state, f, skipkeys=True,
                          default=lambda x: "not serializable", sort_keys=True)

            for key in state["map"]:
                numpy.save(base_name + "_map_%s.npy" % key, state["map"][key])

        next_action = {"unit_id": None, "action_id": None}

        for actor_id in action_opts["unit"].get_actors():
            logger.info("Trying Moving units or build city: %s" % actor_id)
            if action_opts["unit"]._can_actor_act(actor_id):
                pos_acts = action_opts["unit"].get_actions(
                    actor_id, valid_only=True)

                next_action["unit_id"] = actor_id
                if "build" in pos_acts.keys() and random.random() > 0.5:
                    next_action["action_id"] = "build"
                    break
                move_action = random.choice(
                    [key for key in pos_acts.keys() if "goto" in key])
                logger.info("in direction %s" % move_action)
                next_action["action_id"] = move_action
                break

        if save_history:
            with open(base_name + "_actions.json", "w") as f:
                json.dump(action_opts, f, skipkeys=True,
                          default=lambda x: x.json_struct(), sort_keys=True)

            with open(base_name + "_nextAction.json", "w") as f:
                json.dump(next_action, f, sort_keys=True)

        if next_action["action_id"] is None:
            return None  # Send None indicating end of turn
        else:
            return action_opts["unit"], pos_acts[next_action["action_id"]]
