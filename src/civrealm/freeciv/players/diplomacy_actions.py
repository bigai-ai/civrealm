# Copyright (C) 2023  The CivRealm project
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

from civrealm.freeciv.utils import base_action
from civrealm.freeciv.utils.base_action import Action, ActionList
from civrealm.freeciv.utils.fc_types import packet_diplomacy_init_meeting_req, packet_diplomacy_cancel_meeting_req, packet_diplomacy_accept_treaty_req, packet_diplomacy_cancel_pact, packet_diplomacy_create_clause_req, packet_diplomacy_remove_clause_req
import civrealm.freeciv.players.player_const as player_const

from civrealm.freeciv.tech.tech_helpers import is_tech_known, player_invention_state
import civrealm.freeciv.tech.tech_const as tech_const
from civrealm.freeciv.players.player_const import BASE_CLAUSES, CONFLICTING_CLAUSES
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.freeciv.utils.utility import geometric_sequence

GOLD_STEP = 1
GOLD_SET = geometric_sequence(length=15,start=25,end=1500)


class DiplOptions(ActionList):
    def __init__(
            self, ws_client, rule_ctrl, city_ctrl, player_ctrl, diplomacy_clause_map, contact_turns_left,
            reason_to_cancel, diplstates, others_diplstates):
        super().__init__(ws_client)

        self.rule_ctrl = rule_ctrl
        self.city_ctrl = city_ctrl
        self.player_ctrl = player_ctrl

        self.players = self.player_ctrl.players
        self.city_set = set()
        self.before_max_gold = 0
        self.current_max_gold = 0

        self.diplomacy_clause_map = diplomacy_clause_map
        self.contact_turns_left = contact_turns_left
        self.reason_to_cancel = reason_to_cancel
        self.diplstates = diplstates
        self.others_diplstates = others_diplstates

    def _can_actor_act(self, actor_id):
        return True

    def update(self, pplayer):
        new_city_set = self.new_cities()
        self.city_set = self.city_set.union(set(self.city_ctrl.cities.keys()))

        for counter_id in self.players:
            counterpart = self.players[counter_id]

            if not counterpart['is_alive']:
                if self.actor_exists(counter_id):
                    del self._action_dict[counter_id]
                continue

            if self.actor_exists(counter_id):
                # ===================================================================
                # ====================== Consider trade cities ===============
                # ===================================================================

                if counterpart != pplayer:
                    if len(new_city_set) > 0 and self.rule_ctrl.game_info["trading_city"]:
                        self.update_trade_city_clauses(counter_id, pplayer, counterpart, new_city_set)
                        self.update_trade_city_clauses(counter_id, counterpart, pplayer, new_city_set)

                continue

            if counterpart == pplayer or self.is_barbarian_pirate(self.players[counter_id]['nation']):
                continue
            self.add_actor(counter_id)
            self.update_counterpart_options(counter_id, pplayer, counterpart, self.city_set)

    def is_barbarian_pirate(self, nation_id):
        return self.rule_ctrl.nations[nation_id]['rule_name'].lower() in ['barbarian', 'pirate']

    def has_statue_of_liberty(self, cur_player):
        return has_statue_of_liberty(self.city_ctrl.cities, cur_player)

    def update_counterpart_options(self, counter_id, cur_player, counterpart, new_city_set):
        if self.diplomacy_possible(cur_player, counterpart):

            # automatically start a meeting when adding the 1st clause
            # self.add_action(counter_id, StartNegotiate(self.diplomacy_clause_map, self.contact_turns_left, cur_player, counterpart))

            self.add_action(counter_id, StopNegotiate(self.diplomacy_clause_map, self.contact_turns_left,
                                                      cur_player, counterpart))

            self.add_action(counter_id, AcceptTreaty(self.diplomacy_clause_map, self.contact_turns_left,
                                                     cur_player, counterpart, self.ws_client, self.diplstates, self.others_diplstates, self.players, self.city_ctrl))

            self.add_action(counter_id, CancelTreaty(self.diplomacy_clause_map, self.contact_turns_left,
                                                     cur_player, counterpart, self.city_ctrl, self.rule_ctrl, self.reason_to_cancel, self.diplstates))

            self.add_action(counter_id, CancelVision(self.diplomacy_clause_map,
                                                     self.contact_turns_left, cur_player, counterpart))

            self.update_clause_options(counter_id, cur_player, counterpart, new_city_set)
            self.update_clause_options(counter_id, counterpart, cur_player, new_city_set)

    def update_clause_options(self, counter_id, cur_player, counterpart, new_city_set):
        for ctype in BASE_CLAUSES:

            self.add_action(counter_id, AddClause(ctype, 1, counter_id, cur_player, counterpart,
                                                  self.diplomacy_clause_map, self.contact_turns_left, self.ws_client, self.diplstates, self.others_diplstates))

            self.add_action(counter_id, RemoveClause(ctype, 1, counter_id, cur_player,
                            counterpart, self.diplomacy_clause_map, self.contact_turns_left))

            # TODO: check the meaning when value = 0 under this scenario
            # self.add_action(counter_id, RemoveClause(ctype, 0, counter_id, cur_player, counterpart, self.dipl_ctrl))

        if self.rule_ctrl.game_info["trading_tech"]:
            for tech_id in self.rule_ctrl.techs:
                clause_type = player_const.CLAUSE_ADVANCE
                self.add_action(counter_id, AddTradeTechClause(clause_type, tech_id, counter_id, cur_player,
                                                               counterpart, self.diplomacy_clause_map, self.contact_turns_left, self.ws_client, self.diplstates, self.others_diplstates))

                self.add_action(counter_id, RemoveClause(clause_type, tech_id, counter_id, cur_player,
                                                         counterpart, self.diplomacy_clause_map, self.contact_turns_left))

        # ===================================================================
        # ====================== Consider trade gold & cities ===============
        # ===================================================================

        if self.rule_ctrl.game_info["trading_gold"]:
            for pgold in GOLD_SET:
                self.add_action(counter_id, AddTradeGoldClause(player_const.CLAUSE_GOLD, pgold, counter_id,
                                                               cur_player, counterpart, self.diplomacy_clause_map, self.contact_turns_left, self.ws_client, self.diplstates, self.others_diplstates, self.players))

                self.add_action(counter_id, RemoveClause(player_const.CLAUSE_GOLD, pgold, counter_id, cur_player,
                                                         counterpart, self.diplomacy_clause_map, self.contact_turns_left))


        if self.rule_ctrl.game_info["trading_city"]:
            self.update_trade_city_clauses(counter_id, cur_player, counterpart, new_city_set)

    '''
        if self.rule_ctrl.game_info["trading_gold"]:
            self.update_trade_gold_clauses(counter_id, cur_player, counterpart)

    def update_max_gold(self):
        for player_id in self.players:
            if self.current_max_gold < self.players[player_id]['gold']:
                self.current_max_gold = self.players[player_id]['gold']
    
    def update_trade_gold_clauses(self, counter_id, cur_player, counterpart):
        for pgold in range(self.before_max_gold + 1, self.current_max_gold + 1, GOLD_STEP):
            self.add_action(counter_id, 
                            AddTradeGoldClause(player_const.CLAUSE_GOLD, pgold, counter_id, cur_player, counterpart, self.diplomacy_clause_map, self.contact_turns_left, self.ws_client, self.diplstates, self.others_diplstates, self.players))

            self.add_action(counter_id, RemoveClause(player_const.CLAUSE_GOLD, pgold, counter_id, cur_player, counterpart, self.diplomacy_clause_map, self.contact_turns_left))
    '''

    def new_cities(self):
        return set(self.city_ctrl.cities.keys()) - self.city_set

    def update_trade_city_clauses(self, counter_id, cur_player, counterpart, new_city_set):
        for pcity in new_city_set:
            self.add_action(counter_id, AddTradeCityClause(player_const.CLAUSE_CITY, pcity, counter_id,
                                                           cur_player, counterpart, self.diplomacy_clause_map, self.contact_turns_left, self.ws_client, self.diplstates, self.others_diplstates, self.city_ctrl))

            self.add_action(counter_id, RemoveClause(player_const.CLAUSE_CITY, pcity, counter_id, cur_player,
                                                     counterpart, self.diplomacy_clause_map, self.contact_turns_left))

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


