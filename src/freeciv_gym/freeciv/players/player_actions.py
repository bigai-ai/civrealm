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
from freeciv_gym.freeciv.utils.fc_types import packet_player_rates, \
    packet_diplomacy_init_meeting_req, packet_diplomacy_cancel_meeting_req, \
    packet_diplomacy_accept_treaty_req, packet_diplomacy_cancel_pact, \
    packet_diplomacy_create_clause_req, packet_diplomacy_remove_clause_req
import freeciv_gym.freeciv.players.player_const as player_const
import freeciv_gym.freeciv.players.player_helpers as player_helpers

from freeciv_gym.freeciv.tech.tech_helpers import is_tech_known, player_invention_state
import freeciv_gym.freeciv.tech.tech_const as tech_const
from freeciv_gym.freeciv.players.player_const import BASE_CLAUSES, CONFLICTING_CLAUSES
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger


class PlayerOptions(ActionList):
    def __init__(self, ws_client, rule_ctrl, dipl_ctrl, city_ctrl, players):
        super().__init__(ws_client)
        self.players = players
        self.rule_ctrl = rule_ctrl
        self.dipl_ctrl = dipl_ctrl
        self.city_ctrl = city_ctrl
        self.city_set = set()
        self.before_max_gold = 0
        self.current_max_gold = 0
        self.ws_client = ws_client

    def _can_actor_act(self, actor_id):
        return True

    def update(self, pplayer):
        new_city_set = self.new_cities()
        self.update_max_gold()

        for counter_id in self.players:
            counterpart = self.players[counter_id]

            if not counterpart['is_alive']:
                if self.actor_exists(counter_id):
                    del self._action_dict[counter_id]
                continue

            if self.actor_exists(counter_id):
                # ===================================================================
                # ====================== Consider trade gold & cities ===============
                # ===================================================================
                """
                if counterpart != pplayer and len(new_city_set) > 0:
                    self.update_city_action_set(counter_id, pplayer, counterpart, new_city_set)
                    self.update_city_action_set(counter_id, counterpart, pplayer, new_city_set)

                if counterpart != pplayer and self.current_max_gold > self.before_max_gold:
                    self.update_gold_action_set(counter_id, pplayer, counterpart)
                    self.update_gold_action_set(counter_id, counterpart, pplayer)
                """
                continue

            self.add_actor(counter_id)
            if counterpart == pplayer:
                self.update_player_options(counter_id, pplayer)
            else:
                self.update_counterpart_options(counter_id, pplayer, counterpart, new_city_set)

        self.city_set = set(self.city_ctrl.cities.keys())
        self.before_max_gold = self.current_max_gold

    def has_statue_of_liberty(self, cur_player):
        return has_statue_of_liberty(self.city_ctrl.cities, cur_player)

    def update_player_options(self, counter_id, cur_player):
        """
        self.add_action(counter_id, IncreaseLux(cur_player))
        self.add_action(counter_id, DecreaseLux(cur_player))
        self.add_action(counter_id, IncreaseSci(cur_player))
        self.add_action(counter_id, DecreaseSci(cur_player))
        self.add_action(counter_id, IncreaseTax(cur_player))
        self.add_action(counter_id, DecreaseTax(cur_player))
        """

        for sci in range(10, 101, 10):
            for lux in range(10, 101, 10):
                for tax in range(10, 101, 10):
                    self.add_action(counter_id, SetSciLuxTax(cur_player, sci, lux, tax))

    def update_counterpart_options(self, counter_id, cur_player, counterpart, new_city_set):
        if self.diplomacy_possible(cur_player, counterpart):
            self.add_action(counter_id, StartNegotiate(self.dipl_ctrl, cur_player, counterpart))
            self.add_action(counter_id, StopNegotiate(self.dipl_ctrl, cur_player, counterpart))
            self.add_action(counter_id, AcceptTreaty(self.dipl_ctrl, cur_player, counterpart))
            self.add_action(counter_id, CancelTreaty(self.dipl_ctrl, cur_player, counterpart, self.city_ctrl))
            self.add_action(counter_id, CancelVision(self.dipl_ctrl, cur_player, counterpart))

            self.update_clause_options(counter_id, cur_player, counterpart, new_city_set)
            self.update_clause_options(counter_id, counterpart, cur_player, new_city_set)

    def update_clause_options(self, counter_id, cur_player, counterpart, new_city_set):
        for ctype in BASE_CLAUSES:
            add_clause = AddClause(ctype, 1, counter_id, cur_player, counterpart, self.dipl_ctrl, self.ws_client)
            self.add_action(counter_id, add_clause)
            self.add_action(counter_id, RemoveClause(ctype, 1, counter_id, cur_player, counterpart, self.dipl_ctrl))

            # TODO: check the meaning when value = 0 under this scenario
            # self.add_action(counter_id, RemoveClause(ctype, 0, counter_id, cur_player, counterpart, self.dipl_ctrl))

        if self.rule_ctrl.game_info["trading_tech"]:
            for tech_id in self.rule_ctrl.techs:
                clause_type = player_const.CLAUSE_ADVANCE
                add_trade_tech_clause = AddTradeTechClause(clause_type, tech_id, counter_id, cur_player, counterpart,
                                                           self.dipl_ctrl, self.ws_client, self.rule_ctrl, self.players)
                self.add_action(counter_id, add_trade_tech_clause)

                rem_clause = RemoveClause(clause_type, tech_id, counter_id, cur_player, counterpart, self.dipl_ctrl)
                self.add_action(counter_id, rem_clause)

        # ===================================================================
        # ====================== Consider trade gold & cities ===============
        # ===================================================================
        """
        self.update_city_action_set(counter_id, cur_player, counterpart, new_city_set)
        self.update_gold_action_set(counter_id, cur_player, counterpart)
        """

    def update_max_gold(self):
        for player_id in self.players:
            if self.current_max_gold < self.players[player_id]['gold']:
                self.current_max_gold = self.players[player_id]['gold']

    def update_gold_action_set(self, counter_id, cur_player, counterpart):
        for pgold in range(self.before_max_gold + 1, self.current_max_gold + 1):
            self.add_action(counter_id, AddTradeGoldClause(
                player_const.CLAUSE_GOLD, pgold, counter_id, cur_player, counterpart, self.dipl_ctrl,
                self.ws_client, self.rule_ctrl, self.players))

            self.add_action(counter_id, RemoveClause(
                player_const.CLAUSE_GOLD, pgold, counter_id, cur_player, counterpart, self.dipl_ctrl))

    def new_cities(self):
        return set(self.city_ctrl.cities.keys()) - self.city_set

    def update_city_action_set(self, counter_id, cur_player, counterpart, new_city_set):
        for pcity in new_city_set:
            self.add_action(counter_id, AddTradeCityClause(
                player_const.CLAUSE_CITY, pcity, counter_id, cur_player, counterpart, self.dipl_ctrl,
                self.ws_client, self.rule_ctrl, self.city_ctrl))

            self.add_action(counter_id, RemoveClause(
                player_const.CLAUSE_CITY, pcity, counter_id, cur_player, counterpart, self.dipl_ctrl))

    def diplomacy_possible(self, cur_player, counterpart):
        if self.rule_ctrl.game_info['diplomacy'] == player_const.DIPLO_FOR_ALL:
            return True
        elif self.rule_ctrl.game_info['diplomacy'] == player_const.DIPLO_FOR_HUMANS:
            return cur_player['ai_skill_level'] == 0 and counterpart['ai_skill_level'] == 0
        elif self.rule_ctrl.game_info['diplomacy'] == player_const.DIPLO_FOR_AIS:
            return cur_player['ai_skill_level'] > 0 and counterpart['ai_skill_level'] > 0
        elif self.rule_ctrl.game_info['diplomacy'] == player_const.DIPLO_NO_AIS:
            return cur_player['ai_skill_level'] != 0 or counterpart['ai_skill_level'] != 0
        elif self.rule_ctrl.game_info['diplomacy'] == player_const.DIPLO_NO_MIXED:
            return ((cur_player['ai_skill_level'] == 0 and counterpart['ai_skill_level'] == 0)
                    or (cur_player['ai_skill_level'] != 0 and counterpart['ai_skill_level'] != 0))
        elif self.rule_ctrl.game_info['diplomacy'] == player_const.DIPLO_FOR_TEAMS:
            return cur_player['team'] == counterpart['team']
        else:
            return False


