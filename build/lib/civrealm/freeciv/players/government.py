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


from civrealm.freeciv.connectivity.civ_connection import CivConnection
from civrealm.freeciv.game.ruleset import RulesetCtrl

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.utils import base_action
from civrealm.freeciv.utils.base_action import Action, ActionList
from civrealm.freeciv.utils.base_state import PlainState
from civrealm.freeciv.tech.req_info import ReqInfo

import civrealm.freeciv.players.player_const as player_const
from civrealm.freeciv.utils.fc_types import packet_player_change_government, packet_report_req, RPT_CERTAIN, packet_player_rates
import civrealm.freeciv.players.player_helpers as player_helpers


class GovState(PlainState):
    def __init__(self, rule_ctrl: RulesetCtrl):
        super().__init__()
        self.rule_ctrl = rule_ctrl

    def _update_state(self, pplayer):
        self._state["name"] = self.rule_ctrl.governments[pplayer['government']]['name']
        self._state["id"] = self.rule_ctrl.governments[pplayer['government']]['id']
        self._state["helptext"] = self.rule_ctrl.governments[pplayer['government']]['helptext']


class GovActions(ActionList):
    def __init__(self, ws_client: CivConnection, rule_ctrl: RulesetCtrl, dipl_ctrl):
        super().__init__(ws_client)
        self.rule_ctrl = rule_ctrl
        self.dipl_ctrl = dipl_ctrl

    def _can_actor_act(self, actor_id):
        return True

    def update(self, pplayer):
        player_id = pplayer["playerno"]
        if not self.actor_exists(player_id):
            self.add_actor(player_id)

            for govt_id in self.rule_ctrl.governments:
                self.add_action(player_id, ChangeGovernment(govt_id, self.rule_ctrl, self.dipl_ctrl, pplayer))

            for sci in range(0, 101, 10):
                for lux in range(0, (101 - sci), 10):
                    tax = 100 - sci - lux
                    self.add_action(player_id, SetSciLuxTax(pplayer, sci, lux, tax))


class GovernmentCtrl(CivPropController):
    def __init__(self, ws_client: CivConnection, rule_ctrl: RulesetCtrl, dipl_ctrl):
        super().__init__(ws_client)
        self.dipl_ctrl = dipl_ctrl
        self.rule_ctrl = rule_ctrl
        self.prop_state = GovState(rule_ctrl)
        self.prop_actions = GovActions(ws_client, rule_ctrl, dipl_ctrl)

    def register_all_handlers(self):
        pass

    def queue_preinfos(self):
        for rtype in [
                player_const.REPORT_ACHIEVEMENTS, player_const.REPORT_DEMOGRAPHIC, player_const.REPORT_TOP_5_CITIES,
                player_const.REPORT_WONDERS_OF_THE_WORLD]:
            self.request_report(rtype)

    def request_report(self, rtype):
        packet = {"pid": packet_report_req,
                  "type": rtype}
        self.ws_client.send_request(packet)


class ChangeGovernment(base_action.Action):
    action_key = "change_gov"

    def __init__(self, govt_id: int, rule_ctrl: RulesetCtrl, dipl_ctrl, pplayer: dict):
        super().__init__()
        self.govt_id = govt_id
        self.dipl_ctrl = dipl_ctrl
        self.rule_ctrl = rule_ctrl
        self.pplayer = pplayer
        self.action_key += "_%s" % player_const.GOV_TXT[govt_id]

    def is_action_valid(self):
        # //hack for statue of liberty
        if self.govt_id == self.rule_ctrl.governments[self.pplayer['government']]['id']:
            return False

        return (self.dipl_ctrl.prop_actions.has_statue_of_liberty(self.pplayer) or
                ReqInfo.are_reqs_active(self.pplayer, self.rule_ctrl.governments[self.govt_id]["reqs"], RPT_CERTAIN))

    def _action_packet(self):
        packet = {"pid": packet_player_change_government,
                  "government": self.govt_id}

        if self.govt_id == 0:
            self.wait_for_pid = (51, self.pplayer['playerno'])

        """
        switch to new gov in the end of the player phase
        self.wait_for_pid = (51, self.pplayer['playerno'])
        """
        return packet


class SetSciLuxTax(base_action.Action):
    action_key = "set_sci_lux_tax"

    def __init__(self, cur_player, sci, lux, tax):
        super().__init__()
        self.sci = sci
        self.lux = lux
        self.tax = tax
        self.cur_player = cur_player
        self.playerno = cur_player['playerno']
        self.action_key += "_%i_%i_%i" % (self.sci, self.lux, self.tax)

    def is_action_valid(self):
        if self.sci + self.lux + self.tax != 100:
            return False

        for p in [self.sci, self.lux, self.tax]:
            if p > player_helpers.government_max_rate(self.cur_player['government']):
                return False

        return True

    def _action_packet(self):
        packet = {"pid": packet_player_rates,
                  "tax": self.tax,
                  "luxury": self.lux,
                  "science": self.sci}
        self.wait_for_pid = (51, self.playerno)
        return packet

# TODO: Check if necessary to add this action to action_dict of gov


class GovDoNothing(Action):
    action_key = 'gov_do_nothing'

    def __init__(self, ws_client):
        super().__init__()
        self.ws_client = ws_client

    def is_action_valid(self):
        """ always valid """
        return True

    def _action_packet(self):
        return 'do_nothing'

    def trigger_action(self, ws_client):
        self.ws_client.send_message("No change for gov.")
