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


import time
import hashlib
import urllib
import requests
import random
import os
from math import ceil, floor

from civrealm.freeciv.connectivity.civ_connection import CivConnection
from civrealm.freeciv.game.ruleset import RulesetCtrl

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.utils.fc_types import GUI_WEB, packet_client_info, packet_player_ready,\
    packet_conn_pong
from civrealm.freeciv.utils.base_action import NoActions
from civrealm.freeciv.utils.base_state import EmptyState

from civrealm.freeciv.utils.freeciv_logging import fc_logger, update_logger
from civrealm.configs import fc_args

C_S_INITIAL = 0  # /* Client boot, only used once on program start. */
C_S_PREPARING = 1  # /* Main menu (disconnected) and connected in pregame. */
C_S_RUNNING = 2  # /* Connected with game in progress. */
C_S_OVER = 3  # /* Connected with game over. */


class ClientState(CivPropController):
    def __init__(self, username: str, ws_client: CivConnection, rule_ctrl: RulesetCtrl):
        super().__init__(ws_client)
        self.rule_ctrl = rule_ctrl
        self.civclient_state = C_S_INITIAL
        self.connect_error = False
        self.oldstate = -1
        self.prop_actions = NoActions(ws_client)
        self.prop_state = EmptyState()

        self.username_original = username
        self.username = username
        # print(f'init-ClientState: {self.username}')
        self.client = {}
        # Store the client connection state, e.g., conn_id, established. First initialized during handle_server_join_reply.
        self.client["conn"] = {}
        self.client_frozen = False

        # Store all connection information. Also include other players' connections with server
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

        # If there is name conflict, add an index to the end of the username
        self.name_index = 0

        self.multiplayer_game = fc_args['multiplayer_game']
        self.hotseat_game = fc_args['hotseat_game']
        # For host of multiplayer game, follower should be False. For Follower, it should be true
        self.follower = False
        # whether to wait for observer before start game in multiplayer mode
        self.wait_for_observer = fc_args['wait_for_observer']

        # Used when load a game. When saving in a loaded game, the turn number in the savename given by the server will start from 1 while the turn number is actually not.
        self.load_game_tried = False
        self.load_complete = False
        self.follower_take = False
        self.begin_logged = False

        # Use this to determine whether a packet 115 is the first one and then decide whether the client is a follower
        self.first_conn_info_received = False

    def register_all_handlers(self):
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

    def set_follower_property(self):
        self.follower = True

    def get_follower_property(self):
        return self.follower

    def init_game_setting(self):
        if fc_args['debug.randomly_generate_seeds']:
            random.seed(os.getpid()+int(time.time()) % 100000)
            mapseed = random.randint(0, 999999)
            gameseed = random.randint(0, 999999)
            self.ws_client.send_message(f"/set mapseed {mapseed}")
            self.ws_client.send_message(f"/set gameseed {gameseed}")
        else:
            # Set map seed. The same seed leads to the same map.
            if 'debug.mapseed' in fc_args:
                self.ws_client.send_message(f'/set mapseed {fc_args["debug.mapseed"]}')
            if 'debug.gameseed' in fc_args:
                self.ws_client.send_message(f'/set gameseed {fc_args["debug.gameseed"]}')

        if self.multiplayer_game:
            self.set_multiplayer_game()

        if self.hotseat_game:
            self.set_hotseat_game()

    def should_prepare_game_base_on_message(self, message) -> bool:
        if not self.civclient_state == C_S_PREPARING:
            return False

        if self.follower:
            # The follower wait for the ready message from the host
            if 'Please be ready to start' in message:
                return True
        else:
            if self.wait_for_observer == False:
                # Auto start game if not waiting for observer. Needed for single player game
                if 'You are logged in as' in message:
                    return True
                # When wait_for_observer was True, we need this to start the game for single player mode.
                if (fc_args['minp'] == 1 or self.multiplayer_game == False) and ('Please be ready to start' in message or 'Load complete' in message):
                    return True
                elif self.multiplayer_game:
                    # Everytime follower be connected, the host send a ready message
                    if 'has connected from' in message or 'Load complete' in message:
                    # if 'has connected from' in message or 'now controls' in message:
                    # if 'has connected from' in message:
                        self.ws_client.send_message('Please be ready to start')
                    # If it is multiplayer game, check if all players are ready
                    if 'alive players are ready to start' in message:
                        # Follower always set itself to be ready when new player join
                        ready_player_num, overall_player_num = self.get_ready_state(message)
                        if ready_player_num == overall_player_num-1:
                            return True
            elif 'now observes' in message:
                # Observer has joined
                self.wait_for_observer = False
                self.ws_client.send_message('Please be ready to start')
        return False

    def get_ready_state(self, message):
        # Assume the player ready message is of format: "m out of n alive players..."
        temp_str = message.split(' out of ')
        return int(temp_str[0][-1]), int(temp_str[1][0])

    def get_password(self):
        password = fc_args['debug.password']
        sha_password = hashlib.sha512(password.encode('UTF-8'))
        sha_password = urllib.parse.quote(sha_password.hexdigest())
        return sha_password

    def try_create_user_account(self, host, username, password):
        url = f"http://{host}:8080/create_pbem_user?username={username}&email={username}@civrealm.org&password={password}&captcha=null"
        response = requests.post(url)
        return response.status_code

    def login(self):
        freeciv_version = "+Freeciv.Web.Devel-3.3"
        google_user_subject = None
        # print(f'login-username: {self.username}')
        if self.name_index > 0:
            self.username = f'{self.username_original}{self.name_index}'
        self.name_index += 1
        # Maybe create an user account on Freeciv Web
        sha_password = self.get_password()

        self.try_create_user_account(fc_args['host'], self.username, sha_password)

        # Log in to Freeciv Web through websocket
        login_message = {"pid": 4, "username": self.username,
                         "capability": freeciv_version, "version_label": "-dev",
                         "major_version": 2, "minor_version": 5, "patch_version": 99,
                         "port": self.ws_client.client_port, "password": sha_password,
                         "subject": google_user_subject}
        # print(login_message)
        fc_logger.debug(f'Log in to port {self.ws_client.client_port}')
        self.ws_client.send(login_message)
        fc_logger.debug(f'Log in message: {login_message}')

    def set_hotseat_game(self):
        # set player to 2. Based on HACKING file
        self.ws_client.send_message("/set aifill 2")
        # based on https://github.com/freeciv/freeciv-web/blob/4de320067bef09da046d8b1e07b3e018a866493b/freeciv-web/src/main/webapp/javascript/hotseat.js
        self.ws_client.send_message("/set phasemode player")
        self.ws_client.send_message("/set minp 2")
        self.ws_client.send_message(f"/set endvictory {fc_args['endvictory']}")
        self.ws_client.send_message(f"/set victories {fc_args['victories']}")
        self.ws_client.send_message("/set ec_chat=enabled")
        self.ws_client.send_message("/set ec_info=enabled")
        self.ws_client.send_message("/set ec_max_size=20000")
        self.ws_client.send_message("/set ec_turns=32768")

        self.ws_client.send_message("/set autotoggle disabled")
        # add another agent under our control
        self.ws_client.send_message(f"/create {self.user_name}2")
        self.ws_client.send_message(f"/ai {self.user_name}2")

        self.ws_client.send_message("/metamessage hotseat game")
        requests.post(f"http://{fc_args['host']}:8080/gamesetting?openchatbox={fc_args['openchatbox']}")

    def set_multiplayer_game(self):
        # Set AI player to 0. Based on HACKING file
        self.ws_client.send_message(f"/rulesetdir {fc_args['ruleset']}")
        self.ws_client.send_message(f"/set aifill {fc_args['aifill']}")
        self.ws_client.send_message(f"/set endvictory {fc_args['endvictory']}")
        self.ws_client.send_message(f"/set victories {fc_args['victories']}")
        # Based on https://github.com/freeciv/freeciv-web/blob/de87e9c62dc4f274d95b5c298372d3ce8d6d57c7/publite2/pubscript_multiplayer.serv
        self.ws_client.send_message("/set topology \"\"")
        self.ws_client.send_message("/set wrap WRAPX")
        # Set mode as turn-by-turn. Not allow players to play simultaneously.
        self.ws_client.send_message("/set phasemode player")
        self.ws_client.send_message("/set nationset all")
        self.ws_client.send_message(f"/set maxplayers {fc_args['maxplayers']}")
        # This setting allows human to take the control of the agent in the middle of the game
        self.ws_client.send_message(f"/set allowtake {fc_args['allowtake']}")
        self.ws_client.send_message(f"/set autotoggle {fc_args['autotoggle']}")
        self.ws_client.send_message("/set timeout 0")
        self.ws_client.send_message("/set netwait 15")
        # self.ws_client.send_message("/set nettimeout 120")
        self.ws_client.send_message("/set pingtime 30")
        self.ws_client.send_message("/set pingtimeout 720")
        self.ws_client.send_message("/set threaded_save enabled")
        self.ws_client.send_message("/set scorelog enabled")
        self.ws_client.send_message("/set size 4")
        self.ws_client.send_message("/set landm 50")
        # use /set minp 1 will allow single agent to play
        self.ws_client.send_message(f"/set minp {fc_args['minp']}")
        # FRACTAL to make players on one continent, FAIR to make players on islands with the same geography
        self.ws_client.send_message("/set generator FRACTAL")
        # self.ws_client.send_message("/metaconnection persistent")
        self.ws_client.send_message(
            f"/metamessage Multiplayer Game hosted by {self.username} in port {self.ws_client.client_port}")
        requests.post(f"http://{fc_args['host']}:8080/gamesetting?openchatbox={fc_args['openchatbox']}")

    def update_state(self, packet):
        self.client["conn"] = packet

    def has_id(self, cid):
        return cid == self.client["conn"]["id"]

    # Return the player_num to which this connection attaches.
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
        fc_logger.info(packet)
        fc_logger.info("\r\n")

    def handle_authentication_req(self, packet):
        raise Exception("Not implemented yet")
        # show_auth_dialog(packet)

    def handle_server_shutdown(self, packet):
        raise Exception('Receive server shutdown message.')

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
        # if self.follower and not self.follower_take:
        #     self.ws_client.send_message(f'/take {self.username}')
        #     self.follower_take = True
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
            After we send a join packet to the server we receive a reply.
            This function handles the reply.  100% Complete.
        """
        fc_logger.debug(f'Join response packet: {packet}')
        if packet['you_can_join']:
            self.client["conn"]["established"] = True
            self.client["conn"]["id"] = packet['conn_id']

            self.set_client_state(C_S_PREPARING)
            self.send_client_info()

            if self.username != self.username_original:
                fc_args['username'] = self.username
                update_logger(self.username_original, self.username)

        elif 'already connected' in packet['message']:
            if fc_args['self_play']:
                # login() in network_init() will increase name_index and connect again
                self.ws_client.network_init()
            else:
                raise RuntimeError(f"Login congestion: {packet['message']}. Port: {self.ws_client.client_port}")
        else:
            raise RuntimeError(f"Log in rejected: {packet['message']}")

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
        return not self.client_is_observer()

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

    def surrender_game(self):
        if not self.client_is_observer() and self.ws_client != None and self.ws_client.readyState == 1:
            self.ws_client.send_message("/surrender ")

    def pregame_start_game(self):
        test_packet = {"pid": packet_player_ready, "is_ready": True,
                       "player_no": self.player_num()}
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
