# Copyright (C) 2023  The CivRealm project
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

import numpy as np
from gymnasium.spaces import Box, Dict, Discrete, Tuple

from civrealm.freeciv.utils.base_state import PlainState, DictState
from civrealm.freeciv.utils.fc_types import RPT_CERTAIN
from civrealm.freeciv.tech.reqtree import reqtree, reqtree_multiplayer, reqtree_civ2civ3
from civrealm.freeciv.tech.req_info import ReqInfo
from civrealm.freeciv.tech import tech_helpers
from civrealm.freeciv.game.ruleset import RulesetCtrl
from civrealm.freeciv.players.player_ctrl import PlayerCtrl
from civrealm.freeciv.utils.freeciv_logging import fc_logger


class TechState(DictState):
    UPPER_TECH_STATUS = 2
    UPPER_BULB_BOUND = 10000

    def __init__(self, rule_ctrl: RulesetCtrl, player_ctrl: PlayerCtrl):
        super().__init__()
        self.rule_ctrl = rule_ctrl
        self.player_ctrl = player_ctrl
        self.reqtree_size = 0

    def _update_state(self, pplayer):
        if self._state == {}:
            self.init_tech_state()
        my_player = self.player_ctrl.my_player
        for tech_id in self._state.keys():
            ptech = self.rule_ctrl.techs[tech_id]
            cur_tech = self._state[tech_id]
            cur_tech['is_researching'] = my_player['researching'] == ptech['id']
            cur_tech['is_tech_goal'] = my_player['tech_goal'] == ptech['id']
            # cur_tech in the Player's tech invention state can be TECH_KNOWN/TECH_UNKNOWN/TECH_PREREQS_KNOWN.
            cur_tech['inv_state'] = tech_helpers.player_invention_state(
                my_player, ptech['id'])
            cur_tech['is_req_for_goal'] = self.is_tech_req_for_goal(
                ptech['id'], my_player['tech_goal'])

            # Check whether each req of cur_tech is known or not. The req could be based on the player's research progress or the government ID.
            cur_tech['reqs'] = {}
            for req in ptech['research_reqs']:
                req_active = ReqInfo.is_req_active(my_player, req, RPT_CERTAIN)
                cur_tech['reqs'][req['value']] = req_active

    def init_tech_state(self):
        if self.rule_ctrl.ruleset_control['name'] == "Civ2Civ3 ruleset":
            self.reqtree = reqtree_civ2civ3
        elif self.rule_ctrl.ruleset_control['name'] in [
                "Multiplayer ruleset", "Longturn-Web-X ruleset"
        ]:
            self.reqtree = reqtree_multiplayer
        else:
            self.reqtree = reqtree

        self.reqtree_size = len(self.reqtree)
        self._state = {}
        for tech_id in self.rule_ctrl.techs:
            ptech = self.rule_ctrl.techs[tech_id]
            str_id = str(tech_id)
            if str_id not in self.reqtree or self.reqtree[str_id] is None:
                continue

            self._state[tech_id] = cur_tech = {'name': ptech['name']}
            # Get the units which are supported by cur_tech
            cur_tech['sup_units'] = self.rule_ctrl.get_units_from_tech(tech_id)
            # Get the improvement buildings which are supported by cur_tech
            cur_tech[
                'sup_improvements'] = self.rule_ctrl.get_improvements_from_tech(
                    tech_id)

    def is_tech_req_for_goal(self, check_tech_id, goal_tech_id):
        """
         Determines if the technology 'check_tech_id' is a requirement
         for reaching the technology 'goal_tech_id'.
        """
        if check_tech_id == goal_tech_id:
            return True
        if goal_tech_id == 0 or check_tech_id == 0:
            return False

        if goal_tech_id not in self.rule_ctrl.techs:
            return False

        goal_tech = self.rule_ctrl.techs[goal_tech_id]

        for rid in goal_tech['req']:
            if rid == check_tech_id:
                return True
            elif self.is_tech_req_for_goal(check_tech_id, rid):
                return True
        return False

    def is_tech_req_for_tech(self, check_tech_id, next_tech_id):
        """
         Determines if the technology 'check_tech_id' is a direct requirement
         for reaching the technology 'next_tech_id'.
        """
        if check_tech_id == next_tech_id:
            return False
        if next_tech_id == 0 or check_tech_id == 0:
            return False

        next_tech = self.rule_ctrl.techs[next_tech_id]
        if next_tech is None:
            return False

        for rid in next_tech['req']:
            if check_tech_id == rid:
                return True
        return False

    def get_observation_space(self) -> Dict:
        """
        Get observation space.

        Returns
        -------
        gymnasium.space.Dict(
            "tech_status": Box,
            "current_tech": Box
        )
        "tech_status": Box of shape (reqtree_size,)
                       list status of all techs, with values of each entry:
                       -1: obtained,
                        0: under research,
                        1: can be researched,
                        2: need other prerequest tech(s),
        "current_tech": Box(tech_id: Int, current_bulbs_on_it: Int)
        """
        return Dict({
            "tech_status":
            Box(np.ones(self.reqtree_size) * (-1),
                np.ones(self.reqtree_size) * self.UPPER_TECH_STATUS,
                dtype=int),
            "current_tech":
            Tuple(Discrete(self.reqtree_size), Discrete(self.UPPER_BULB_BOUND),
                  Box(0, self.UPPER_BULB_BOUND, dtype=float))
        })

    # Action space should be a list of available techs though.
    # Still working on obtaining correct status now.
    def get_action_space(self) -> Box:
        """
        Get action space.

        Returns
        -------
        gymnasium.space.Box of shape (reqtree_size,)
        list status (indicating availability) of each entry:
            -1: obtained,
             0: under research,
             1: can be researched,
             2: need other prerequest tech(s),
        """
        return Box(np.ones(self.reqtree_size) * (-1),
                   np.ones(self.reqtree_size) * self.UPPER_TECH_STATUS,
                   dtype=int)
