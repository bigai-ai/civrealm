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
from BitVector import BitVector
from utils.utility import byte_to_bit_array

from connectivity.client_state import C_S_PREPARING
from connectivity.Basehandler import CivPropController

from players.diplomacy import DS_NO_CONTACT, DS_CEASEFIRE, DS_PEACE, DS_ARMISTICE
from players.player_state import PlayerState, PLRF_AI
from players.player_actions import PlayerOptions

from city.city_state import CityState
from research.tech_helpers import TECH_KNOWN

class PlayerCtrl(CivPropController):
    def __init__(self, ws_client, clstate, rule_ctrl, dipl_ctrl):
        CivPropController.__init__(self, ws_client)
        self.register_handler(50, "handle_player_remove")
        self.register_handler(51, "handle_player_info")
        self.register_handler(58, "handle_player_attribute_chunk")
        self.register_handler(60, "handle_research_info")

        self.clstate = clstate
        self.rule_ctrl = rule_ctrl
        self.dipl_ctrl = dipl_ctrl
        self.players = {}
        self.research_data = {}
        self.endgame_player_info = []

        self.prop_state = PlayerState(rule_ctrl, self, clstate, dipl_ctrl.diplstates, self.players)
        self.prop_actions = PlayerOptions(ws_client, rule_ctrl, self.players, clstate)

    @staticmethod
    def get_player_connection_status(pplayer):
        """Status text for short connection info"""
        if pplayer is None:
            return ""

        if not pplayer['is_alive']:
            return "dead"

        if pplayer['phase_done']:
            return "done moving"
        elif pplayer['nturns_idle'] > 1:
            return pplayer['nturns_idle'] + " turns idling"
        else:
            return "moving"

    def player_is_myself(self, player_id):
        cur_player = self.clstate.cur_player()
        if cur_player != None:
            return player_id == cur_player["playerno"]
        else:
            return False

    def player_not_myself(self, player_id):
        return not self.player_is_myself(player_id)

    def players_alive(self, pplayer):
        cur_player = self.clstate.cur_player()
        if cur_player != None:
            return pplayer['is_alive'] and cur_player['is_alive']
        else:
            return False

    def players_not_same_team(self, pplayer):
        cur_player = self.clstate.cur_player()
        if cur_player != None:
            return pplayer['team'] != cur_player['team']
        else:
            return False
        #self_upkeep = self.player_ctrl.cur_player.tech_upkeep

    def is_player_ready(self):
        player_num = self.clstate.player_num()
        return player_num != None and player_num in self.players.keys() and self.players[player_num]["is_ready"]

    def get_player(self, player_num):
        return self.players[player_num]

    def city_owner(self, pcity):
        return self.players[CityState.city_owner_player_id(pcity)]

    def valid_player_by_number(self, playerno):
        #TODO:
        #pslot = self.player_slot_by_number(player_id)
        #if (not self.player_slot_is_used(pslot)):
        #    return None
        if playerno in self.players:
            return self.players[playerno]
        else:
            return None

    def player_by_number(self, playerno):
        return self.players[playerno]

    def player_by_name(self, pname):
        for player_id in self.players:
            pplayer = self.players[player_id]
            if pname == pplayer['name']:
                return pplayer
        else:
            return None

    def player_by_full_username(self, pname):
        ainame = ""
        if pname.startswith("AI "):
            ainame = pname[3:]
        else:
            ainame = pname

        for player_id in self.players:
            pplayer = self.players[player_id]
            if pplayer['flags'].isSet(PLRF_AI):
                if ainame == pplayer['name']:
                    return pplayer
            elif pname == pplayer['username']:
                return pplayer
        return None

    @staticmethod
    def player_index(pplayer):
        """
            Return the player index.
            Currently same as player_number(), paired with player_count()
            indicates use as an array index.
        """
        return PlayerCtrl.player_number(pplayer)

    @staticmethod
    def player_number(player):
        """Return the player index/number/id."""
        return player['playerno']

    def research_get(self, pplayer):
        """Returns the research object related to the given player."""
        if pplayer is None:
            return None

        return self.research_data[pplayer['playerno']]

    def get_nation_options(self, selected_player):
        player_id = selected_player
        pplayer = self.players[selected_player]

        if pplayer is None:
            return

        selected_myself = self.player_is_myself(self)
        both_alive_and_different = self.player_not_myself(self) and self.players_alive(pplayer)

        player_options = []

        if not self.clstate.client_is_observer() and both_alive_and_different:
            if self.dipl_ctrl.check_not_dipl_states(player_id, [DS_NO_CONTACT]):
                player_options.append("meet_player")

            if self.players_not_same_team(pplayer) and self.dipl_ctrl.check_not_dipl_states(player_id):
                player_options.append("cancel_treaty")

        if pplayer['flags'].isSet(PLRF_AI) or selected_myself:
            player_options.append("send_msg")

        if self.clstate.can_client_control():
            if not selected_myself:
                if self.dipl_ctrl.check_in_dipl_states(player_id, [DS_CEASEFIRE, DS_ARMISTICE, DS_PEACE]):
                    player_options.append("declare_war")
                else:
                    player_options.append("cancel_treaty")

            if both_alive_and_different and self.players_not_same_team(pplayer) and \
                self.clstate.cur_player()['gives_shared_vision'].isSet(player_id):
                player_options.append("withdraw_vision")

        if self.clstate.client_is_observer() or (both_alive_and_different and
                                                  self.dipl_ctrl.check_not_dipl_states(player_id, [DS_NO_CONTACT])):
            player_options.append("intl_report")

        player_options.append("toggle_ai")

    def handle_endgame_player(self, packet):
        self.endgame_player_info.append(packet)

    """
    def alert_war(self, player_no):
        return

        pplayer = self.players[player_no]

        message_log.update({event: E_DIPLOMACY,
                            message: "War: You are now at war with the "
                            + nations[pplayer['nation']]['adjective']
                                + " leader " + pplayer['name'] + "!"
                          })
    """

    
    def pregame_getplayer_options(self):
        """Shows the pick nation dialog. This can be called multiple times, but will
          only call update_player_info_pregame_real once in a short timespan."""

        if C_S_PREPARING == self.clstate.client_state():

            player_list = []
            for pid in self.players:
                player = self.players[pid]
                if player is None:
                    continue

                player_item = {"name": player['name'], "id": pid, "nation": player['nation'],
                               "playerid": player["playerno"]}
                if player["is_ready"]:
                    player_item["status"] = "player_ready"
                else:
                    try:
                        player['name'].index("AI")
                        player["status"] = "AI ready"
                    except:
                        player["status"] = "player_not_ready"
                player_list.append(player_item)

            play_options = ["pick_nation", "observe", "take",
                            "aitoggle", "novice", "easy", "normal", "hard"]

            return play_options, player_list
        else:
            return [], []

    def handle_research_info(self, packet):
        old_inventions = None
        if packet['id'] in self.research_data:
            old_inventions = self.research_data[packet['id']]['inventions']

        self.research_data[packet['id']] = packet

        pplayer = self.players[packet['id']]
        pplayer.update(packet)
        del pplayer['id']

        if (not self.clstate.client_is_observer() and old_inventions != None and
            self.clstate.is_playing() and self.clstate.cur_player()['playerno'] == packet['id']):
            for i, invention in enumerate(packet['inventions']):
                if invention != old_inventions[i] and invention == TECH_KNOWN:
                    #queue_tech_gained_dialog(i)
                    break

    def handle_player_info(self, packet):
        """ Interpret player flags."""
        packet['flags'] = BitVector(bitlist = byte_to_bit_array(packet['flags']))
        packet['gives_shared_vision'] = BitVector(bitlist = byte_to_bit_array(packet['gives_shared_vision']))
        playerno = packet["playerno"]
        if not playerno in self.players.keys() or self.players[playerno] is None:
            self.players[playerno] = packet
        else:
            self.players[playerno].update(packet)

        if self.clstate.is_playing():
            if packet['playerno'] == self.clstate.cur_player()['playerno']:
                self.clstate.change_player(self.players[packet['playerno']])
                #update_game_status_panel()
                #update_net_income()
        #update_player_info_pregame()
        #update_tech_screen()

    def handle_player_remove(self, packet):
        del self.players[packet['playerno']]
        #update_player_info_pregame()

    def handle_player_attribute_chunk(self, packet):
        """
          /* The attribute block of the player structure is an area of Freeciv
           * server memory that the client controls. The server will store it to
           * savegames, send it when the client requests a copy and change it on
           * the client's request. The server has no idea about its content. This
           * is a chunk of it.
           *
           * The C clients can use the attribute block to store key-value pair
           * attributes for the object types city, player, tile and unit. The
           * format the they use to encode this data can be found in Freeciv's
           * client/attribute.c.
           *
           * The C clients uses it to store parameters of cities for the (client
           * side) CMA agent. */

          /* TODO: Find out if putting something inside savegames is needed. If it
           * is: decide if compatibility with the format of the Freeciv C clients
           * is needed and implement the result of the decision. */
        """
        pass

    """
    def show_endgame_dialog(self):
        #Shows the endgame dialog
        title = "Final Report: The Greatest Civilizations in the world!"
        message = ""

        for i, info in enumerate(self.endgame_player_info):
            pplayer = players[info['player_id']]
            nation_adj = nations[pplayer['nation']]['adjective']
            message += (i+1) + ": The " + nation_adj + " ruler " + pplayer['name'] + " scored " + info['score'] + " points" + "<br>"
    """
