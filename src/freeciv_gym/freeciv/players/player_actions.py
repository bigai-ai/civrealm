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

from freeciv_gym.freeciv.utils import base_action
from freeciv_gym.freeciv.utils.base_action import ActionList
from freeciv_gym.freeciv.utils.fc_types import packet_player_rates,\
    packet_diplomacy_init_meeting_req, packet_diplomacy_cancel_meeting_req,\
    packet_diplomacy_accept_treaty_req, packet_diplomacy_cancel_pact,\
    packet_diplomacy_create_clause_req, packet_diplomacy_remove_clause_req
import freeciv_gym.freeciv.players.player_const as player_const

from freeciv_gym.freeciv.players.government import GovernmentCtrl
from freeciv_gym.freeciv.tech.tech_helpers import is_tech_known, player_invention_state
import freeciv_gym.freeciv.tech.tech_const as tech_const
# from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
# from freeciv_gym.freeciv.connectivity.client_state import ClientState

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger


class PlayerOptions(ActionList):
    # def __init__(self, ws_client, rule_ctrl: RulesetCtrl, players, clstate: ClientState):
    def __init__(self, ws_client, rule_ctrl, dipl_ctrl, players, clstate):
        super().__init__(ws_client)
        self.players = players
        self.clstate = clstate
        self.rule_ctrl = rule_ctrl
        self.dipl_ctrl = dipl_ctrl

    def _can_actor_act(self, actor_id):
        return True

    def update(self, pplayer):
        for counter_id in self.players:
            if self.actor_exists(counter_id):
                continue
            self.add_actor(counter_id)

            counterpart = self.players[counter_id]
            if counterpart == pplayer:
                self.update_player_options(counter_id, pplayer)
            else:
                self.update_counterpart_options(self.clstate, self.dipl_ctrl, counter_id, pplayer, counterpart)

    def update_player_options(self, counter_id, pplayer):
        maxrate = GovernmentCtrl.government_max_rate(pplayer['government'])

        cur_state = {"tax": pplayer['tax'], "sci": pplayer["science"],
                     "lux": pplayer["luxury"], "max_rate": maxrate}

        fc_logger.info(cur_state)

        increase_lux = IncreaseLux(**cur_state)
        if increase_lux.is_action_valid():
            self.add_action(counter_id, increase_lux)
        decrease_lux = DecreaseLux(**cur_state)
        if decrease_lux.is_action_valid():
            self.add_action(counter_id, decrease_lux )
        increase_sci = IncreaseSci(**cur_state)
        if increase_sci.is_action_valid():
            self.add_action(counter_id, increase_sci)
        decrease_sci = DecreaseSci(**cur_state)
        if decrease_sci.is_action_valid():
            self.add_action(counter_id, decrease_sci)
        increase_tax = IncreaseTax(**cur_state)
        if increase_tax.is_action_valid():
            self.add_action(counter_id, increase_tax)
        decrease_tax = DecreaseTax(**cur_state)
        if decrease_tax.is_action_valid():
            self.add_action(counter_id, decrease_tax)

    def update_counterpart_options(self, clstate, dipl_ctrl, counter_id, cur_player, counterpart):
        start_negotiate = StartNegotiate(clstate, dipl_ctrl, cur_player, counterpart)
        if start_negotiate.is_action_valid():
            self.add_action(counter_id, start_negotiate)

        stop_negotiate = StopNegotiate(clstate, dipl_ctrl, cur_player, counterpart)
        if stop_negotiate.is_action_valid():
            self.add_action(counter_id, stop_negotiate)

        accept_treaty = AcceptTreaty(clstate, dipl_ctrl, cur_player, counterpart)
        if accept_treaty.is_action_valid():
            self.add_action(counter_id, accept_treaty)

        if counter_id in dipl_ctrl.diplomacy_clause_map.keys():
            clauses = dipl_ctrl.diplomacy_clause_map[counter_id]
            for clause in clauses:
                counterpart_id = clause['counterpart']
                giver = clause['giver']
                type = clause['type']
                value = clause['value']
                remove_clause = RemoveClause(type, value, giver, counterpart_id)
                if remove_clause.is_action_valid():
                    self.add_action(counter_id, remove_clause)

        base_clauses = [player_const.CLAUSE_MAP, player_const.CLAUSE_SEAMAP, player_const.CLAUSE_VISION,
                        player_const.CLAUSE_EMBASSY, player_const.CLAUSE_CEASEFIRE, player_const.CLAUSE_PEACE,
                        player_const.CLAUSE_ALLIANCE]
        for ctype in base_clauses:
            add_clause_1 = AddClause(ctype, 1, cur_player['playerno'], counter_id)
            if add_clause_1.is_action_valid():
                self.add_action(counter_id, add_clause_1)

            add_clause_2 = AddClause(ctype, 1, counter_id, cur_player['playerno'])
            if add_clause_2.is_action_valid():
                self.add_action(counter_id, add_clause_2)

        for tech_id in self.rule_ctrl.techs:
            add_trade_tech_1 = AddTradeTechClause(player_const.CLAUSE_ADVANCE, tech_id,
                                                  cur_player['playerno'], counter_id,
                                                  self.rule_ctrl, self.players)
            if add_trade_tech_1.is_action_valid():
                self.add_action(counter_id, add_trade_tech_1)

            add_trade_tech_2 = AddTradeTechClause(player_const.CLAUSE_ADVANCE, tech_id,
                                                  counter_id, cur_player['playerno'],
                                                  self.rule_ctrl, self.players)
            if add_trade_tech_2.is_action_valid():
                self.add_action(counter_id, add_trade_tech_2)