class StartNegotiate(base_action.Action):
    """
    logic from freeciv/common/diptreaty.c
    func: could_meet_with_player
    """

    action_key = "start_negotiation"

    def __init__(self, diplomacy_clause_map, contact_turns_left, cur_player, counterpart):
        super().__init__()
        self.diplomacy_clause_map = diplomacy_clause_map
        self.contact_turns_left = contact_turns_left

        self.cur_player = cur_player
        self.counterpart = counterpart
        self.action_key += "_%i" % counterpart['playerno']

    def is_action_valid(self):
        if self.counterpart['playerno'] not in self.diplomacy_clause_map.keys():
            if (self.cur_player['real_embassy'][self.counterpart['playerno']]
                    or self.counterpart['real_embassy'][self.cur_player['playerno']] or
                    self.contact_turns_left[self.cur_player['playerno']][self.counterpart['playerno']] > 0 or
                    self.contact_turns_left[self.counterpart['playerno']][self.cur_player['playerno']] > 0):
                return True

        return False

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_init_meeting_req,
                  "counterpart": self.counterpart["playerno"]}

        self.wait_for_pid = (96, self.counterpart["playerno"])
        return packet


class CancelTreaty(StartNegotiate):
    """
    logic from freeciv/common/player.c
    func: pplayer_can_cancel_treaty
    """

    action_key = "cancel_treaty"

    def __init__(
            self, diplomacy_clause_map, contact_turns_left, cur_player, counterpart, city_ctrl, rule_ctrl,
            reason_to_cancel, diplstates):
        super().__init__(diplomacy_clause_map, contact_turns_left, cur_player, counterpart)
        self.city_ctrl = city_ctrl
        self.rule_ctrl = rule_ctrl
        self.reason_to_cancel = reason_to_cancel
        self.diplstates = diplstates

    def is_action_valid(self):
        if self.counterpart['playerno'] in self.diplstates:
            if self.diplstates[self.counterpart['playerno']] in [player_const.DS_WAR, player_const.DS_NO_CONTACT]:
                return False

        if self.counterpart['team'] == self.cur_player['team']:
            return False

        return not self.senate_blocking()

    def senate_blocking(self):
        liberty_flag = has_statue_of_liberty(self.city_ctrl.cities, self.cur_player)
        return (self.reason_to_cancel[self.cur_player['playerno']][self.counterpart['playerno']] == 0
                and self.is_republic_democracy(self.cur_player['government']) and not liberty_flag)

    def is_republic_democracy(self, gov_id):
        return self.rule_ctrl.governments[gov_id]['rule_name'] in ['Republic', 'Democracy']

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_cancel_pact,
                  "other_player_id": self.counterpart["playerno"],
                  "clause": self.diplstates[self.counterpart['playerno']]}

        self.wait_for_pid = (59, (self.cur_player['playerno'], self.counterpart["playerno"]))
        return packet


