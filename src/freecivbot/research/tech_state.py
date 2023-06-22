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

from freecivbot.utils.base_state import PlainState, ListState
from freecivbot.utils.fc_types import RPT_CERTAIN
from freecivbot.research.reqtree import reqtree, reqtree_multiplayer, reqtree_civ2civ3
from freecivbot.research.req_info import ReqCtrl
from freecivbot.research import tech_helpers

from freecivbot.utils.freeciv_logging import logger


class TechState(ListState):
    def __init__(self, rule_ctrl, tech_ctrl):
        PlainState.__init__(self)
        self.rule_ctrl = rule_ctrl
        self.tech_ctrl = tech_ctrl

    def _update_state(self, pplayer):
        if self._state == {}:
            self.init_tech_state()

        for tech_id in self._state.keys():
            ptech = self.rule_ctrl.techs[tech_id]
            cur_tech = self._state[tech_id]
            cur_tech['is_researching'] = pplayer['researching'] == ptech['id']
            cur_tech['is_tech_goal'] = pplayer['tech_goal'] == ptech['id']
            cur_tech['inv_state'] = tech_helpers.player_invention_state(pplayer, ptech['id'])
            cur_tech['is_req_for_goal'] = self.rule_ctrl.is_tech_req_for_goal(ptech['id'],
                                                                              pplayer['tech_goal'])

            cur_tech['reqs'] = {}
            for req in ptech['research_reqs']:
                req_active = ReqCtrl.is_req_active(pplayer, req, RPT_CERTAIN)
                self._state[tech_id]['reqs'][req['value']] = req_active

    def init_tech_state(self):
        if self.rule_ctrl.ruleset_control['name'] == "Civ2Civ3 ruleset":
            self.reqtree = reqtree_civ2civ3
        elif self.rule_ctrl.ruleset_control['name'] in ["Multiplayer ruleset", "Longturn-Web-X ruleset"]:
            self.reqtree = reqtree_multiplayer
        else:
            self.reqtree = reqtree

        logger.info(self.rule_ctrl.ruleset_control['name'])

        self._state = {}
        for tech_id in self.rule_ctrl.techs:
            ptech = self.rule_ctrl.techs[tech_id]
            str_id = "%i" % tech_id
            if str_id not in self.reqtree or self.reqtree[str_id] is None:
                continue

            self._state[tech_id] = cur_tech = {'name': ptech['name']}
            cur_tech['sup_units'] = self.rule_ctrl.get_units_from_tech(tech_id)
            cur_tech['sup_improvements'] = self.rule_ctrl.get_improvements_from_tech(tech_id)
