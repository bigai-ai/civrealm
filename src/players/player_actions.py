'''
Created on 24.02.2018

@author: christian
'''
from utils import base_action
from utils.fc_types import packet_player_rates,\
    packet_diplomacy_init_meeting_req, packet_diplomacy_cancel_meeting_req,\
    packet_diplomacy_accept_treaty_req, packet_diplomacy_cancel_pact,\
    packet_diplomacy_create_clause_req, packet_diplomacy_remove_clause_req
from players.diplomacy import CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE
from research.tech import TECH_KNOWN, TECH_UNKNOWN, TECH_PREREQS_KNOWN, TechCtrl

class IncreaseSci(base_action.Action):
    action_key = "increase_sci"
    def __init__(self, ws_client, tax, sci, lux, max_rate):
        base_action.Action.__init__(self, ws_client)
        self.tax = self.get_corrected_num(tax)
        self.sci = self.get_corrected_num(sci)
        self.lux = self.get_corrected_num(lux)
        self.max_rate = max_rate

    def get_corrected_num(self, num):
        if num % 10 != 0:
            return num - (num % 10)

    def is_action_valid(self):
        return 0 <= self.sci+10 <= 100

    def _change_rate(self):
        self.sci += 10

    def _action_packet(self):
        self.tax = self.max_rate - self.sci - self.lux
        packet = {"pid" : packet_player_rates,
                  "tax" : self.tax, "luxury" : self.lux, "science" : self.sci }

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
    def __init__(self, ws_client, counterpart):
        base_action.Action.__init__(self, ws_client)
        self.counterpart = counterpart

    def is_action_valid(self):
        return True

    def _action_packet(self):
        packet = {"pid" : packet_diplomacy_init_meeting_req,
                  "counterpart" : self.counterpart["playerno"]}
        return packet

class AcceptTreaty(StartNegotiate):
    action_key = "accept_treaty"
    def _action_packet(self):
        packet = {"pid" : packet_diplomacy_accept_treaty_req,
                  "counterpart" : self.counterpart["playerno"]}
        return packet

class StopNegotiate(StartNegotiate):
    action_key = "stop_negotiation"
    def _action_packet(self):
        packet = {"pid" : packet_diplomacy_cancel_meeting_req,
                  "counterpart" : self.counterpart["playerno"]}
        return packet

class RemoveClause(base_action.Action):
    action_key = "remove_clause"
    def __init__(self, ws_client, clause_type, value, giver, taker, cur_player):
        base_action.Action.__init__(self, ws_client)
        self.clause_type = clause_type
        self.value = value
        self.giver = giver
        self.taker = taker
        self.cur_player = cur_player
        self.action_key += "_%i" % clause_type

    def _action_packet(self):
        packet = {"pid" : packet_diplomacy_remove_clause_req,
                  "counterpart" : self.taker["playerno"],
                  "giver": self.giver["playerno"],
                  "type" : self.clause_type,
                  "value": self.value}
        return packet

class AddClause(RemoveClause):
    action_key = "add_clause"
    def is_action_valid(self):
        if self.clause_type in [CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]:
            return self.giver == self.cur_player
        return True

    def trigger_action(self):
        if self.clause_type in [CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]:
            #// eg. creating peace treaty requires removing ceasefire first.
            rem_packet = RemoveClause._action_packet(self)
            self.ws_client.send_request(rem_packet)
        RemoveClause.trigger_action(self)

    def _action_packet(self):
        packet = {"pid" : packet_diplomacy_create_clause_req,
                  "counterpart" : self.taker["playerno"],
                  "giver": self.giver["playerno"],
                  "type" : self.clause_type,
                  "value": self.value}
        return packet

class CancelClause(AddClause):
    action_key = "cancel_clause"
    def is_action_valid(self):
        if self.clause_type in [CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]:
            return self.giver == self.cur_player
        return False

    def _action_packet(self):
        packet = {"pid" : packet_diplomacy_cancel_pact,
                  "other_player_id" : self.taker["playerno"],
                  "clause" : self.clause_type}
        return packet

class AddTradeTechClause(AddClause):
    action_key = "trade_tech_clause"
    def __init__(self, ws_client, clause_type, value, giver, taker, cur_player, rule_ctrl):
        AddClause.__init__(self, ws_client, clause_type, value, giver, taker, cur_player)
        self.rule_ctrl = rule_ctrl
        self.action_key += "_%i" % value

    def is_action_valid(self):
        if not self.rule_ctrl.game_info["trading_tech"]:
            return False
        return TechCtrl.player_invention_state(self.giver, self.value) == TECH_KNOWN and \
               TechCtrl.player_invention_state(self.taker, self.value) in [TECH_UNKNOWN,
                                                                           TECH_PREREQS_KNOWN]