class IncreaseSci(base_action.Action):
    action_key = "increase_sci"

    def __init__(self, tax, sci, lux, max_rate):
        super().__init__()
        self.tax = self.get_corrected_num(tax)
        self.sci = self.get_corrected_num(sci)
        self.lux = self.get_corrected_num(lux)
        self.max_rate = max_rate

    def get_corrected_num(self, num):
        if num % 10 != 0:
            return num - (num % 10)
        else:
            return num

    def is_action_valid(self):
        return 0 <= self.sci+10 <= self.max_rate

    def _change_rate(self):
        self.sci += 10
        if self.lux > 0:
            self.lux -= 10
        else:
            self.tax -= 10

    def _action_packet(self):
        self._change_rate()
        packet = {"pid": packet_player_rates,
                  "tax": self.tax,
                  "luxury": self.lux,
                  "science": self.sci}
        self.wait_for_pid = 51
        return packet


class DecreaseSci(IncreaseSci):
    action_key = "decrease_sci"

    def is_action_valid(self):
        return 0 <= self.sci - 10 <= self.max_rate

    def _change_rate(self):
        self.sci -= 10
        if self.lux < self.max_rate:
            self.lux += 10
        else:
            self.tax += 10


class IncreaseLux(IncreaseSci):
    action_key = "increase_lux"

    def is_action_valid(self):
        return 0 <= self.lux + 10 <= self.max_rate

    def _change_rate(self):
        self.lux += 10
        if self.tax > 0:
            self.tax -= 10
        else:
            self.sci -= 10


class DecreaseLux(IncreaseSci):
    action_key = "decrease_lux"

    def is_action_valid(self):
        return 0 <= self.lux - 10 <= self.max_rate

    def _change_rate(self):
        self.lux -= 10
        if self.tax < self.max_rate:
            self.tax += 10
        else:
            self.sci += 10


class IncreaseTax(IncreaseSci):
    action_key = "increase_tax"

    def is_action_valid(self):
        return 0 <= self.tax + 10 <= self.max_rate

    def _change_rate(self):
        self.tax += 10
        if self.lux > 0:
            self.lux -= 10
        else:
            self.sci -= 10


class DecreaseTax(IncreaseSci):
    action_key = "decrease_tax"

    def is_action_valid(self):
        return 0 <= self.tax - 10 <= self.max_rate

    def _change_rate(self):
        self.tax -= 10
        if self.lux < self.max_rate:
            self.lux += 10
        else:
            self.sci += 10


class StartNegotiate(base_action.Action):
    action_key = "start_negotiation"

    def __init__(self, clstate, dipl_ctrl, cur_player, counterpart):
        super().__init__()
        self.clstate = clstate
        self.dipl_ctrl = dipl_ctrl
        self.cur_player = cur_player
        self.counterpart = counterpart

    def is_action_valid(self):
        if (not self.clstate.client_is_observer() and self.counterpart != self.cur_player
                and self.counterpart['is_alive'] and self.cur_player['is_alive']):
            if self.dipl_ctrl.check_not_dipl_states(self.counterpart['playerno'], [player_const.DS_NO_CONTACT]):
                return True
        return False

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_init_meeting_req,
                  "counterpart": self.counterpart["playerno"]}
        return packet


class AcceptTreaty(StartNegotiate):
    action_key = "accept_treaty"

    def is_action_valid(self):
        return self.dipl_ctrl.active_diplomacy_meeting_id == self.counterpart['playerno']

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_accept_treaty_req,
                  "counterpart": self.counterpart["playerno"]}
        return packet


class StopNegotiate(StartNegotiate):
    action_key = "stop_negotiation"

    def is_action_valid(self):
        return self.dipl_ctrl.active_diplomacy_meeting_id == self.counterpart['playerno']

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_cancel_meeting_req,
                  "counterpart": self.counterpart["playerno"]}
        return packet


class RemoveClause(base_action.Action):
    action_key = "remove_clause"

    def __init__(self, clause_type, value, giver, counterpart):
        super().__init__()
        self.clause_type = clause_type
        self.value = value
        self.giver = giver
        self.counterpart = counterpart
        self.action_key += "_%s_player_%i" % (player_const.CLAUSE_TXT[clause_type], counterpart)

    def is_action_valid(self):
        return True

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_remove_clause_req,
                  "counterpart": self.counterpart,
                  "giver": self.giver,
                  "type": self.clause_type,
                  "value": self.value}
        return packet


class AddClause(RemoveClause):
    action_key = "add_clause"

    def is_action_valid(self):
        return True

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_create_clause_req,
                  "counterpart": self.counterpart,
                  "giver": self.giver,
                  "type": self.clause_type,
                  "value": self.value}
        return packet


class AddTradeTechClause(AddClause):
    action_key = "trade_tech_clause"

    def __init__(self, clause_type, value, giver, counterpart, rule_ctrl, players):
        super().__init__(clause_type, value, giver, counterpart)
        self.rule_ctrl = rule_ctrl
        self.counterpart = counterpart
        self.giver = giver
        self.players = players
        self.action_key += "_%s_%i" % (rule_ctrl.techs[value]["name"], value)

    def is_action_valid(self):
        if not self.rule_ctrl.game_info["trading_tech"]:
            return False
        return (is_tech_known(self.players[self.giver], self.value)
                and player_invention_state(self.players[self.counterpart], self.value)
                in [tech_const.TECH_UNKNOWN, tech_const.TECH_PREREQS_KNOWN])


