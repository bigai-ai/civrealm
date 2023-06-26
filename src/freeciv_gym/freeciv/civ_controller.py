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

import random

from freeciv_gym.freeciv.connectivity.base_controller import CivPropController
from freeciv_gym.freeciv.connectivity.civ_connection import CivConnection
from freeciv_gym.freeciv.connectivity.client_state import C_S_PREPARING, ClientState, C_S_RUNNING

from freeciv_gym.freeciv.players.player_ctrl import PlayerCtrl, PLRF_AI
from freeciv_gym.freeciv.players.diplomacy import DiplomacyCtrl
from freeciv_gym.freeciv.players.government import GovernmentCtrl

from freeciv_gym.freeciv.game.game_ctrl import GameCtrl
from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
from freeciv_gym.freeciv.game.options_ctrl import OptionCtrl

from freeciv_gym.freeciv.units.unit_ctrl import UnitCtrl
from freeciv_gym.freeciv.map.map_ctrl import MapCtrl
from freeciv_gym.freeciv.city.city_ctrl import CityCtrl
from freeciv_gym.freeciv.research.tech_ctrl import TechCtrl

from freeciv_gym.freeciv.utils.fc_events import E_UNDEFINED, E_BAD_COMMAND
from freeciv_gym.freeciv.utils.fc_types import packet_nation_select_req, packet_player_phase_done
from freeciv_gym.freeciv.utils.civ_monitor import CivMonitor

from freeciv_gym.freeciv.turn_manager import TurnManager
from freeciv_gym.freeciv.utils.freeciv_logging import logger
from freeciv_gym.configs import args


