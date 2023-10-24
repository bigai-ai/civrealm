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

import os
import json
import time
from civrealm.freeciv.connectivity.civ_connection import CivConnection

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.utils.base_action import NoActions
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.freeciv.utils.eval_tags import EVALUATION_TAGS

from civrealm.freeciv.game.info_states import GameState

# see handle_ruleset_extra, where EXTRA_* variables are defines dynamically.
EXTRA_NONE = -1
IDENTITY_NUMBER_ZERO = 0


class GameCtrl(CivPropController):
    def __init__(self, ws_client: CivConnection):
        super().__init__(ws_client)

        self.calendar_info = {}
        self.scenario_info = {}
        self.page_msg = {}
        self.ws_client = ws_client
        self.prop_state = GameState(self.scenario_info, self.calendar_info)
        self.prop_actions = NoActions(ws_client)
        self.end_game_player_packet = None
        self.end_game_report = None
        self.game_results = dict()

    def register_all_handlers(self):
        self.register_handler(13, "handle_scenario_description")
        self.register_handler(180, "handle_scenario_info")

        self.register_handler(163, "handle_game_load")

        self.register_handler(255, "handle_calendar_info")

        self.register_handler(110, "handle_page_msg")
        self.register_handler(250, "handle_page_msg_part")
        self.register_handler(19, "handle_team_name_info")

        self.register_handler(185, "handle_vote_new")
        self.register_handler(186, "handle_vote_update")
        self.register_handler(187, "handle_vote_remove")
        self.register_handler(188, "handle_vote_resolve")

        self.register_handler(204, "handle_edit_startpos")
        self.register_handler(205, "handle_edit_startpos_full")
        self.register_handler(219, "handle_edit_object_created")

        self.register_handler(223, "handle_endgame_player")
        self.register_handler(12, "handle_endgame_report")
        self.register_handler(238, "handle_achievement_info")
        self.register_handler(245, "handle_play_music")

    def handle_scenario_info(self, packet):
        """
        Receive scenario information about the current game.

        The current game is a scenario game if scenario_info's 'is_scenario'
        field is set to true.
        """
        self.scenario_info.update(packet)

    def handle_scenario_description(self, packet):
        """Receive scenario description of the current scenario."""
        self.scenario_info["description"] = packet["description"]

        # /* Show the updated game information. */
        # update_game_info_pregame()

    def handle_game_load(self, packet):
        # if not packet['load_successful']:
        #     fc_logger.debug(f"Load game unsuccessfully. Message: {packet['load_filename']}")
        #     raise RuntimeError(f"Load game unsuccessfully. Message: {packet['load_filename']}")
        pass

    def handle_calendar_info(self, packet):
        """Handle the calendar info packet."""
        self.calendar_info.update(packet)

    def handle_page_msg(self, packet):
        """Page_msg header handler."""
        # Message information
        self.page_msg["headline"] = packet["headline"]
        self.page_msg["caption"] = packet["caption"]
        self.page_msg["event"] = packet["event"]

        # /* How many fragments to expect. */
        self.page_msg["missing_parts"] = packet["parts"]

        # /* Will come in follow up packets. */
        self.page_msg["message"] = ""

    def handle_page_msg_part(self, packet):
        """Page_msg part handler."""
        # /* Add the new parts of the message content. */
        self.page_msg["message"] = self.page_msg["message"] + packet["lines"]

        # /* Register that it was received. */
        self.page_msg["missing_parts"] -= 1
        if self.page_msg["missing_parts"] == 0:
            # /* This was the last part. */
            regxp = "/\n/gi"

            self.page_msg["message"] = self.page_msg["message"].replace(regxp, "<br>\n")
            fc_logger.info(self.page_msg["headline"] + self.page_msg["message"])

            # /* Clear the message. */
            self.page_msg = {}

    def handle_endgame_player(self, packet):
        self.end_game_player_packet = packet
        player_id = packet['player_id']
        self.game_results[player_id] = dict()
        self.game_results[player_id]['winner'] = packet['winner']
        self.game_results[player_id]['score'] = packet['score']
        self.game_results[player_id]['category_score'] = packet['category_score']
        self.ws_client.stop_ioloop()

    def handle_endgame_report(self, packet):
        self.end_game_report = packet

    def handle_play_music(self, packet):
        pass

    def handle_achievement_info(self, packet):
        pass

    def handle_team_name_info(self, packet):
        pass

    def handle_vote_new(self, packet):
        pass

    def handle_vote_update(self, packet):
        # /* TODO: implement */
        pass

    def handle_vote_remove(self, packet):
        # /* TODO: implement */
        pass

    def handle_vote_resolve(self, packet):
        # /* TODO: implement */
        pass

    def handle_edit_object_created(self, packet):
        # /* TODO: implement */
        pass

    def get_game_scores(self, game_scores):
        if game_scores is None:
            return None, None, None, None

        # start_turn = 0
        score_items = game_scores.split("\n")
        # Format: {player_id: {'name':PLAYER_NAME, 'start_turn': when the player is added in the game}}
        players = {}
        # Format: {turn_num: year_description}
        turns = {}
        # Format: {tag_id: tag_description}
        tags = {}
        # Format: {tag_name: {player_id: [scores]}}. The length of scores is the active turns of the player. It starts from the turn when the player is added and ends in the turn when the player is removed.
        evaluations = {}

        for score_item in score_items:
            scores = score_item.split(" ")
            if scores[0] == 'tag':
                ptag = int(scores[1])
                tags[ptag] = scores[2] + '-' + EVALUATION_TAGS[ptag]

            elif scores[0] == 'turn':
                pturn = int(scores[1])
                turn_name = " ".join(scores[3:])
                turns[pturn] = turn_name

            elif scores[0] == 'addplayer':
                player_id = int(scores[2])
                players[player_id] = {}
                player_name = " ".join(scores[3:])
                players[player_id]['name'] = player_name
                players[player_id]['start_turn'] = int(scores[1])

            elif scores[0] == 'data':
                ptag = int(scores[2])
                ptag_name = EVALUATION_TAGS[ptag]
                pplayer = int(scores[3])
                value = int(scores[4])

                if ptag_name not in evaluations:
                    evaluations[ptag_name] = dict()
                if pplayer not in evaluations[ptag_name]:
                    evaluations[ptag_name][pplayer] = []

                evaluations[ptag_name][pplayer].append(value)

        game_scores_folder = f"game_scores/{time.strftime('%Y-%m-%d-%H:%M:%S')}-{self.ws_client.client_port}"
        if not os.path.exists(game_scores_folder):
            os.makedirs(game_scores_folder)

            file_1 = os.path.join(game_scores_folder, 'players.json')
            with open(file_1, 'w') as f:
                json.dump(players, f)

            file_2 = os.path.join(game_scores_folder, 'evaluations.json')
            with open(file_2, 'w') as f:
                json.dump(evaluations, f)

        return players, tags, turns, evaluations