class StopNegotiate(StartNegotiate):
    action_key = "stop_negotiation"

    def is_action_valid(self):
        return self.counterpart['playerno'] in self.diplomacy_clause_map.keys()

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

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart, diplomacy_clause_map, contact_turns_left):
        super().__init__()
        self.clause_type = clause_type
        self.value = value
        self.counter_id = counter_id
        self.cur_player = cur_player
        self.counterpart = counterpart
        self.giver = cur_player['playerno']
        self.receiver = counterpart['playerno']

        self.diplomacy_clause_map = diplomacy_clause_map
        self.contact_turns_left = contact_turns_left
        self.start_meeting = None

        self.action_key += "_%s_%i_%i_%i" % (player_const.CLAUSE_TXT[clause_type], value, self.giver, self.receiver)

    def is_action_valid(self):
        if self.already_on_meeting():
            return self.clause_exists()
        return False

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_remove_clause_req,
                  "counterpart": self.counter_id,
                  "giver": self.giver,
                  "type": self.clause_type,
                  "value": self.value}
        self.wait_for_pid = (102, self.counter_id)
        return packet

    def already_on_meeting(self):
        return self.counter_id in self.diplomacy_clause_map.keys()

    def clause_exists(self):
        clauses = self.diplomacy_clause_map[self.counter_id]
        for clause in clauses:
            if clause['giver'] == self.giver and clause['type'] == self.clause_type and clause['value'] == self.value:
                return True
        return False