class IncreaseSci(base_action.Action):
    action_key = "increase_sci"

    def __init__(self, cur_player):
        super().__init__()
        self.cur_player = cur_player
        self.playerno = cur_player['playerno']

    def is_action_valid(self):
        return self.cur_player["science"] + 10 <= player_helpers.government_max_rate(self.cur_player['government'])

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

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
        self.wait_for_pid = (51, self.playerno)
        return packet


class DecreaseSci(IncreaseSci):
    action_key = "decrease_sci"

    def is_action_valid(self):
        return 0 <= self.cur_player["science"] - 10

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.sci -= 10
        if self.lux < player_helpers.government_max_rate(self.cur_player['government']):
            self.lux += 10
        else:
            self.tax += 10


class IncreaseLux(IncreaseSci):
    action_key = "increase_lux"

    def is_action_valid(self):
        return self.cur_player["luxury"] + 10 <= player_helpers.government_max_rate(self.cur_player['government'])

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.lux += 10
        if self.tax > 0:
            self.tax -= 10
        else:
            self.sci -= 10


class DecreaseLux(IncreaseSci):
    action_key = "decrease_lux"

    def is_action_valid(self):
        return 0 <= self.cur_player["luxury"] - 10

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.lux -= 10
        if self.tax < player_helpers.government_max_rate(self.cur_player['government']):
            self.tax += 10
        else:
            self.sci += 10


