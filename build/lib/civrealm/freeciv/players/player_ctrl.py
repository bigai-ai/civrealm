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


from typing import Dict
from BitVector import BitVector
from civrealm.freeciv.utils.utility import byte_to_bit_array


from civrealm.freeciv.connectivity.civ_connection import CivConnection
from civrealm.freeciv.connectivity.client_state import ClientState
from civrealm.freeciv.game.ruleset import RulesetCtrl
from civrealm.freeciv.city.city_ctrl import CityCtrl

from civrealm.freeciv.utils.base_controller import CivPropController

from civrealm.freeciv.players.player_state import PlayerState
from civrealm.freeciv.players.player_actions import PlayerOptions
from civrealm.freeciv.city.city_state import CityState
from civrealm.freeciv.utils.utility import format_hex

from civrealm.freeciv.utils.freeciv_logging import fc_logger

import civrealm.freeciv.players.player_const as player_const
import civrealm.freeciv.tech.tech_const as tech_const
from civrealm.freeciv.connectivity.client_state import C_S_PREPARING


class PlayerCtrl(CivPropController):
    def __init__(
            self, ws_client: CivConnection, clstate: ClientState, city_ctrl: CityCtrl, rule_ctrl: RulesetCtrl):
        super().__init__(ws_client)

        self.clstate = clstate
        self.rule_ctrl = rule_ctrl
        self.city_ctrl = city_ctrl

        self.players: Dict[int, Dict] = {}

        self.research_data = {}
        self.endgame_player_info = []

        self.prop_state = PlayerState(self, rule_ctrl, clstate)
        self.prop_actions = PlayerOptions(ws_client, rule_ctrl, city_ctrl, self.players)

    def register_all_handlers(self):
        self.register_handler(50, "handle_player_remove")
        self.register_handler(51, "handle_player_info")
        self.register_handler(58, "handle_player_attribute_chunk")
        self.register_handler(60, "handle_research_info")
        self.register_handler(259, "handle_web_player_info_addition")

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

    @property
    def my_player_id(self):
        return self.prop_state.my_player_id

    @property
    def my_player(self):
        return self.prop_state.my_player

    def previous_players_finished(self) -> bool:
        # Determine whether other players with a smaller playno have finished. Note that here we assume the host has
        # a smallest playerno so that it always starts its turn first.
        for playerno in self.players:
            if playerno < self.my_player_id and not self.players[playerno]['phase_done']:
                return False
        return True

    def total_players(self):
        return len(self.players)

    def player_is_myself(self, player_id):
        return player_id == self.my_player_id

    def player_not_myself(self, player_id):
        return not self.player_is_myself(player_id)

    def players_alive(self, pplayer):
        return pplayer['is_alive'] and self.my_player['is_alive']

    def players_not_same_team(self, pplayer):
        return pplayer['team'] != self.my_player['team']

    def is_player_ready(self):
        return self.my_player_id is not None and self.my_player_id in self.players.keys() and self.my_player["is_ready"]

    def get_player(self, player_num):
        return self.players[player_num]

    def city_owner(self, pcity):
        return self.players[CityState.city_owner_player_id(pcity)]

    def player_has_wonder(self, playerno, improvement_id):
        """returns true if the given player has the given wonder (improvement)"""
        for city_id in self.city_ctrl.cities:
            pcity = self.city_ctrl.cities[city_id]
            if (self.city_owner(pcity)["playerno"] == playerno
                    and self.rule_ctrl.city_has_building(pcity, improvement_id)):
                return True
        return False

    def valid_player_by_number(self, playerno):
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
        return None

    def player_by_full_username(self, pname):
        ainame = ""
        if pname.startswith("AI "):
            ainame = pname[3:]
        else:
            ainame = pname

        for player_id in self.players:
            pplayer = self.players[player_id]
            if pplayer['flags'][player_const.PLRF_AI]:
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
                    if "AI" in player["name"]:
                        player["status"] = "AI ready"
                    else:
                        player["status"] = "player_not_ready"

                player_list.append(player_item)

            play_options = ["pick_nation", "observe", "take",
                            "aitoggle", "novice", "easy", "normal", "hard"]

            return play_options, player_list
        else:
            return [], []

    def handle_player_info(self, packet):
        """ Interpret player flags."""
        packet['flags'] = BitVector(bitlist=byte_to_bit_array(packet['flags']))
        packet['gives_shared_vision'] = BitVector(bitlist=byte_to_bit_array(packet['gives_shared_vision']))
        packet['gives_shared_tiles'] = BitVector(bitlist=byte_to_bit_array(packet['gives_shared_tiles']))
        playerno = packet["playerno"]
        # Update player information
        if playerno not in self.players.keys() or self.players[playerno] is None:
            self.players[playerno] = packet
        else:
            self.players[playerno].update(packet)

        if self.player_is_myself(playerno):
            pass
            # TODO: check what the following code is doing
            # update_game_status_panel()
            # update_net_income()
        # update_player_info_pregame()
        # update_tech_screen()

        """ tell city_ctrl if tiles are shared between players """
        self.city_ctrl.prop_actions.tiles_shared[packet["playerno"]] = packet['gives_shared_tiles']

    def handle_web_player_info_addition(self, packet):
        # Currently there is only one additional field expected_income、
        if packet['playerno'] in self.players:
            del packet['pid']
            self.players[packet['playerno']].update(packet)

    def handle_research_info(self, packet):
        old_inventions = None
        if packet['id'] in self.research_data:
            old_inventions = self.research_data[packet['id']]['inventions']

        self.research_data[packet['id']] = packet

        # TODO: implement for "team_pooled_research" setting
        if self.rule_ctrl.game_info['team_pooled_research']:
            for player_id in self.players:
                pplayer = self.players[player_id]
                if pplayer['team'] == packet['id']:
                    pplayer.update(packet)
                    del pplayer['id']
        else:
            pplayer = self.players[packet['id']]
            pplayer.update(packet)
            del pplayer['id']

        if not self.clstate.client_is_observer() and old_inventions != None and self.player_is_myself(packet['id']):
            for i, invention in enumerate(packet['inventions']):
                if invention != old_inventions[i] and invention == tech_const.TECH_KNOWN:
                    fc_logger.info(f"Gained new technology: {self.rule_ctrl.techs[i]['name']}")
                    break

    # TODO: Check whether there are other cases that would also lead to player removal, e.g., other players are
    #  conquered.
    def handle_player_remove(self, packet):
        # When we load a game, we will receive player_remove packet. In this case, packet['playerno'] is not in
        # self.players.
        if packet['playerno'] in self.players:
            del self.players[packet['playerno']]
            # update_player_info_pregame()

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

    def get_player_colors(self):
        player_colors = dict()
        for player_id in self.players:
            color_red = self.players[player_id]['color_red']
            color_green = self.players[player_id]['color_green']
            color_blue = self.players[player_id]['color_blue']
            player_colors[player_id] = '#' + format_hex(color_red) + format_hex(color_green) + format_hex(color_blue)
        return player_colors