class AddClause(RemoveClause):
    action_key = "add_clause"

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart, diplomacy_clause_map,
                 contact_turns_left, ws_client, diplstates, others_diplstates):
        super().__init__(clause_type, value, counter_id, cur_player, counterpart, diplomacy_clause_map, contact_turns_left)
        self.ws_client = ws_client

        # diplstates contains diplomacy states of my_player
        # others_diplstates contains diplomacy states of all players including my_player
        self.diplstates = diplstates
        self.others_diplstates = others_diplstates
        self.start_meeting = None

    """
    is_clause_valid may return True if the clause already exists in the clause map
    it will be used in AcceptTreaty
    """
    def is_clause_valid(self):

        if self.cur_player['playerno'] == self.counter_id and self.clause_type in CONFLICTING_CLAUSES:
            return False

        ds = self.diplstates[self.counter_id]
        if (ds == player_const.DS_PEACE and self.clause_type in [player_const.CLAUSE_PEACE, player_const.CLAUSE_CEASEFIRE]) or (ds == player_const.DS_ARMISTICE and self.clause_type in [player_const.CLAUSE_PEACE, player_const.CLAUSE_CEASEFIRE]) or (ds == player_const.DS_ALLIANCE and self.clause_type in [player_const.CLAUSE_ALLIANCE, player_const.CLAUSE_PEACE, player_const.CLAUSE_CEASEFIRE]) or (ds == player_const.DS_CEASEFIRE and self.clause_type == player_const.CLAUSE_CEASEFIRE):
            fc_logger.debug(f'we already have this diplomatic state: {self.clause_type}')
            return False

        if (self.clause_type == player_const.CLAUSE_EMBASSY and
                self.counterpart['real_embassy'][self.cur_player['playerno']]):
            fc_logger.debug('Receiver already has embassy of the giver')
            return False

        if self.clause_type == player_const.CLAUSE_ALLIANCE:

            for p in self.others_diplstates[self.cur_player['playerno']]:
                if p == self.counter_id:
                    continue
                if self.war_alliance_conflict_exist(self.cur_player['playerno'], self.counter_id, p):
                    return False

        return True

    def is_action_valid(self):
        if not self.is_clause_valid():
            return False
        return self.can_add_current_clause()

    def can_start_a_meeting(self):
        if self.cur_player['playerno'] == self.counter_id:
            self.start_meeting = StartNegotiate(self.diplomacy_clause_map,
                                                self.contact_turns_left, self.counterpart, self.cur_player)
        else:
            self.start_meeting = StartNegotiate(self.diplomacy_clause_map,
                                                self.contact_turns_left, self.cur_player, self.counterpart)

        return self.start_meeting.is_action_valid()

    def can_add_current_clause(self):
        if self.already_on_meeting():
            return not self.clause_exists()
        else:
            return self.can_start_a_meeting()

    def war_alliance_conflict_exist(self, plr_1, plr_2, p):
        if plr_1 in self.others_diplstates and plr_2 in self.others_diplstates and p in self.others_diplstates[plr_1] and p in self.others_diplstates[plr_2]:
            if self.others_diplstates[plr_1][p] == player_const.DS_WAR and self.others_diplstates[plr_2][
                    p] == player_const.DS_ALLIANCE:
                return True
            if self.others_diplstates[plr_1][p] == player_const.DS_ALLIANCE and self.others_diplstates[plr_2][
                    p] == player_const.DS_WAR:
                return True
        if p in self.others_diplstates and plr_1 in self.others_diplstates[p] and plr_2 in self.others_diplstates[p]:
            if self.others_diplstates[p][plr_1] == player_const.DS_WAR and self.others_diplstates[p][
                    plr_2] == player_const.DS_ALLIANCE:
                return True
            if self.others_diplstates[p][plr_2] == player_const.DS_ALLIANCE and self.others_diplstates[p][
                    plr_2] == player_const.DS_WAR:
                return True
        return False

    def remove_conflicting_clause(self):
        """ consistent with handle_diplomacy_create_clause """

        if self.clause_type in CONFLICTING_CLAUSES or self.clause_type == player_const.CLAUSE_GOLD:
            clauses = self.diplomacy_clause_map[self.counter_id]

            rem_clause = None
            for clause in clauses:

                """ clause in CONFLICTING_CLAUSES does not have direction thus there can only be one clause of this kind """
                if self.clause_type in CONFLICTING_CLAUSES and clause['type'] in CONFLICTING_CLAUSES:
                    if clause['giver'] == self.cur_player['playerno']:
                        rem_clause = RemoveClause(clause['type'], clause['value'], self.counter_id, self.cur_player, self.counterpart, self.diplomacy_clause_map, self.contact_turns_left)
                    else:
                        rem_clause = RemoveClause(clause['type'], clause['value'], self.counter_id, self.counterpart, self.cur_player, self.diplomacy_clause_map, self.contact_turns_left)

                """ clause of CLAUSE_GOLD has direction thus there can be two clauses of this kind respectively corresponding to cur_player --> counterpart and counterpart --> cur_player"""

                if self.clause_type == player_const.CLAUSE_GOLD and clause['type'] == player_const.CLAUSE_GOLD and clause['giver'] ==  self.cur_player['playerno']:
                    rem_clause = RemoveClause(clause['type'], clause['value'], self.counter_id, self.cur_player, self.counterpart, self.diplomacy_clause_map, self.contact_turns_left)

                if rem_clause is not None and rem_clause.is_action_valid():
                    rem_clause.trigger_action(self.ws_client)
                    break

    def _action_packet(self):
        if self.already_on_meeting():
            self.remove_conflicting_clause()
        else:
            self.start_meeting.trigger_action(self.ws_client)

        packet = {"pid": packet_diplomacy_create_clause_req,
                  "counterpart": self.counter_id,
                  "giver": self.giver,
                  "type": self.clause_type,
                  "value": self.value}
        self.wait_for_pid = (100, self.counter_id)
        return packet


