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

import time
from math import ceil, floor
from freecivbot.connectivity.base_controller import CivPropController
from freecivbot.utils.fc_types import GUI_WEB, packet_client_info, packet_player_ready,\
    packet_conn_pong
from freecivbot.utils.base_action import NoActions
from freecivbot.utils.base_state import EmptyState

from freecivbot.utils.freeciv_logging import logger

C_S_INITIAL = 0  # /* Client boot, only used once on program start. */
C_S_PREPARING = 1  # /* Main menu (disconnected) and connected in pregame. */
C_S_RUNNING = 2  # /* Connected with game in progress. */
C_S_OVER = 3  # /* Connected with game over. */


class ClientState(CivPropController):
    def __init__(self, ws_client, rule_ctrl):
        CivPropController.__init__(self, ws_client)
        self.rule_ctrl = rule_ctrl
        self.civclient_state = C_S_INITIAL
        self.connect_error = False
        self.oldstate = -1
        self.prop_actions = NoActions(ws_client)
        self.prop_state = EmptyState()

        self.client = {}
        self.client["conn"] = {}
        self.client_frozen = False

        self.connections = {}
        self.conn_ping_info = {}
        self.debug_active = False
        self.debug_ping_list = []
        self.ping_last = None

        self.observing = False
        self.metamessage_changed = False

        self.phase_start_time = 0
        self.last_turn_change_time = 0
        self.turn_change_elapsed = 0
        self.seconds_to_phasedone = 0
        self.seconds_to_phasedone_sync = 0

        self.register_handler(0, "handle_processing_started")
        self.register_handler(1, "handle_processing_finished")

        self.register_handler(5, "handle_server_join_reply")
        self.register_handler(6, "handle_authentication_req")
        self.register_handler(8, "handle_server_shutdown")
        self.register_handler(27, "handle_connect_msg")
        self.register_handler(88, "handle_conn_ping")
        self.register_handler(244, "handle_timeout_info")

        self.register_handler(130, "handle_freeze_client")
        self.register_handler(131, "handle_thaw_client")

        self.register_handler(116, "handle_conn_ping_info")

    def init_state(self, packet):
        self.client["conn"] = packet

    def has_id(self, cid):
        return cid == self.client["conn"]["id"]

    def is_playing(self):
        return "playing" in self.client["conn"].keys()

    def cur_player(self):
        if self.is_playing():
            return self.client["conn"]["playing"]

    def change_player(self, pplayer):
        self.client["conn"]["playing"] = pplayer

    def player_num(self):
        if "player_num" in self.client["conn"]:
            return self.client["conn"]['player_num']
        else:
            return None

    def handle_timeout_info(self, packet):
        self.last_turn_change_time = ceil(packet['last_turn_change_time'])
        self.seconds_to_phasedone = floor(packet['seconds_to_phasedone'])
        self.seconds_to_phasedone_sync = time.time()

    def handle_connect_msg(self, packet):
        logger.info(packet)
        logger.info("\r\n")

    def handle_authentication_req(self, packet):
        raise Exception("Not implemented yet")
        # show_auth_dialog(packet)

    def handle_server_shutdown(self, packet):
        # /* TODO: implement*/
        pass

    def handle_conn_ping_info(self, packet):
        if self.debug_active:
            self.conn_ping_info = packet
            self.debug_ping_list.append(packet['ping_time'][0] * 1000)

    def handle_processing_started(self, packet):
        self.client_frozen = True

    def handle_processing_finished(self, packet):
        self.client_frozen = False

    def handle_freeze_client(self, packet):
        self.client_frozen = True

    def handle_thaw_client(self, packet):
        self.client_frozen = False

    def send_client_info(self):
        client_info = {
            "pid": packet_client_info,
            "gui": GUI_WEB,
            "emerg_version": 0,
            "distribution": ""
        }

        self.ws_client.send_request(client_info)

    def handle_server_join_reply(self, packet):
        """
            After we send a join packet to the server we receive a reply.  This
            function handles the reply.  100% Complete.
        """
        if packet['you_can_join']:
            self.client["conn"]["established"] = True
            self.client["conn"]["id"] = packet['conn_id']

            self.set_client_state(C_S_PREPARING)
            self.send_client_info()

            """
            TODO:
             #pregame.pregame_start_game(self)
            if self.autostart:
                pregame.pregame_start_game(self)
            elif self.observing:
                self.request_observe_game()*/
            """

    def update_client_state(self, value):
        self.set_client_state(value)

    def set_client_state(self, newstate):
        """Sets the client state (initial, pre, running, over etc)."""
        self.connect_error = (C_S_PREPARING == self.civclient_state) and (C_S_PREPARING == newstate)
        self.oldstate = self.civclient_state

        if self.civclient_state != newstate:
            self.civclient_state = newstate

        if self.civclient_state == C_S_RUNNING:
            pass
            # clear_chatbox()
            # self.show_new_game_message()
            # self.update_metamessage_on_gamestart()
        elif self.civclient_state == C_S_OVER:
            pass
            # show_endgame_dialog()
        elif self.civclient_state == C_S_PREPARING:
            pass
        else:
            pass

    def client_state(self):
        return self.civclient_state

    def can_client_control(self):
        """Returns TRUE if the client can control the player."""
        return "playing" in self.client["conn"] and not self.client_is_observer()

    def can_client_issue_orders(self):
        """Returns TRUE if the client can issue orders (giving unit commands, etc)."""
        return self.can_client_control() and C_S_RUNNING == self.client_state()

    def client_is_observer(self):
        """Webclient does have observer support."""
        return self.client["conn"]['observer'] or self.observing

    def find_conn_by_id(self, cid):
        if cid in self.connections:
            return self.connections[cid]
        else:
            return None

    def client_remove_cli_conn(self, connection):
        del self.connections[connection['id']]

    def conn_list_append(self, connection):
        self.connections[connection['id']] = connection

    def show_new_game_message(self):
        """Intro message"""
        # clear_chatbox()

        if self.observing:
            return

        if "playing" in self.client["conn"]:
            pplayer = self.client["conn"]["playing"]
            player_nation_text = "Welcome, " + self.client["conn"]["username"] + " ruler of the "
            player_nation_text += self.rule_ctrl.nations[pplayer['nation']]['adjective']
            player_nation_text += " empire."
            logger.info(player_nation_text)
            # message = player_nation_text
            # message_log.update({ "event": E_CONNECTION, "message": message })

    def update_metamessage_on_gamestart(self):
        """Updates message on the metaserver on gamestart."""

        if (not self.observing and not self.metamessage_changed and
                "playing" in self.client["conn"]):
            pplayer = self.client["conn"]["playing"]
            metasuggest = self.client["conn"]["username"] + " ruler of the " + \
                self.rule_ctrl.nations[pplayer['nation']]['adjective'] + "."
            self.ws_client.send_message("/metamessage " + metasuggest)
            # setInterval(update_metamessage_game_running_status, 200000)

    def update_metamessage_game_running_status(self):
        """Updates message on the metaserver during a game."""
        if "playing" in self.client["conn"] and not self.metamessage_changed:
            pplayer = self.client["conn"]["playing"]
            metasuggest = self.rule_ctrl.nations[pplayer['nation']]['adjective'] + " | "
            metasuggest += self.rule_ctrl.governments[pplayer['government']
                                                      ]['name'] if self.rule_ctrl.governments[pplayer['government']] != None else "-"
            metasuggest += " | Score:" + pplayer['score']
            metasuggest += " | Research:" + self.rule_ctrl.techs[pplayer['researching']
                                                                 ]['name'] if self.rule_ctrl.techs[pplayer['researching']] != None else "-"

        self.ws_client.send_message("/metamessage " + metasuggest)

    def request_observe_game(self):
        self.ws_client.send_message("/observe ")

    def surrender_game(self):
        if not self.client_is_observer() and self.ws_client != None and self.ws_client.readyState == 1:
            self.ws_client.send_message("/surrender ")

    def pregame_start_game(self):
        if "player_num" not in self.client['conn']:
            return

        test_packet = {"pid": packet_player_ready, "is_ready": True,
                       "player_no": self.client['conn']['player_num']}
        self.ws_client.send_request(test_packet)

    def observe(self):
        if self.observing:
            self.ws_client.send_message("/detach")
        else:
            self.ws_client.send_message("/observe")

        self.observing = not self.observing

    def take_player(self, player_name):
        self.ws_client.send_message("/take " + player_name)
        self.observing = False

    def aitoggle_player(self, player_name):
        self.ws_client.send_message("/aitoggle " + player_name)
        self.observing = False

    def handle_conn_ping(self, packet):
        self.ping_last = time.time()
        pong_packet = {"pid": packet_conn_pong}
        self.ws_client.send_request(pong_packet)
