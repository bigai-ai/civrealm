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

from freeciv_gym.freeciv.utils.base_controller import CivPropController
from freeciv_gym.freeciv.utils.fc_types import packet_player_change_government, packet_report_req, RPT_CERTAIN
from freeciv_gym.freeciv.utils import base_action
from freeciv_gym.freeciv.utils.base_action import ActionList
from freeciv_gym.freeciv.utils.base_state import PlainState
from freeciv_gym.freeciv.tech.req_info import ReqInfo
# from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
# from freeciv_gym.freeciv.city.city_ctrl import CityCtrl
import freeciv_gym.freeciv.players.player_const as player_const




class GovState(PlainState):
    # def __init__(self, rule_ctrl: RulesetCtrl):
    def __init__(self, rule_ctrl):
        super().__init__()
        self.rule_ctrl = rule_ctrl

    def _update_state(self, pplayer):
        self._state["name"] = self.rule_ctrl.governments[pplayer['government']]['name']
        self._state["id"] = self.rule_ctrl.governments[pplayer['government']]['id']
        self._state["helptext"] = self.rule_ctrl.governments[pplayer['government']]['helptext']


class GovActions(ActionList):
    # def __init__(self, ws_client, rule_ctrl: RulesetCtrl, city_ctrl):
    def __init__(self, ws_client, rule_ctrl, city_ctrl):
        super().__init__(ws_client)
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
        super().__init__(ws_client)
        self.city_ctrl = city_ctrl
        self.rule_ctrl = rule_ctrl
        self.prop_state = GovState(rule_ctrl)
        self.prop_actions = GovActions(ws_client, rule_ctrl, city_ctrl)

    def register_all_handlers(self):
        pass

    def queue_preinfos(self):
        for rtype in [player_const.REPORT_ACHIEVEMENTS, player_const.REPORT_DEMOGRAPHIC, player_const.REPORT_TOP_5_CITIES, player_const.REPORT_WONDERS_OF_THE_WORLD]:
            self.request_report(rtype)

    @staticmethod
    def government_max_rate(govt_id):
        """
         Returns the max tax rate for a given government.
         FIXME: This shouldn't be hardcoded, but instead fetched
         from the effects.
        """
        if govt_id in [player_const.GOV_ANARCHY, player_const.GOV_DEMOCRACY]:
            return 100
        elif govt_id == player_const.GOV_DESPOTISM:
            return 60
        elif govt_id == player_const.GOV_MONARCHY:
            return 70
        elif govt_id in [player_const.GOV_COMMUNISM, player_const.GOV_REPUBLIC]:
            return 80
        else:
            return 100  # // this should not happen

    def request_report(self, rtype):
        packet = {"pid": packet_report_req,
                  "type": rtype}
        self.ws_client.send_request(packet)


class ChangeGovernment(base_action.Action):
    action_key = "change_gov"

    # def __init__(self, govt_id, city_ctrl: CityCtrl, rule_ctrl: RulesetCtrl, pplayer):
    def __init__(self, govt_id, city_ctrl, rule_ctrl, pplayer):
        super().__init__()
        self.govt_id = govt_id
        self.city_ctrl = city_ctrl
        self.rule_ctrl = rule_ctrl
        self.pplayer = pplayer
        self.action_key += "_%s" % player_const.GOV_TXT[govt_id]

    def is_action_valid(self):
        # //hack for statue of liberty
        if self.govt_id == self.rule_ctrl.governments[self.pplayer['government']]['id']:
            return False

        pplayer = self.pplayer
        return self.city_ctrl.player_has_wonder(pplayer["playerno"], 63) or \
            ReqInfo.are_reqs_active(pplayer, self.rule_ctrl.governments[self.govt_id]["reqs"],
                                    RPT_CERTAIN)

    def _action_packet(self):
        packet = {"pid": packet_player_change_government,
                  "government": self.govt_id}
        return packet
