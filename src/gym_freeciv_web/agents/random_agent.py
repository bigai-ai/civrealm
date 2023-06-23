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

import random
import json
import numpy

from freecivbot.utils.freeciv_logging import logger
from gym_freeciv_web.agents.base_agent import BaseAgent


class RandomAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    def act(self, observation):
        state = observation[0]
        action_opts = observation[1]

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

        if next_action["action_id"] is None:
            return None  # Send None indicating end of turn
        else:
            return action_opts["unit"], pos_acts[next_action["action_id"]]