class IncreaseTax(IncreaseSci):
    action_key = "increase_tax"

    def is_action_valid(self):
        return self.cur_player["tax"] + 10 <= player_helpers.government_max_rate(self.cur_player['government'])

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.tax += 10
        if self.lux > 0:
            self.lux -= 10
        else:
            self.sci -= 10


class DecreaseTax(IncreaseSci):
    action_key = "decrease_tax"

    def is_action_valid(self):
        return 0 <= self.cur_player["tax"] - 10

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.tax -= 10
        if self.lux < player_helpers.government_max_rate(self.cur_player['government']):
            self.lux += 10
        else:
            self.sci += 10


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


class StartNegotiate(base_action.Action):
    """
    logic from freeciv/common/diptreaty.c
    func: could_meet_with_player
    """

    action_key = "start_negotiation"

    def __init__(self, dipl_ctrl, cur_player, counterpart):
        super().__init__()
        self.dipl_ctrl = dipl_ctrl
        self.cur_player = cur_player
        self.counterpart = counterpart
        self.action_key += "_%i" % counterpart['playerno']

    def is_action_valid(self):
        if self.counterpart['playerno'] not in self.dipl_ctrl.diplomacy_clause_map.keys():
            if self.dipl_ctrl.is_barbarian_pirate(self.counterpart['nation']):
                return False
            if (self.cur_player['real_embassy'][self.counterpart['playerno']]
                    or self.counterpart['real_embassy'][self.cur_player['playerno']] or
                    self.dipl_ctrl.contact_turns_left[self.cur_player['playerno']][self.counterpart['playerno']] > 0 or
                    self.dipl_ctrl.contact_turns_left[self.counterpart['playerno']][self.cur_player['playerno']] > 0):
                return True
        return False

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_init_meeting_req,
                  "counterpart": self.counterpart["playerno"]}

        self.wait_for_pid = (96, self.counterpart["playerno"])
        return packet


class AcceptTreaty(StartNegotiate):
    action_key = "accept_treaty"

    def is_action_valid(self):
        return self.counterpart['playerno'] in self.dipl_ctrl.diplomacy_clause_map.keys()

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_accept_treaty_req,
                  "counterpart": self.counterpart["playerno"]}
        self.wait_for_pid = (104, self.counterpart["playerno"])
        return packet


