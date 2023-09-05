# Copyright (C) 2023  The Freeciv-gym project
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

import random
import json
import requests
import time
from datetime import datetime, timezone, timedelta

from freeciv_gym.freeciv.utils.base_controller import CivPropController
from freeciv_gym.freeciv.connectivity.civ_connection import CivConnection
from freeciv_gym.freeciv.connectivity.client_state import C_S_PREPARING, ClientState, C_S_RUNNING

from freeciv_gym.freeciv.players.player_ctrl import PlayerCtrl
import freeciv_gym.freeciv.players.player_const as player_const
from freeciv_gym.freeciv.players.diplomacy import DiplomacyCtrl
from freeciv_gym.freeciv.players.government import GovernmentCtrl

from freeciv_gym.freeciv.game.game_ctrl import GameCtrl
from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
from freeciv_gym.freeciv.game.options_ctrl import OptionCtrl

from freeciv_gym.freeciv.units.unit_ctrl import UnitCtrl
from freeciv_gym.freeciv.map.map_ctrl import MapCtrl
from freeciv_gym.freeciv.city.city_ctrl import CityCtrl
from freeciv_gym.freeciv.tech.tech_ctrl import TechCtrl

from freeciv_gym.freeciv.utils.fc_events import E_UNDEFINED, E_BAD_COMMAND, E_SCRIPT, E_GAME_END
from freeciv_gym.freeciv.utils.fc_types import packet_nation_select_req, packet_player_phase_done
from freeciv_gym.freeciv.utils.civ_monitor import CivMonitor

from freeciv_gym.freeciv.turn_manager import TurnManager
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.freeciv.utils.port_list import PORT_LIST
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.fc_types import packet_chat_msg_req

MAX_REQUESTS = 10
SLEEP_TIME = 1