class CivController(CivPropController):
    """
    This class is the main controller for the game. It is responsible for handling the game state and the game logic. It is also responsible for handling the WebSocket connection to the Freeciv server. It is the main interface for the user to interact with the game. 

    To connect to the server, call the init_network() method. 
    To login to a game, call the init_game() method.  
    """

    def __init__(self, username, host='localhost', client_port=args['client_port'], visualize=False):
        """
        Initialize the controller for the game before the WebSocket connection is open. 

        Parameters
        ----------
        username : str
            The username of the player.
        host : str, optional
            The host of the Freeciv server. The default is 'localhost'.
        client_port : int, optional
            The port of the Freeciv server. The default is 6000.
            6000, 6004 and 6005 are for single player game.
            6001 and 6002 are for multiplayer game.
            6003 and 6006 are for longturn game (one turn per day).
        visualize : bool, optional
            Whether to visualize the game. The default is False.
        """
        super().__init__(CivConnection(host, client_port))
        self.ws_client.set_on_connection_success_callback(self.init_game)
        self.ws_client.set_packets_callback(self.assign_packets)

        self.ai_skill_level = 3
        self.nation_select_id = -1
        self.turn_manager = TurnManager()
        if args['multiplayer_game']:
            assert client_port == 6001, 'Multiplayer game must use port 6001'
        self.user_name = username

        self.visualize = visualize
        self.monitor = None
        if self.visualize:
            self.monitor = CivMonitor(host, username)

        # Use this to determine whether a packet 115 is the first one and then decide whether the client is a follower
        self.first_conn_info_received = False
        self.init_controllers()

    def register_all_handlers(self):
        self.register_handler(25, "handle_chat_msg")
        self.register_handler(28, "handle_early_chat_msg")

        self.register_handler(115, "handle_conn_info")
        self.register_handler(126, "handle_start_phase")
        self.register_handler(125, "handle_end_phase")

        self.register_handler(128, "handle_begin_turn")
        self.register_handler(129, "handle_end_turn")

        self.register_handler(29, "handle_version_info")
        # New handler for hotseat mode (or more generally due to game setting change)
        # The received messages may need to be handled for different modes
        self.register_handler(512, "handle_ruleset_clause_msg")
        self.register_handler(20, "handle_ruleset_impr_flag_msg")
        self.register_handler(259, "handle_web_player_addition_info")
        self.register_handler(66, "handle_unknown_research_msg")

    def init_controllers(self):
        """
        Initialize all controllers for the game. This is done in the constructor before the WebSocket connection is open, hence it is called before init_game() is called.
        """
        self.game_ctrl = GameCtrl(self.ws_client)
        self.opt_ctrl = OptionCtrl(self.ws_client)
        self.rule_ctrl = RulesetCtrl(self.ws_client)
        self.map_ctrl = MapCtrl(self.ws_client, self.rule_ctrl)

        self.clstate = ClientState(self.user_name,
                                   self.ws_client, self.rule_ctrl)

        self.dipl_ctrl = DiplomacyCtrl(self.ws_client, self.clstate, self.rule_ctrl)
        self.player_ctrl = PlayerCtrl(self.ws_client, self.clstate, self.rule_ctrl, self.dipl_ctrl)

        self.tech_ctrl = TechCtrl(self.ws_client, self.rule_ctrl, self.player_ctrl)
        self.city_ctrl = CityCtrl(self.ws_client, self.rule_ctrl, self.player_ctrl, self.clstate,
                                  self.game_ctrl, self.map_ctrl)

        self.unit_ctrl = UnitCtrl(self.ws_client, self.rule_ctrl, self.map_ctrl,
                                  self.player_ctrl, self.city_ctrl, self.dipl_ctrl)

        self.gov_ctrl = GovernmentCtrl(self.ws_client, self.city_ctrl, self.rule_ctrl)

        self.controller_list = {"game": self.game_ctrl,
                                "rules": self.rule_ctrl,
                                "map": self.map_ctrl,
                                "player": self.player_ctrl,
                                "city": self.city_ctrl,
                                "tech": self.tech_ctrl,
                                "unit": self.unit_ctrl,
                                "options": self.opt_ctrl,
                                "dipl": self.dipl_ctrl,
                                "gov": self.gov_ctrl,
                                "client": self.clstate}
        for ctrl in self.controller_list:
            self.controller_list[ctrl].register_with_parent(self)

    # ============================================================
    # ======================= Game control =======================
    # ============================================================
    def init_network(self):
        self.ws_client.network_init()

    def lock_control(self):
        """
        Lock the control of the game. This is a blocking function, should be called when the player is waiting for the server to respond and should not be able to act.
        """
        self.ws_client.start_ioloop()

    def init_game(self):
        """
        When the WebSocket connection is open and ready to communicate, then
        send the first login message to the server.
        """
        if self.visualize:
            self.monitor.start_monitor()

        self.clstate.login()

    def get_turn(self):
        return self.turn_manager.turn

    def ready_to_act(self):
        # TODO: make sure the condition is correct
        return not self.ws_client.is_waiting_for_responses()

    def try_grant_control_to_player(self):
        """
        Check whether the player is ready to act. If true, the controller should stop the WebSocket loop and grant control to the player.
        """
        # TODO: Check the triggering conditions. Now it is only called when the contoller has processed a batch of packets.
        if not self.turn_manager.turn_active:
            return
        if self.ready_to_act():
            self.ws_client.stop_ioloop()

    def perform_action(self, action):
        if action == None:
            self.send_end_turn()
        else:
            action.trigger_action(self.ws_client)

    def get_observations(self):
        self.lock_control()
        return self.turn_manager.get_observation()

    def get_reward(self):
        return self.turn_manager.get_reward()

    def get_info(self):
        return {'turn': self.turn_manager.turn}

    def send_end_turn(self):
        """Ends the current turn."""
        if self.rule_ctrl.game_info == {}:
            return

        self.turn_manager.end_turn()
        logger.info('Ending turn {}'.format(self.rule_ctrl.game_info['turn']))
        packet = {"pid": packet_player_phase_done, "turn": self.rule_ctrl.game_info['turn']}
        self.ws_client.send_request(packet)

    def game_has_terminated(self) -> bool:
        """Returns True if the game has ended.       
        """
        # TODO: check victory conditions.
        return self.turn_manager.turn > args['max_turns']

    def close(self):
        if self.visualize:
            self.monitor.stop_monitor()
        self.ws_client.close()

    # ============================================================
    # ========================= Handlers =========================
    # ============================================================
    def assign_packets(self, p_list):
        """Distributes packets to the handlers of the controllers"""
        if p_list is None:
            return
        try:
            logger.info(("Waiting for: ", self.ws_client.wait_for_packs))
            for packet in p_list:
                if packet is None:
                    continue
                self.ws_client.stop_waiting(packet['pid'])
                self.handle_pack(packet['pid'], packet)
                if 31 in self.ws_client.wait_for_packs:
                    # TODO: handle wait_for_packs
                    pass

            self.try_grant_control_to_player()
        except Exception:
            raise

    def prepare_game(self):
        names, opts = self.player_ctrl.pregame_getplayer_options()
        if names != []:
            self.pregame_choose_player(opts[0]["name"], opts[0]["playerid"], "pick_nation")

    def pregame_choose_player(self, name, player_id, option="pick_nation"):
        if name == None:
            return
        name = name.split(" ")[0]

        if option != "pick_nation":
            self.ws_client.send_message("/%s %s" % (option, name))
        else:
            self.pregame_choose_nation(player_id)

        self.clstate.pregame_start_game()
        # /* set state of Start game button depending on if user is ready. */

        # self.clstate.update_metamessage_on_gamestart()
        # if self.player_ctrl.is_player_ready():

    def pregame_choose_nation(self, player_id):
        namelist = self.rule_ctrl.get_nation_options()
        chosen_nation_name = namelist[random.randint(0, len(namelist))]
        player_num = self.clstate.player_num()
        if (chosen_nation_name == -1 or player_num == None
                or player_id == None or player_id < 0):
            return

        pplayer = self.player_ctrl.get_player(player_id)
        pnation = self.rule_ctrl.nations[chosen_nation_name]
        if pplayer == None:
            return

        leader_name = pplayer['name']
        if pplayer['flags'][PLRF_AI] > 0:
            leader_name = pnation['leader_name'][0]

        packet = {"pid": packet_nation_select_req,
                  "player_no": player_id,
                  "nation_no": chosen_nation_name,
                  "is_male": True,  # /* FIXME */
                  "name": leader_name,
                  "style": pnation['style']}

        self.ws_client.send_request(packet)

    def change_ruleset(self, to):
        # """Change the ruleset to"""

        # send_message("/rulesetdir " + to)
        # // reset some ruleset defined settings.
        # send_message("/set nationset all")
        # submit_nation_choice(chosen_nation, choosing_player)
        raise Exception("Not implemented")

    def handle_early_chat_msg(self, packet):
        """
        Handle an early message packet. Thease have format like other chat
      messages but server sends them only about events related to establishing
      the connection and other setup in the early phase. They are a separate
      packet just so that client knows thse to be already relevant when it's
      only setting itself up - other chat messages might be just something
      sent to all clients, and we might want to still consider ourselves
      "not connected" (not receivers of those messages) until we are fully
      in the game.
        """
        # /* Handle as a regular chat message for now. */
        self.handle_chat_msg(packet)

    def handle_chat_msg(self, packet):
        """#/* 100% complete */"""
        try:
            message = packet['message']
            conn_id = packet['conn_id']
            event = packet['event']
        except KeyError:
            logger.error(f'Packet is missing some keys: {packet}')
            raise Exception("Packet is missing some keys")

        if message is None:
            return
        if event is None or event < 0 or event >= E_UNDEFINED:
            logger.info('Undefined message event type')
            logger.info(packet)
            logger.info("\r\n")
            packet['event'] = event = E_UNDEFINED

        if event == E_BAD_COMMAND:
            logger.warning("Bad command event!")
            logger.warning(message)
            # TODO: handle bad command
            # assert(False)

        if self.clstate.should_prepare_game_base_on_message(message):
            self.prepare_game()

        if conn_id in self.clstate.connections:
            message = "<b>" + self.clstate.connections[conn_id]['username'] + ":</b>" + message
        else:
            if "/metamessage" in message:
                # don't spam message dialog on game start.
                return
            if "Metaserver message string" in message:
                # don't spam message dialog on game start.
                return

        packet['message'] = message
        logger.info("chat_msg: ", packet)

    def handle_start_phase(self, packet):
        """Handle signal from server to start phase - prior to starting turn"""
        logger.info("Starting Phase")
        self.clstate.update_client_state(C_S_RUNNING)

    def handle_end_phase(self, packet):
        # chatbox_clip_messages()
        pass

    def handle_version_info(self, packet):
        logger.debug(packet)

    def handle_ruleset_clause_msg(self, packet):
        logger.debug(packet)

    def handle_ruleset_impr_flag_msg(self, packet):
        logger.debug(packet)

    def handle_web_player_addition_info(self, packet):
        logger.debug(packet)

    def handle_unknown_research_msg(self, packet):
        logger.debug(packet)

    def handle_begin_turn(self, packet):
        """Handle signal from server to start turn"""
        if self.monitor != None:
            while True:
                if self.monitor.start_observe:
                    break

        if self.clstate.client_is_observer() or not self.clstate.is_playing():
            self.send_end_turn()
            return

        pplayer = self.clstate.cur_player()
        self.turn_manager.begin_turn(pplayer, self.controller_list)

    def handle_end_turn(self, packet):
        """Handle signal from server to end turn"""
        # reset_unit_anim_list()
        pass

    def handle_conn_info(self, packet):
        """
            Remove, add, or update dummy connection struct representing some
            connection to the server, with info from packet_conn_info.
            Updates player and game connection lists.
            Calls update_players_dialog() in case info for that has changed.
            99% done.
        """

        pconn = self.clstate.find_conn_by_id(packet['id'])

        if not packet['used']:
            # Forget the connection
            if pconn is None:
                logger.warning("Server removed unknown connection " + str(packet['id']))
                return
            self.clstate.client_remove_cli_conn(pconn)
            pconn = None
        else:
            # TODO: ensure 'player_num' in packet-115 is equivalent to 'playerno' in packet-51
            pplayer = self.player_ctrl.valid_player_by_number(packet['player_num'])
            # Receive the first conn_info
            if self.first_conn_info_received == False:
                # Assume the first packet-115 (conn_info) comes after the packet-51 (player_info)
                assert (pplayer != None)
                # The client is a host. Specify the game setting below.
                if packet['player_num'] == 0:
                    self.clstate.init_game_setting()
                else:
                    # Set the follower property in clstate
                    self.clstate.set_follower_property()
                self.first_conn_info_received = True
            # Unknown player
            if pplayer == None:
                return

            # Insert player info into connection info packet. 'playing' means the player is still playing the game
            packet['playing'] = pplayer
            # If the connection info is about the client itself
            if self.clstate.has_id(packet["id"]):
                # Update connection info and player info
                self.clstate.update_state(packet)

            # Store connection info
            self.clstate.conn_list_append(packet)

        if self.clstate.has_id(packet["id"]) and self.clstate.cur_player() != packet['playing']:
            # It seems impossible to get here
            assert (False)
            self.clstate.set_client_state(C_S_PREPARING)

        # /* FIXME: not implemented yet.
        # update_players_dialog()
        # update_conn_list_dialog()