class CancelTreaty(StartNegotiate):
    """
    logic from freeciv/common/player.c
    func: pplayer_can_cancel_treaty
    """

    action_key = "cancel_treaty"

    def __init__(self, dipl_ctrl, cur_player, counterpart, city_ctrl):
        super().__init__(dipl_ctrl, cur_player, counterpart)
        self.city_ctrl = city_ctrl

    def is_action_valid(self):
        return (self.dipl_ctrl.check_not_dipl_states(self.counterpart['playerno']) and
                self.counterpart['team'] != self.cur_player['team'] and not self.senate_blocking())

    def senate_blocking(self):
        liberty_flag = has_statue_of_liberty(self.city_ctrl.cities, self.cur_player)
        return (self.dipl_ctrl.reason_to_cancel[self.cur_player['playerno']][self.counterpart['playerno']] == 0
                and self.dipl_ctrl.is_republic_democracy(self.cur_player['government']) and not liberty_flag)

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_cancel_pact,
                  "other_player_id": self.counterpart["playerno"],
                  "clause": self.dipl_ctrl.diplstates[self.counterpart['playerno']]}

        self.wait_for_pid = (59, (self.cur_player['playerno'], self.counterpart["playerno"]))
        return packet


class StopNegotiate(StartNegotiate):
    action_key = "stop_negotiation"

    def is_action_valid(self):
        return self.counterpart['playerno'] in self.dipl_ctrl.diplomacy_clause_map.keys()

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_cancel_meeting_req,
                  "counterpart": self.counterpart["playerno"]}
        self.wait_for_pid = (98, self.counterpart["playerno"])
        return packet


class CancelVision(StartNegotiate):
    action_key = "cancel_vision"

    def is_action_valid(self):
        return (self.counterpart['team'] != self.cur_player['team']
                and self.cur_player['gives_shared_vision'][self.counterpart['playerno']] == 1)

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_cancel_pact,
                  "other_player_id": self.counterpart["playerno"],
                  "clause": player_const.CLAUSE_VISION}
        self.wait_for_pid = (51, self.cur_player['playerno'])
        return packet


class RemoveClause(base_action.Action):
    action_key = "remove_clause"

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart, dipl_ctrl):
        super().__init__()
        self.clause_type = clause_type
        self.value = value
        self.cur_player = cur_player
        self.counterpart = counterpart
        self.giver = cur_player['playerno']
        self.receiver = counterpart['playerno']
        self.dipl_ctrl = dipl_ctrl
        self.counter_id = counter_id
        self.action_key += "_%s_%i_%i_%i" % (player_const.CLAUSE_TXT[clause_type], value, self.giver, self.receiver)

    def is_action_valid(self):
        if self.if_on_meeting():
            return self.if_clause_exists()
        return False

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_remove_clause_req,
                  "counterpart": self.counter_id,
                  "giver": self.giver,
                  "type": self.clause_type,
                  "value": self.value}
        self.wait_for_pid = (102, self.counter_id)
        return packet

    def if_on_meeting(self):
        return self.counter_id in self.dipl_ctrl.diplomacy_clause_map.keys()

    def if_clause_exists(self):
        clauses = self.dipl_ctrl.diplomacy_clause_map[self.counter_id]
        for clause in clauses:
            if clause['giver'] == self.giver and clause['type'] == self.clause_type and clause['value'] == self.value:
                return True
        return False


