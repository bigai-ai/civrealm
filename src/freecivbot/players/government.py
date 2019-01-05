"""
    Freeciv-web - the web version of Freeciv. http://play.freeciv.org/
    Copyright (C) 2009-2015  The Freeciv-web project

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from freecivbot.connectivity.Basehandler import CivPropController
from freecivbot.utils.fc_types import packet_player_change_government, packet_report_req,\
    RPT_CERTAIN
from freecivbot.utils import base_action
from freecivbot.utils.base_action import ActionList
from freecivbot.utils.base_state import PlainState
from freecivbot.research.req_info import ReqCtrl

REPORT_WONDERS_OF_THE_WORLD = 0
REPORT_TOP_5_CITIES = 1
REPORT_DEMOGRAPHIC = 2
REPORT_ACHIEVEMENTS = 3

GOV_ANARCHY = 0
GOV_DESPOTISM = 1
GOV_MONARCHY = 2
GOV_COMMUNISM = 3
GOV_REPUBLIC = 4
GOV_DEMOCRACY = 5

GOV_TXT = {GOV_ANARCHY: "Anarchy", GOV_DESPOTISM: "Despotism",
           GOV_MONARCHY: "Monarchy", GOV_COMMUNISM: "Communism",
           GOV_REPUBLIC: "Republic", GOV_DEMOCRACY: "Democracy"}

class GovState(PlainState):
    def __init__(self, rule_ctrl):
        PlainState.__init__(self)
        self.rule_ctrl = rule_ctrl
        
    def _update_state(self, pplayer):
        self._state["name"] = self.rule_ctrl.governments[pplayer['government']]['name']
        self._state["id"] = self.rule_ctrl.governments[pplayer['government']]['id']
        self._state["helptext"] = self.rule_ctrl.governments[pplayer['government']]['helptext']

class GovActions(ActionList):
    def __init__(self, ws_client, rule_ctrl, city_ctrl):
        ActionList.__init__(self, ws_client)
        self.rule_ctrl = rule_ctrl
        self.city_ctrl = city_ctrl
    
    def _can_actor_act(self, actor_id):
        return True

    def update(self, pplayer):
        player_id = pplayer["playerno"]
        if not self.actor_exists(player_id):
            self.add_actor(player_id)
            for govt_id in self.rule_ctrl.governments:
                act = ChangeGovernment(govt_id, self.city_ctrl, self.rule_ctrl, pplayer)
                self.add_action(player_id, act)

class GovernmentCtrl(CivPropController):
    def __init__(self, ws_client, city_ctrl, rule_ctrl):
        CivPropController.__init__(self, ws_client)
        self.city_ctrl = city_ctrl
        self.rule_ctrl = rule_ctrl
        self.prop_state = GovState(rule_ctrl)
        self.prop_actions = GovActions(ws_client, rule_ctrl, city_ctrl)

    def queue_preinfos(self):
        for rtype in [REPORT_ACHIEVEMENTS, REPORT_DEMOGRAPHIC, REPORT_TOP_5_CITIES, REPORT_WONDERS_OF_THE_WORLD]:
            self.request_report(rtype)

    @staticmethod
    def government_max_rate(govt_id):
        """
         Returns the max tax rate for a given government.
         FIXME: This shouldn't be hardcoded, but instead fetched
         from the effects.
        """
        if govt_id in [GOV_ANARCHY, GOV_DEMOCRACY]:
            return 100
        elif govt_id == GOV_DESPOTISM:
            return 60
        elif govt_id == GOV_MONARCHY:
            return 70
        elif govt_id in [GOV_COMMUNISM, GOV_REPUBLIC]:
            return 80
        else:
            return 100 #// this should not happen
    
    def request_report(self, rtype):
        packet = {"pid"  : packet_report_req,
                  "type" : rtype}
        self.ws_client.send_request(packet)

class ChangeGovernment(base_action.Action):
    action_key = "change_gov"
    def __init__(self, govt_id, city_ctrl, rule_ctrl, pplayer):
        base_action.Action.__init__(self)
        self.govt_id = govt_id
        self.city_ctrl = city_ctrl
        self.rule_ctrl = rule_ctrl
        self.pplayer = pplayer
        self.action_key += "_%s" % GOV_TXT[govt_id]

    def is_action_valid(self):
        #//hack for statue of liberty
        if self.govt_id == self.rule_ctrl.governments[self.pplayer['government']]['id']:
            return False

        pplayer = self.pplayer
        return self.city_ctrl.player_has_wonder(pplayer["playerno"], 63) or \
               ReqCtrl.are_reqs_active(pplayer, self.rule_ctrl.governments[self.govt_id]["reqs"],
                                       RPT_CERTAIN)
    def _action_packet(self):
        packet = {"pid" : packet_player_change_government,
                  "government" : self.govt_id}
        return packet
