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
from freeciv_gym.freeciv.players.diplomacy import CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE,\
    CLAUSE_MAP, CLAUSE_SEAMAP, CLAUSE_VISION, CLAUSE_EMBASSY, CLAUSE_ADVANCE,\
    CLAUSE_TXT

from freeciv_gym.freeciv.players.government import GovernmentCtrl
from freeciv_gym.freeciv.research.tech_helpers import is_tech_known, player_invention_state,\
    TECH_UNKNOWN, TECH_PREREQS_KNOWN

from freeciv_gym.freeciv.utils.freeciv_logging import logger


class PlayerOptions(ActionList):
    def __init__(self, ws_client, rule_ctrl, players, clstate):
        super().__init__(ws_client)
        self.players = players
        self.clstate = clstate
        self.rule_ctrl = rule_ctrl

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
                self.update_counterpart_options(counter_id, pplayer, counterpart)

    def update_player_options(self, counter_id, pplayer):
        maxrate = GovernmentCtrl.government_max_rate(pplayer['government'])

        cur_state = {"tax": pplayer['tax'], "sci": pplayer["science"],
                     "lux": pplayer["luxury"], "max_rate": maxrate}

        logger.info(cur_state)
        self.add_action(counter_id, IncreaseLux(**cur_state))
        self.add_action(counter_id, DecreaseLux(**cur_state))
        self.add_action(counter_id, DecreaseSci(**cur_state))
        self.add_action(counter_id, IncreaseSci(**cur_state))

    def update_counterpart_options(self, counter_id, cur_player, counterpart):
        self.add_action(counter_id, StartNegotiate(counterpart))
        self.add_action(counter_id, StopNegotiate(counterpart))
        self.add_action(counter_id, AcceptTreaty(counterpart))
        self.update_clause_options(counter_id, cur_player, counterpart)
        self.update_clause_options(counter_id, counterpart, cur_player)

    def update_clause_options(self, counter_id, giver, taker):
        cur_p = self.clstate.cur_player()
        base_clauses = [CLAUSE_MAP, CLAUSE_SEAMAP, CLAUSE_VISION, CLAUSE_EMBASSY,
                        CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]

        for ctype in base_clauses:
            self.add_action(counter_id, AddClause(ctype, 1, giver, taker, cur_p))
            self.add_action(counter_id, RemoveClause(ctype, 1, giver, taker, cur_p))

        for ctype in [CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]:
            self.add_action(counter_id, CancelClause(ctype, 1, giver, taker, cur_p))

        for tech_id in self.rule_ctrl.techs:
            self.add_action(counter_id, AddTradeTechClause(CLAUSE_ADVANCE, tech_id,
                                                           giver, taker, cur_p, self.rule_ctrl))
        """
        if self.ruleset.game["trading_city"]:
            for city_id in cities:
                pcity = cities[city_id]
                if city_owner(pcity) == giver and not does_city_have_improvement(pcity, "Palace"):
                    all_clauses.append({"type": CLAUSE_CITY, "value": city_id})

        if self.ruleset.game["trading_gold"]:
            if giver == self.player_ctrl.clstate.cur_player()['playerno']:
                all_clauses.append({"type": CLAUSE_GOLD, "value": ("#self_gold").val(value)})
            else:
                all_clauses.append({"type": CLAUSE_GOLD, "value": ("#counterpart_gold").val(value)})
        """


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
        return 0 <= self.sci+10 <= 100

    def _change_rate(self):
        self.sci += 10

    def _action_packet(self):
        self.tax = self.max_rate - self.sci - self.lux
        packet = {"pid": packet_player_rates,
                  "tax": self.tax, "luxury": self.lux, "science": self.sci}

        return packet


class DecreaseSci(IncreaseSci):
    action_key = "decrease_sci"

    def is_action_valid(self):
        return 0 <= self.sci - 10 <= 100

    def _change_rate(self):
        self.sci -= 10


class IncreaseLux(IncreaseSci):
    action_key = "increase_lux"

    def is_action_valid(self):
        return 0 <= self.lux + 10 <= 100

    def _change_rate(self):
        self.lux += 10


class DecreaseLux(IncreaseSci):
    action_key = "decrease_lux"

    def is_action_valid(self):
        return 0 <= self.lux - 10 <= 100

    def _change_rate(self):
        self.lux -= 10


class StartNegotiate(base_action.Action):
    action_key = "start_negotiation"

    def __init__(self, counterpart):
        super().__init__()
        self.counterpart = counterpart

    def is_action_valid(self):
        return True

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_init_meeting_req,
                  "counterpart": self.counterpart["playerno"]}
        return packet


class AcceptTreaty(StartNegotiate):
    action_key = "accept_treaty"

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_accept_treaty_req,
                  "counterpart": self.counterpart["playerno"]}
        return packet


class StopNegotiate(StartNegotiate):
    action_key = "stop_negotiation"

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_cancel_meeting_req,
                  "counterpart": self.counterpart["playerno"]}
        return packet


class RemoveClause(base_action.Action):
    action_key = "remove_clause"

    def __init__(self, clause_type, value, giver, taker, cur_player):
        super().__init__()
        self.clause_type = clause_type
        self.value = value
        self.giver = giver
        self.taker = taker
        self.cur_player = cur_player
        self.action_key += "_cl%s_player%i" % (CLAUSE_TXT[clause_type],
                                               self.giver["playerno"])

    def is_action_valid(self):
        return True
        # TODO: To be investigated

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_remove_clause_req,
                  "counterpart": self.taker["playerno"],
                  "giver": self.giver["playerno"],
                  "type": self.clause_type,
                  "value": self.value}
        return packet


class AddClause(RemoveClause):
    action_key = "add_clause"

    def is_action_valid(self):
        if self.clause_type in [CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]:
            return self.giver == self.cur_player
        return True

    def trigger_action(self, ws_client):
        if self.clause_type in [CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]:
            # // eg. creating peace treaty requires removing ceasefire first.
            rem_packet = RemoveClause._action_packet(self)
            ws_client.send_request(rem_packet)
        RemoveClause.trigger_action(self, ws_client)

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_create_clause_req,
                  "counterpart": self.taker["playerno"],
                  "giver": self.giver["playerno"],
                  "type": self.clause_type,
                  "value": self.value}
        return packet


class CancelClause(AddClause):
    action_key = "cancel_clause"

    def is_action_valid(self):
        if self.clause_type in [CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]:
            return self.giver == self.cur_player
        return False

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_cancel_pact,
                  "other_player_id": self.taker["playerno"],
                  "clause": self.clause_type}
        return packet


class AddTradeTechClause(AddClause):
    action_key = "trade_tech_clause"

    def __init__(self, clause_type, value, giver, taker, cur_player, rule_ctrl):
        super().__init__(clause_type, value, giver, taker, cur_player)
        self.rule_ctrl = rule_ctrl
        self.action_key += "_%i_%s" % (value, rule_ctrl.techs[value]["name"])

    def is_action_valid(self):
        if not self.rule_ctrl.game_info["trading_tech"]:
            return False
        return is_tech_known(self.giver, self.value) and \
            player_invention_state(self.taker, self.value) in [TECH_UNKNOWN,
                                                               TECH_PREREQS_KNOWN]