class AddClause(RemoveClause):
    action_key = "add_clause"

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart, dipl_ctrl, ws_client):
        super().__init__(clause_type, value, counter_id, cur_player, counterpart, dipl_ctrl)
        self.ws_client = ws_client

    def is_action_valid(self):

        if self.if_on_meeting():
            if self.cur_player['playerno'] == self.counter_id and self.clause_type in CONFLICTING_CLAUSES:
                return False

            ds = self.dipl_ctrl.diplstates[self.counter_id]
            if ((ds == player_const.DS_PEACE and self.clause_type == player_const.CLAUSE_PEACE)
                    or (ds == player_const.DS_ARMISTICE and self.clause_type == player_const.CLAUSE_PEACE)
                    or (ds == player_const.DS_ALLIANCE and self.clause_type == player_const.CLAUSE_ALLIANCE)
                    or (ds == player_const.CLAUSE_CEASEFIRE and self.clause_type == player_const.CLAUSE_CEASEFIRE)):
                fc_logger.debug(f'we already have this diplomatic state: {self.clause_type}')
                return False

            if self.clause_type == player_const.CLAUSE_EMBASSY and self.counterpart['real_embassy'][self.cur_player['playerno']]:
                fc_logger.debug('already has embassy')
                return False

            if self.clause_type == player_const.CLAUSE_ALLIANCE:
                ds_alliance = player_const.DS_ALLIANCE

                for p in self.dipl_ctrl.others_diplstates[self.cur_player['playerno']]:
                    if (self.dipl_ctrl.others_diplstates[self.cur_player['playerno']][p] == player_const.DS_WAR and
                            p in self.dipl_ctrl.others_diplstates[self.counterpart['playerno']] and
                            self.dipl_ctrl.others_diplstates[self.counterpart['playerno']][p] == ds_alliance):
                        return False

            return not self.if_clause_exists()
        return False

    def remove_conflicting_clause(self):
        if self.clause_type in CONFLICTING_CLAUSES:
            clauses = self.dipl_ctrl.diplomacy_clause_map[self.counter_id]
            for clause in clauses:
                if clause['type'] in CONFLICTING_CLAUSES:
                    if clause['giver'] == self.cur_player['playerno']:
                        rem_clause = RemoveClause(clause['type'], clause['value'], self.counter_id,
                                                  self.cur_player, self.counterpart, self.dipl_ctrl)
                    else:
                        rem_clause = RemoveClause(clause['type'], clause['value'], self.counter_id,
                                                  self.counterpart, self.cur_player, self.dipl_ctrl)
                    if rem_clause.is_action_valid():
                        rem_clause.trigger_action(self.ws_client)
                        break

    def _action_packet(self):
        self.remove_conflicting_clause()
        packet = {"pid": packet_diplomacy_create_clause_req,
                  "counterpart": self.counter_id,
                  "giver": self.giver,
                  "type": self.clause_type,
                  "value": self.value}
        self.wait_for_pid = (100, self.counter_id)
        return packet


class AddTradeTechClause(AddClause):
    action_key = "trade_tech_clause"

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart,
                 dipl_ctrl, ws_client, rule_ctrl, players):
        super().__init__(clause_type, value, counter_id, cur_player, counterpart, dipl_ctrl, ws_client)
        self.rule_ctrl = rule_ctrl
        self.players = players

    def is_action_valid(self):
        if self.if_on_meeting():
            return (not self.if_clause_exists() and is_tech_known(self.cur_player, self.value)
                    and player_invention_state(self.counterpart, self.value) in
                    [tech_const.TECH_UNKNOWN, tech_const.TECH_PREREQS_KNOWN])
        return False


class AddTradeGoldClause(AddClause):
    action_key = "trade_gold_clause"

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart, dipl_ctrl, ws_client, rule_ctrl,
                 players):
        super().__init__(clause_type, value, counter_id, cur_player, counterpart, dipl_ctrl, ws_client)
        self.rule_ctrl = rule_ctrl
        self.players = players

    def is_action_valid(self):
        if not self.rule_ctrl.game_info["trading_gold"]:
            return False
        if self.if_on_meeting():
            return not self.if_clause_exists() and not self.value > self.players[self.giver]['gold']
        return False


class AddTradeCityClause(AddClause):
    action_key = "trade_city_clause"

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart, dipl_ctrl, ws_client, rule_ctrl,
                 city_ctrl):
        super().__init__(clause_type, value, counter_id, cur_player, counterpart, dipl_ctrl, ws_client)
        self.rule_ctrl = rule_ctrl
        self.city_ctrl = city_ctrl

    def is_action_valid(self):
        if not self.rule_ctrl.game_info["trading_city"]:
            return False
        if self.value not in self.city_ctrl.cities:
            return False
        if self.if_on_meeting():
            return (not self.if_clause_exists() and not self.city_ctrl.cities[self.value]['capital']
                    and self.city_ctrl.cities[self.value]['owner'] == self.giver)
        return False


def has_statue_of_liberty(cities, cur_player):
    for city_id in cities:
        pcity = cities[city_id]

        if pcity['owner'] == cur_player['playerno'] and 'improvements' in pcity and pcity['improvements'][63]:
            return True

    return False
