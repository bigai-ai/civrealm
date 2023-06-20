'''
**********************************************************************
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

***********************************************************************/
'''

from freecivbot.connectivity.base_controller import CivPropController
from freecivbot.game.info_states import GameState
from freecivbot.utils.base_action import NoActions

from freecivbot.utils.freeciv_logging import logger

# see handle_ruleset_extra, where EXTRA_* variables are defines dynamically.
EXTRA_NONE = -1
IDENTITY_NUMBER_ZERO = 0


class GameCtrl(CivPropController):
    def __init__(self, ws_client):
        CivPropController.__init__(self, ws_client)

        self.calendar_info = {}
        self.scenario_info = {}
        self.page_msg = {}

        self.prop_state = GameState(self.scenario_info, self.calendar_info)
        self.prop_actions = NoActions(ws_client)

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
        self.register_handler(238, "handle_achievement_info")
        self.register_handler(245, "handle_play_music")
        self.register_handler(260, "handle_info_text_message")

    def handle_scenario_info(self, packet):
        """
        Receive scenario information about the current game.

        The current game is a scenario game if scenario_info's 'is_scenario'
        field is set to true.
        """
        self.scenario_info.update(packet)

    def handle_scenario_description(self, packet):
        """Receive scenario description of the current scenario."""
        self.scenario_info['description'] = packet['description']

        # /* Show the updated game information. */
        # update_game_info_pregame()

    def handle_game_load(self, packet):
        # /* TODO: implement */
        pass

    def handle_calendar_info(self, packet):
        """Handle the calendar info packet."""
        self.calendar_info.update(packet)

    def handle_page_msg(self, packet):
        """Page_msg header handler."""
        # Message information
        self.page_msg['headline'] = packet['headline']
        self.page_msg['caption'] = packet['caption']
        self.page_msg['event'] = packet['event']

        # /* How many fragments to expect. */
        self.page_msg['missing_parts'] = packet['parts']

        # /* Will come in follow up packets. */
        self.page_msg['message'] = ""

    def handle_page_msg_part(self, packet):
        """Page_msg part handler."""
        # /* Add the new parts of the message content. */
        self.page_msg['message'] = self.page_msg['message'] + packet['lines']

        # /* Register that it was received. */
        self.page_msg['missing_parts'] -= 1
        if self.page_msg['missing_parts'] == 0:
            # /* This was the last part. */
            regxp = "/\n/gi"

            self.page_msg['message'] = self.page_msg['message'].replace(regxp, "<br>\n")
            logger.info(self.page_msg['headline'] + self.page_msg['message'])

            # /* Clear the message. */
            self.page_msg = {}

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

    def handle_info_text_message(self, packet):
        # /* TODO: implement */
        pass