class AddTradeTechClause(AddClause):
    action_key = "trade_tech_clause"

    def is_clause_valid(self):
        # cannot know what techs player counter_id has without an embassy
        if self.cur_player['playerno'] == self.counter_id:
            if not self.counterpart['real_embassy'][self.counter_id]:
                return False

        if not is_tech_known(self.cur_player, self.value):
            return False

        if player_invention_state(self.counterpart, self.value) not in [tech_const.TECH_UNKNOWN,
                                                                        tech_const.TECH_PREREQS_KNOWN]:
            return False

        return True


class AddTradeGoldClause(AddClause):
    action_key = "trade_gold_clause"

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart, diplomacy_clause_map,
                 contact_turns_left, ws_client, diplstates, others_diplstates, players):
        super().__init__(clause_type, value, counter_id, cur_player, counterpart,
                         diplomacy_clause_map, contact_turns_left, ws_client, diplstates, others_diplstates)

        self.players = players

    def is_clause_valid(self):
        if self.value > self.players[self.giver]['gold']:
            return False

        return True


class AddTradeCityClause(AddClause):
    action_key = "trade_city_clause"

    def __init__(self, clause_type, value, counter_id, cur_player, counterpart, diplomacy_clause_map,
                 contact_turns_left, ws_client, diplstates, others_diplstates, city_ctrl):
        super().__init__(clause_type, value, counter_id, cur_player, counterpart,
                         diplomacy_clause_map, contact_turns_left, ws_client, diplstates, others_diplstates)

        self.city_ctrl = city_ctrl

    def is_clause_valid(self):
        if self.value not in self.city_ctrl.cities:
            return False

        # city has Palace --> Capital city -- > cannot trade
        if self.city_ctrl.cities[self.value]['improvements'][21] or self.city_ctrl.cities[self.value]['owner'] != self.giver:
            return False

        return True


