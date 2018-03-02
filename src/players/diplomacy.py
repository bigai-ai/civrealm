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

CLAUSE_ADVANCE = 0
CLAUSE_GOLD = 1
CLAUSE_MAP = 2
CLAUSE_SEAMAP = 3
CLAUSE_CITY = 4
CLAUSE_CEASEFIRE = 5
CLAUSE_PEACE = 6
CLAUSE_ALLIANCE = 7
CLAUSE_VISION = 8
CLAUSE_EMBASSY = 9

DS_ARMISTICE = 0
DS_WAR = 1
DS_CEASEFIRE = 2
DS_PEACE = 3
DS_ALLIANCE = 4
DS_NO_CONTACT = 5
DS_TEAM = 6
DS_LAST = 7

from connectivity.Basehandler import CivEvtHandler
from players.player_actions import AddClause, AddTradeTechClause, StartNegotiate,\
    StopNegotiate, AcceptTreaty, CancelClause


class DiplomacyCtrl(CivEvtHandler):
    def __init__(self, ws_client, clstate, ruleset, dipl_evaluator):
        CivEvtHandler.__init__(self, ws_client)
        self.diplstates = {}
        self.diplomacy_request_queue = []
        self.diplomacy_clause_map = {}
        self.active_diplomacy_meeting_id = None
        self.ruleset = ruleset
        self.clstate = clstate
        self.dipl_evaluator = dipl_evaluator

        self.register_handler(59, "handle_player_diplstate")
        self.register_handler(96, "handle_diplomacy_init_meeting")
        self.register_handler(98, "handle_diplomacy_cancel_meeting")
        self.register_handler(100, "handle_diplomacy_create_clause")
        self.register_handler(102, "handle_diplomacy_remove_clause")
        self.register_handler(104, "handle_diplomacy_accept_treaty")

    def get_current_state(self, counterpart):
        player_id = counterpart["playerno"]
        return {"diplstates%i" % player_id: self.diplstates[player_id]}
        """
        for counterpart in self.players:
            if counterpart == cur_player:
                state.update(self.dipl_ctrl.get_current_state(counterpart))

        state["shared_vision"] = 0
        
        if (pplayer['diplstates'] !== undefined) {
            pplayer['diplstates'].forEach(function (st, i) {
              if (st['state'] !== DS_NO_CONTACT && i !== pplayer['playerno']) {
                var dplst = intel_data['dipl'][st['state']]
                if (dplst === undefined) {
                  dplst = {
                    state: get_diplstate_text(st['state']),
                    nations: []
                  }
                  intel_data['dipl'][st['state']] = dplst
                }
                dplst['nations'].append(nations[players[i]['nation']]['adjective'])
              }
            })
          }

        if self.clstate.can_client_control():
            if not self.player_is_myself(player_id) and diplstates[player_id] != None:
                state["dipl_state"] = get_diplstate_text(diplstates[player_id])

            if pplayer['gives_shared_vision'].isSet(cur_player['playerno']):
                state["shared_vision"] += 1 # "To you"
            if cur_player['gives_shared_vision'].isSet(player_id):
                state["shared_vision"] += 2 # "To Them
        """

    def get_counterpart_options(self, counterpart):
        cur_player = self.clstate.cur_player()
        dipl_actions = [StartNegotiate(self.ws_client, counterpart),
                        StopNegotiate(self.ws_client, counterpart),
                        AcceptTreaty(self.ws_client, counterpart)]

        dipl_actions.extend(self.get_clause_options(cur_player, counterpart))
        dipl_actions.extend(self.get_clause_options(counterpart, cur_player))
        return dict([(act.action_key, act) for act in dipl_actions])

    def get_clause_options(self, giver, taker):
        cur_p = self.clstate.cur_player()
        base_clauses = [CLAUSE_MAP, CLAUSE_SEAMAP, CLAUSE_VISION, CLAUSE_EMBASSY,
                        CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]

        dipl_actions  = [AddClause(self.ws_client, ctype, 1, giver, taker, cur_p)
                         for ctype in base_clauses]

        dipl_actions.extend([CancelClause(self.ws_client, ctype, 1, giver, taker, cur_p)
                             for ctype in [CLAUSE_CEASEFIRE, CLAUSE_PEACE, CLAUSE_ALLIANCE]])

        dipl_actions.extend([AddTradeTechClause(self.ws_client, CLAUSE_ADVANCE, tech_id,
                                                giver, taker, cur_p, self.ruleset)
                                                for tech_id in self.ruleset.techs])

        return dipl_actions

        """
        if self.ruleset.game_info["trading_city"]:
            for city_id in cities:
                pcity = cities[city_id]
                if city_owner(pcity) == giver and not does_city_have_improvement(pcity, "Palace"):
                    all_clauses.append({"type": CLAUSE_CITY, "value": city_id})

        if self.ruleset.game_info["trading_gold"]:
            if giver == self.player_ctrl.clstate.cur_player()['playerno']:
                all_clauses.append({"type": CLAUSE_GOLD, "value": ("#self_gold").val(value)})
            else:
                all_clauses.append({"type": CLAUSE_GOLD, "value": ("#counterpart_gold").val(value)})
        """

    def handle_player_diplstate(self, packet):
        if not self.clstate.is_playing():
            return
        cur_playerno = self.clstate.cur_player()["playerno"]
        opposite_player = None
        if packet['plr1'] == cur_playerno:
            opposite_player = 'plr2'
        elif packet['plr2'] == cur_playerno:
            opposite_player = 'plr1'
        else:
            return

        self.diplstates[packet[opposite_player]] = packet['type']

        """
        if packet['type'] == DS_WAR and self.check_not_dipl_states(packet[opposite_player]):
            self.dipl_evaluator.alert_war(packet[opposite_player])
        """
        """
        // TODO: remove current diplstates (after moving all users to the new one),
        //       or just make it a reference to players[me].diplstates
        //
        // There's no need to set players[packet.plr2].diplstates, as there'll be
        // a packet for that.  In fact, there's a packet for each of (p1,x) and (p2,x)
        // when the state changes between p1 and p2, and for all pairs of players
        // when a turn begins
        """
        """
        player1 = self.player_ctrl.players[packet['plr1']]
        if not "diplstates" in player1.keys():
            player1["diplstates"] = [{} for _ in self.player_ctrl.players]

        player1["diplstates"][packet['plr2']] = {
                            "state": packet['type'],
                            "turns_left": packet['turns_left'],
                            "contact_turns_left": packet['contact_turns_left']
                            }
        """

    def handle_diplomacy_init_meeting(self, packet):
        if not (packet['counterpart'] in self.diplomacy_request_queue):
            self.diplomacy_request_queue.append(packet['counterpart'])

        self.diplomacy_clause_map[packet['counterpart']] = []
        self.refresh_diplomacy_request_queue()

    def handle_diplomacy_cancel_meeting(self, packet):
        counterpart = packet['counterpart']

        if self.active_diplomacy_meeting_id == counterpart:
            self.active_diplomacy_meeting_id = None

        if counterpart in self.diplomacy_request_queue:
            del self.diplomacy_request_queue[self.diplomacy_request_queue.index(counterpart)]
        #setTimeout(refresh_diplomacy_request_queue, 1000)

    def refresh_diplomacy_request_queue(self):
        if self.diplomacy_request_queue != []:
            next = self.diplomacy_request_queue[0]
            if next != None and next != self.active_diplomacy_meeting_id:
                self.active_diplomacy_meeting_id = next

    def handle_diplomacy_create_clause(self, packet):
        if(self.diplomacy_clause_map[packet['counterpart']] == None):
            self.diplomacy_clause_map[packet['counterpart']] = []
        self.diplomacy_clause_map[packet['counterpart']].append(packet)

    def handle_diplomacy_remove_clause(self, packet):
        clause_list = self.diplomacy_clause_map[packet['counterpart']]
        for i, check_clause in enumerate(clause_list):
            if (packet['counterpart'] == check_clause['counterpart'] and
                packet['giver'] == check_clause['giver'] and
                packet['type'] == check_clause['type']):

                del clause_list[i]
                break

    def handle_diplomacy_accept_treaty(self, packet):
        counterpart = packet['counterpart']
        myself_accepted = packet['I_accepted']
        other_accepted = packet['other_accepted']

        if not self.active_diplomacy_meeting_id == counterpart and myself_accepted and other_accepted:
            if counterpart in self.diplomacy_request_queue:
                del self.diplomacy_request_queue[self.diplomacy_request_queue.index(counterpart)]
            elif self.active_diplomacy_meeting_id == counterpart:
                self.dipl_evaluator.evaluate_clauses(self.diplomacy_clause_map[counterpart], counterpart,
                                                     myself_accepted, other_accepted)

        self.refresh_diplomacy_request_queue()
        #setTimeout(refresh_diplomacy_request_queue, 1000)

    def check_not_dipl_states(self, player_id, check_list=[DS_WAR, DS_NO_CONTACT]):
        if player_id in self.diplstates:
            if not (self.diplstates[player_id] in check_list):
                return True
        else:
            return False

    def check_in_dipl_states(self, player_id, check_list=[DS_ALLIANCE, DS_TEAM]):
        if player_id in self.diplstates:
            if self.diplstates[player_id] in check_list:
                return True
        else:
            return False

    @staticmethod
    def get_diplstate_text(state_id):
        if DS_ARMISTICE == state_id:
            return "Armistice"
        elif (DS_WAR == state_id):
            return "War"
        elif (DS_CEASEFIRE == state_id):
            return "Ceasefire"
        elif (DS_PEACE == state_id):
            return "Peace"
        elif (DS_ALLIANCE == state_id):
            return "Alliance"
        elif (DS_NO_CONTACT == state_id):
            return "No contact"
        elif (DS_TEAM == state_id):
            return "Team"
        else:
            return "Unknown state"

    """
    def evaluate_clauses(self):
        def eval_clause(counterpart, giver, ctype, value):
            pass
        if self.active_diplomacy_meeting_id != None:
            clauses = self.diplomacy_clause_map[self.active_diplomacy_meeting_id]
            for cid, clause in enumerate(clauses):
                eval_clause(clause["counterpart"], clause["giver"],
                            clause["type"], clause["value"])

    def meeting_gold_change_req(self, giver, gold):
        #Request update of gold clause
        clauses = self.diplomacy_clause_map[self.active_diplomacy_meeting_id]
        if clauses != None:
            for cid, clause in enumerate(clauses):
                if clause['giver'] == giver and clause['type'] == CLAUSE_GOLD:
                    if clause['value'] == gold:
                        return
                    self.remove_clause_req(cid)

        if gold != 0:
            packet = {"pid" : packet_diplomacy_create_clause_req,
                      "counterpart" : self.active_diplomacy_meeting_id,
                      "giver" : giver,
                      "type" : CLAUSE_GOLD,
                      "value" : gold}
            self.ws_client.send_request(packet)
    """