class CivController(CivPropController):
    """
    This class is the main controller for the game. It is responsible for handling the game state and the game logic. It is also responsible for handling the WebSocket connection to the Freeciv server. It is the main interface for the user to interact with the game. 

    To connect to the server, call the init_network() method. 
    To login to a game, call the init_game() method.  
    """

    def __init__(self, username=fc_args['username'], host=fc_args['host'],
                 client_port=fc_args['client_port'], visualize=False):
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
            6000 is for single player game.
            6001 is for multiplayer game.            
        visualize : bool, optional
            Whether to visualize the game. The default is False.
        """
        print("CivController: ", fc_args['username'])
        print("username:", username)
        super().__init__(CivConnection(host, client_port))
        self.ws_client.set_on_connection_success_callback(self.init_game)
        self.ws_client.set_packets_callback(self.assign_packets)

        self.ai_skill_level = 3
        self.nation_select_id = -1

        if fc_args['multiplayer_game']:
            assert client_port in PORT_LIST, f'Multiplayer game port {client_port} is invalid.'

        self.visualize = visualize
        self.monitor = None
        if self.visualize:
            self.monitor = CivMonitor(host, username)

        # Host address
        self.host = host
        if fc_args['multiplayer_game']:
            assert client_port in PORT_LIST, f'Multiplayer game port {client_port} is invalid.'
        self.client_port = client_port
        self.score_log_url = f'http://{self.host}:8080/data/scorelogs/score-{self.client_port}.log'

        self.turn_manager = TurnManager(self.client_port)

        self.username = username
        # The save will be deleted by default. If we find some issues in a certain turn, we should set this as False for that turn.
        self.delete_save = True
        self.game_saving_time_range = []
        self.game_is_over = False
        self.init_controllers(username)

    def reset(self):
        self.ws_client = CivConnection(self.host, self.client_port)
        self.ws_client.set_on_connection_success_callback(self.init_game)
        self.ws_client.set_packets_callback(self.assign_packets)
        self.hdict = {}
        # Register key in hdict
        self.register_all_handlers()
        self.turn_manager = TurnManager(self.client_port)
        self.delete_save = True
        self.game_saving_time_range = []
        self.init_controllers(self.username)

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
        self.register_handler(66, "handle_unknown_research_msg")

    def init_controllers(self, username):
        """
        Initialize all controllers for the game. This is done in the constructor before the WebSocket connection is open, hence it is called before init_game() is called.
        """
        self.game_ctrl = GameCtrl(self.ws_client)
        self.opt_ctrl = OptionCtrl(self.ws_client)
        self.rule_ctrl = RulesetCtrl(self.ws_client)
        self.map_ctrl = MapCtrl(self.ws_client, self.rule_ctrl)

        self.clstate = ClientState(username,
                                   self.ws_client, self.rule_ctrl)

        self.dipl_ctrl = DiplomacyCtrl(self.ws_client, self.clstate, self.rule_ctrl)

        self.city_ctrl = CityCtrl(self.ws_client, self.rule_ctrl, self.clstate, self.game_ctrl, self.map_ctrl)
        self.player_ctrl = PlayerCtrl(self.ws_client, self.clstate, self.city_ctrl, self.rule_ctrl, self.dipl_ctrl)
        self.tech_ctrl = TechCtrl(self.ws_client, self.rule_ctrl, self.player_ctrl)

        self.unit_ctrl = UnitCtrl(self.ws_client, self.opt_ctrl, self.rule_ctrl, self.map_ctrl,
                                  self.player_ctrl, self.city_ctrl, self.dipl_ctrl)

        self.gov_ctrl = GovernmentCtrl(self.ws_client, self.rule_ctrl, self.player_ctrl)

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
        """
        Called when Env calls reset() method.
        """
        self.ws_client.network_init()

    # Set the parameter with para_name as the given value.
    def set_parameter(self, para_name, value):
        fc_args[para_name] = value

    def lock_control(self):
        """
        Lock the control of the game. This is a blocking function, should be called when the player is waiting for the server to respond and should not be able to act.
        """
        try:
            self.ws_client.start_ioloop()
        except KeyboardInterrupt:
            self.close()
        # except RuntimeError as e:
        #     if str(e) == 'This event loop is already running':
        #         pass
        #     else:
        #         raise e

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

    def should_wait(self):
        if not self.player_ctrl.previous_players_finished():
            return True

        if self.ws_client.is_waiting_for_responses():
            return True

        return False

    def ready_to_act(self):
        """
        TODO: make sure the condition is correct, and incorporate this logic with the logic in the turn manager.
        - In a non-concurrent setting, the player should wait for the players with smaller player numbers to end their phase. 
        - turn_active is set to True after receving PACKET_BEGIN_TURN. It is set to False after our player has completed its phase.
        - In our player's phase, it should also wait for responses of actions performed in the previous step from the server to be ready to act. 
        """
        return self.turn_manager.turn_active and not self.should_wait()

    def my_player_is_defeated(self):
        if self.player_ctrl.my_player_id in self.player_ctrl.players:
            if not self.player_ctrl.my_player['is_alive']:
                return True
        return False

    def maybe_grant_control_to_player(self):
        """
        Check whether the player is ready to act. If true, the controller should stop the WebSocket loop and grant control to the player.
        """
        # TODO: Check the triggering conditions. Now it is only called when the contoller has processed a batch of packets.
        if self.ready_to_act():
            if not self.clstate.begin_logged:
                self.turn_manager.log_begin_turn()
                self.clstate.begin_logged = True
            self.ws_client.stop_ioloop()
            return

        if not self.should_wait() and self.my_player_is_defeated():
            self.ws_client.stop_ioloop()
            return

        return

    @property
    def action_space(self):
        return self.turn_manager.action_space

    @property
    def observation_space(self):
        return self.turn_manager.observation_space

    def perform_action(self, action):
        if action == None:
            self.send_end_turn()
        elif action == 'pass':
            self.ws_client.send_message(f"Debug.Do nothing for this step.")
        else:
            self.turn_manager.perform_action(action, self.ws_client)

    def _get_info(self):
        fc_logger.debug(f'get_info. Turn: {self.turn_manager.turn}')
        self.lock_control()
        if self.my_player_is_defeated():
            info = {'turn': self.turn_manager.turn, 'available_actions': None}
        else:
            self.turn_manager.get_available_actions()
            # Wait for and process probabilities of actions from server.
            self.lock_control()
            info = {'turn': self.turn_manager.turn, 'available_actions': self.turn_manager.get_info()}

        return info

    def _get_observation(self):
        fc_logger.debug(f'get_observation. Turn: {self.turn_manager.turn}')
        # TODO: change function name and return value
        if self.my_player_is_defeated():
            return None

        return self.turn_manager.get_observation()

    def get_info_and_observation(self):
        '''
        We put _get_info() before _get_observation() because the actions of new units will be initialized in 
        _get_info() and we need to get the probabilities of some actions (e.g., attack). We will trigger the 
        corresponding get_probability (e.g., GetAttack) actions in _get_info() to query the probabilities from 
        server. Therefore, we call _get_observation() after that to receive the action probabilities from server.        
        '''
        info = self._get_info()
        observation = self._get_observation()
        return info, observation

    def get_reward(self):
        current_score = self.player_ctrl.my_player['score']
        return self.turn_manager.get_reward(current_score)

    def send_end_turn(self):
        """Ends the current turn."""
        if self.rule_ctrl.game_info == {}:
            return
        self.clstate.begin_logged = False
        fc_logger.info(f"Ending turn {self.rule_ctrl.game_info['turn']}. Port: {self.client_port}")
        packet = {"pid": packet_player_phase_done, "turn": self.rule_ctrl.game_info['turn']}
        self.ws_client.send_request(packet)
        self.turn_manager.end_turn()

    def game_has_truncated(self) -> bool:
        """Returns True if the game has been truncated.
        """
        # fc_logger.debug(f"game_has_truncated: {self.turn_manager.turn > fc_args['max_turns']}")
        return self.turn_manager.turn > fc_args['max_turns']

    def game_has_terminated(self) -> bool:
        """Returns True if the game has ended.       
        """
        # FIXME: check victory conditions.
        if not self.player_ctrl.my_player['is_alive']:
            return True

        return False

    # ============================================================
    # ========================= Handlers =========================
    # ============================================================
    def assign_packets(self, p_list):
        """Distributes packets to the handlers of the controllers"""
        if p_list is None:
            return
        try:
            fc_logger.info(("Waiting for: ", self.ws_client.wait_for_packs))
            for packet in p_list:
                if packet is None:
                    continue
                pid_info = None
                if packet['pid'] == 31:
                    pid_info = (packet['pid'], packet['tile'])
                elif packet['pid'] == 44 or packet['pid'] == 62:
                    pid_info = (packet['pid'], packet['unit_id'])
                elif packet['pid'] == 249:
                    pid_info = (packet['pid'], packet['city'])
                elif packet['pid'] == 223:
                    pid_info = (packet['pid'], packet['player_id'])
                else:
                    if 'id' in packet:
                        pid_info = (packet['pid'], packet['id'])
                    elif 'actor_unit_id' in packet:
                        pid_info = (packet['pid'], packet['actor_unit_id'])
                    elif 'playerno' in packet:
                        pid_info = (packet['pid'], packet['playerno'])
                    elif 'playerid' in packet:
                        pid_info = (packet['pid'], packet['playerid'])
                    elif 'counterpart' in packet:
                        pid_info = (packet['pid'], packet['counterpart'])
                    elif 'plr1' in packet:
                        pid_info = (packet['pid'], (packet['plr1'], packet['plr2']))
                    elif 'tile' in packet:
                        pid_info = (packet['pid'], packet['tile'])
                    else:
                        pid_info = (packet['pid'], None)
                self.ws_client.stop_waiting(pid_info)
                self.handle_pack(packet['pid'], packet)

            if not self.clstate.client_frozen:
                self.maybe_grant_control_to_player()
        except Exception:
            raise

    def end_game(self):
        packet = {'pid': packet_chat_msg_req,
                  'message': f"/endgame"}
        wait_for_pid_list = self.end_game_packet_list()
        self.ws_client.send_request(packet, wait_for_pid=wait_for_pid_list)
        # Listen to the server to get final scores. We use start_ioloop() here since using lock_control() will lead to recursive calling of end_game() during KeyboardInterrupt.
        self.ws_client.start_ioloop()

    def close(self):
        if not self.game_is_over:
            self.end_game()
        if self.visualize:
            self.monitor.stop_monitor()
        if fc_args['debug.autosave'] and self.delete_save:
            self.delete_save_game()
        self.ws_client.close()

    def end_game_packet_list(self):
        wait_for_pid_list = []
        for player_id in self.player_ctrl.players.keys():
            wait_for_pid_list.append((223, player_id))
        return wait_for_pid_list

    def request_scorelog(self):
        """
        Format description of the scorelog format version 2
        ===================================================

        Empty lines and lines starting with '#' are comments. Each non-comment 
        line starts with a command. The parameter are supplied on that line
        and are seperated by a space. Strings which may contain whitespaces
        are always the last parameter and so extend till the end of line.

        The following commands exists:
        id <game-id>
        <game-id> is a string without whitespaces which is used
                  to match a scorelog against a savegame.

        tag <tag-id> <descr>
        add a data-type (tag)
          the <tag-id> is used in the 'data' commands
          <descr> is a string without whitespaces which
                  identified this tag

        turn <turn> <number> <descr>
        adds information about the <turn> turn
          <number> can be for example year
          <descr> may contain whitespaces

        addplayer <turn> <player-id> <name>
        adds a player starting at the given turn (inclusive)
          <player-id> is a number which can be reused
          <name> may contain whitespaces

        delplayer <turn> <player-id>
        removes a player from the game. The player was
          active till the given turn (inclusive)
          <player-id> used by the creation

        data <turn> <tag-id> <player-id> <value>
        give the value of the given tag for the given
        player for the given turn
        """
        game_scores = None

        for ptry in range(MAX_REQUESTS):
            response = requests.get(self.score_log_url, headers={"Cache-Control": "no-cache"})
            if response.status_code == 200:
                fc_logger.debug(f'Request of game_scores succeed')
                game_scores = response.text
                break
            else:
                fc_logger.debug(f'Request of game_scores failed with status code: {response.status_code}')
                time.sleep(SLEEP_TIME)
        return game_scores

    def save_game(self):
        # We keep the time interval in case the message delay causes the first or second save_name is different from the real save_name
        begin_time = datetime.now(timezone.utc)
        self.ws_client.send_message(f"/save ")
        end_time = datetime.now(timezone.utc)

        minutes_diff = (end_time - begin_time).total_seconds() // 60.0 + 1
        self.game_saving_time_range = [begin_time + timedelta(it) for it in range(int(minutes_diff))]

    def delete_save_game(self):
        """
        Delete the save game on the server (docker).
        Saved games are in '/var/lib/tomcat10/webapps/data/savegames/{username}'
        """
        # Check whether save_game() has been called.
        if len(self.game_saving_time_range) > 0:
            # fc_logger.info('delete_save_game')
            url = f"http://{self.host}:8080/listsavegames?username={self.clstate.username}"
            response = requests.post(url)
            save_list = response.text.split(';')

            real_saved_name = ''
            for saving_time in self.game_saving_time_range:
                possible_saved_name = f"{self.clstate.username}_T{self.turn_manager.turn}_{saving_time.strftime('%Y-%m-%d-%H_%M')}"
                for saved_name in save_list:
                    # Note that we should not let real_save_name=save_name because save_name may have a suffix, e.g., .sav.zst.
                    if possible_saved_name in saved_name:
                        real_saved_name = possible_saved_name
                        break

            if real_saved_name == '':
                fc_logger.warning('Failed to find saved game file to delete.')
                for saving_time in self.game_saving_time_range:
                    possible_saved_name = f"{self.clstate.username}_T{self.turn_manager.turn}_{saving_time.strftime('%Y-%m-%d-%H_%M')}"
                    fc_logger.warning(f'Possible save name: {possible_saved_name}')
                for saved_name in save_list:
                    fc_logger.warning(f'Save name in List: {saved_name}')
                return

            # If use savegame=ALL, it will delete all saves under the given username.
            sha_password = self.clstate.get_password()
            url = f"http://{self.host}:8080/deletesavegame?username={self.clstate.username}&savegame={real_saved_name}&sha_password={sha_password}"
            response = requests.post(url)
            if response.text != '':
                fc_logger.debug(f'Failed to delete save. Response text: {response.text}')
            else:
                fc_logger.debug(f'Deleting unnecessary saved game.')

            self.game_saving_time_range.clear()

    def load_game(self, save_name):
        load_username = save_name.split('_')[0]
        if load_username != self.clstate.username:
            raise RuntimeError(
                f'The loaded game is saved by another user: {load_username}. Your username is {self.clstate.username}.')
        self.ws_client.send_message(f"/load {save_name}")
        self.turn_manager.turn = int(save_name.split('_')[1][1:])

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
        if pplayer['flags'][player_const.PLRF_AI] > 0:
            leader_name = pnation['leader_name'][0]
        # China id is 107
        # chosen_nation_name = 107
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

    def handle_load_game(self, message):
        # To observe a load game, you can first sign in and then send /observe PLAYER_NAME message by console or chatbox. If there is a space in the PLAYER_NAME, use "" to specify.
        if 'You are logged in as' in message and not self.clstate.load_game_tried:
            self.load_game(fc_args['debug.load_game'])
            self.clstate.load_game_tried = True

        if 'load: Cannot find savegame or scenario with the name' in message:
            fc_logger.error(f"Load game unsuccessfully. Message: {message}")
            raise RuntimeError(f"Load game unsuccessfully. Message: {message}")

        if 'Load complete' in message:
            self.clstate.load_complete = True

    def parse_script_message(self, message):
        if 'minitask' in message:
            js_message = {"error": ""}
            try:
                js_message.update(json.loads(message))
            except Exception as ex:
                js_message["error"] = ex
            self.turn_manager.set_message(js_message)
        return
    
    def get_turn_message(self):
        return self.turn_manager.turn_message

    def handle_chat_msg(self, packet):
        """#/* 100% complete */"""
        try:
            message = packet['message']
            conn_id = packet['conn_id']
            event = packet['event']
        except KeyError:
            fc_logger.error(f'Packet is missing some keys: {packet}')
            raise Exception("Packet is missing some keys")

        if message is None:
            return
        if event is None or event < 0 or event >= E_UNDEFINED:
            fc_logger.info('Undefined message event type')
            fc_logger.info(packet)
            fc_logger.info("\r\n")
            packet['event'] = event = E_UNDEFINED

        if event == E_BAD_COMMAND:
            fc_logger.warning("Bad command event!")
            fc_logger.warning(message)
            # TODO: handle bad command
            # assert(False)
        elif event == E_SCRIPT:
            self.parse_script_message(message)
        elif event == E_GAME_END:
            self.game_is_over = True

        if 'connected to no player' in message:
            raise RuntimeError(
                f"{message}. There is no room for new players. You may increase the maximum player number or change the username to match an existing player if you are loading a game.")

        if fc_args['debug.load_game'] != "" and self.clstate.civclient_state == C_S_PREPARING:
            self.handle_load_game(message)

        if self.clstate.should_prepare_game_base_on_message(message):
            if fc_args['debug.load_game'] != "":
                if self.clstate.load_complete:
                    # Already load game, start without choosing nation
                    self.clstate.pregame_start_game()
            else:
                # Choose nation and start game
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
        fc_logger.info(f'chat_msg: {packet}')

    def handle_start_phase(self, packet):
        """Handle signal from server to start phase - prior to starting turn"""
        fc_logger.info("Starting Phase")
        self.clstate.update_client_state(C_S_RUNNING)

    def handle_end_phase(self, packet):
        # chatbox_clip_messages()
        pass

    def handle_version_info(self, packet):
        fc_logger.debug(packet)

    def handle_ruleset_clause_msg(self, packet):
        fc_logger.debug(packet)

    def handle_ruleset_impr_flag_msg(self, packet):
        fc_logger.debug(packet)

    def handle_unknown_research_msg(self, packet):
        fc_logger.debug(packet)

    def handle_begin_turn(self, packet):
        """Handle signal from server to start turn"""
        if self.turn_manager.turn <= fc_args['max_turns'] and fc_args['debug.autosave']:
            # Save the game state in the begining of every turn.
            # Save game command '/save' does not support user-defined save_name.
            self.save_game()

        if self.monitor != None:
            while True:
                if self.monitor.start_observe:
                    break

        if self.clstate.client_is_observer():
            self.send_end_turn()
            return

        self.unit_ctrl.reset_keep_activity_state()
        pplayer = self.player_ctrl.my_player
        fc_logger.debug(f'Receiving begin turn packets: {packet}')
        self.turn_manager.begin_turn(pplayer, self.controller_list)

    def handle_end_turn(self, packet):
        """Handle signal from server to end turn"""
        # reset_unit_anim_list()
        # Delete saved game in the end of turn.
        # fc_logger.info('handle_end_turn')

        if fc_args['debug.autosave'] and self.delete_save:
            self.delete_save_game()
        # # Set delete_save for the next turn
        # self.delete_save = True

        self.turn_manager.turn += 1
        # if self.client_port == 6301:
        #     self.close()

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
                fc_logger.warning(f"Server removed unknown connection {packet['id']}")
                return
            self.clstate.client_remove_cli_conn(pconn)
            pconn = None
        else:
            pplayer = self.player_ctrl.valid_player_by_number(packet['player_num'])
            # Receive the first conn_info
            if self.clstate.first_conn_info_received == False:
                # When first conn_info comes, the connections in clstate is empty.
                assert (pconn == None)
                # Assume the first packet-115 (conn_info) comes after the packet-51 (player_info)
                assert (pplayer != None)
                # The client is a host. Specify the game setting below.
                # Assume the connection id of a host is 1.
                if packet['id'] == 1 and packet['username'] == self.clstate.username:
                    self.clstate.init_game_setting()
                else:
                    # Set the follower property in clstate
                    self.clstate.set_follower_property()
                self.clstate.first_conn_info_received = True
            # This connection is not attached to any players, just return.
            if pplayer == None:
                return

            # If the connection info is about the client itself
            if self.clstate.has_id(packet["id"]):
                # Update connection info and player info
                self.clstate.update_state(packet)

            # Store connection info
            self.clstate.conn_list_append(packet)

        # /* FIXME: not implemented yet.
        # update_players_dialog()
        # update_conn_list_dialog()