class AcceptTreaty(StartNegotiate):
    action_key = "accept_treaty"

    def __init__(self,diplomacy_clause_map, contact_turns_left, cur_player, counterpart, ws_client, diplstates, others_diplstates, players, city_ctrl):
        super().__init__(diplomacy_clause_map, contact_turns_left, cur_player, counterpart)
        self.ws_client = ws_client
        self.diplstates = diplstates
        self.others_diplstates = others_diplstates
        self.players = players
        self.city_ctrl = city_ctrl

    """ 
    we do not adopt action classes in _action_dict to call is_action_valid but initializing new ones
    it is because we mask some actions in the env
    thus for a loaded game or when playing with human players
    actions in _action_dict cannot handle some clauses in a clause map 
    which have not been masked for saved games or human players
    """
    def is_action_valid(self):
        if not self.counterpart['playerno'] in self.diplomacy_clause_map.keys():
            return False

        clauses = self.diplomacy_clause_map[self.counterpart['playerno']]
        for clause in clauses:
            if clause['giver'] == self.cur_player['playerno']:
                if not self.is_existing_clause_valid(self.counterpart['playerno'], self.cur_player, self.counterpart, clause):
                    return False
            else:
                if not self.is_existing_clause_valid(self.counterpart['playerno'], self.counterpart, self.cur_player, clause):
                    return False

        return True

    def is_existing_clause_valid(self, counter_id, cur_player, counterpart, clause):
        if clause['type'] == player_const.CLAUSE_ADVANCE:
            current_clause = AddTradeTechClause(clause['type'], clause['value'], counter_id,
                                                cur_player, counterpart, self.diplomacy_clause_map,
                                                self.contact_turns_left, self.ws_client, self.diplstates,
                                                self.others_diplstates)
        elif clause['type'] == player_const.CLAUSE_GOLD:
            current_clause = AddTradeGoldClause(clause['type'], clause['value'], counter_id,
                                                cur_player, counterpart, self.diplomacy_clause_map,
                                                self.contact_turns_left, self.ws_client, self.diplstates,
                                                self.others_diplstates, self.players)
        elif clause['type'] == player_const.CLAUSE_CITY:
            current_clause = AddTradeCityClause(clause['type'], clause['value'], counter_id,
                                                cur_player, counterpart, self.diplomacy_clause_map,
                                                self.contact_turns_left, self.ws_client, self.diplstates,
                                                self.others_diplstates, self.city_ctrl)
        else:
            current_clause = AddClause(clause['type'], 1, counter_id, cur_player,
                                       counterpart, self.diplomacy_clause_map, self.contact_turns_left,
                                       self.ws_client, self.diplstates, self.others_diplstates)

        return current_clause.is_clause_valid()

    def _action_packet(self):
        packet = {"pid": packet_diplomacy_accept_treaty_req,
                  "counterpart": self.counterpart["playerno"]}
        self.wait_for_pid = (104, self.counterpart["playerno"])
        return packet


# TODO: Check if necessary to add this action to action_dict of diplomacy
class IgnoreDiplomacy(Action):
    action_key = 'ignore_diplomacy_request'

    def __init__(self, counter_id, ws_client):
        super().__init__()
        self.counter_id = counter_id
        self.ws_client = ws_client

    def is_action_valid(self):
        """ always valid """
        return True

    def _action_packet(self):
        return 'ignore_diplomacy_request'

    def trigger_action(self, ws_client):
        self.ws_client.send_message(f"Ignore diplomacy request of player {self.counter_id}")


def has_statue_of_liberty(cities, cur_player):
    for city_id in cities:
        pcity = cities[city_id]

        if pcity['owner'] == cur_player['playerno'] and 'improvements' in pcity and pcity['improvements'][63]:
            return True

    return False


