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

"""
The server will send information about its settings. It is stored here.
You can look up a setting by its name or by its id number. */
"""


from typing import Dict

from civrealm.freeciv.connectivity.civ_connection import CivConnection

from civrealm.freeciv.utils.fc_types import TRUE, FALSE
from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.utils.base_action import NoActions

from civrealm.freeciv.game.info_states import GameState, ServerState


class OptionCtrl(CivPropController):
    """
        The "options" file handles actual "options", and also view options,
        message options, dialog/report settings, cma settings, server settings,
        and global worklists.
    """

    def __init__(self, ws_client: CivConnection):
        super().__init__(ws_client)
        self.server_settings: Dict[int, Dict] = {}
        self.prop_state = ServerState(self.server_settings)
        self.prop_actions = NoActions(ws_client)

        # /** Defaults for options normally on command line **/

        self.default_user_name = ""
        self.default_server_host = "localhost"
        # //var  default_server_port = DEFAULT_SOCK_PORT
        # //var default_metaserver = META_URL
        self.default_theme_name = "human"
        self.default_tileset_name = ""
        self.default_sound_set_name = "stdsounds"
        self.default_sound_plugin_name = ""

        self.sounds_enabled = True

        self.save_options_on_exit = TRUE
        self.fullscreen_mode = FALSE

        # /** Local Options: **/

        self.solid_color_behind_units = FALSE
        self.sound_bell_at_new_turn = FALSE
        self.smooth_move_unit_msec = 30
        self.smooth_center_slide_msec = 200
        self.do_combat_animation = TRUE
        self.ai_manual_turn_done = TRUE
        self.auto_center_on_unit = TRUE
        self.auto_center_on_combat = FALSE
        self.auto_center_each_turn = TRUE
        self.wakeup_focus = TRUE
        self.goto_into_unknown = TRUE
        self.center_when_popup_city = TRUE
        self.concise_city_production = FALSE
        self.auto_turn_done = FALSE
        self.meta_accelerators = TRUE
        self.ask_city_name = TRUE
        self.popup_new_cities = True
        # The player is interested in getting a pop up for a mere arrival.
        self.popup_actor_arrival = True
        self.keyboardless_goto = TRUE
        self.enable_cursor_changes = TRUE
        self.separate_unit_selection = FALSE
        self.unit_selection_clears_orders = TRUE
        self.highlight_our_names = "yellow"

        # /* This option is currently set by the client - not by the user. */
        self.update_city_text_in_refresh_tile = TRUE

        self.draw_city_outlines = TRUE
        self.draw_city_output = FALSE
        self.draw_map_grid = FALSE
        self.draw_city_names = TRUE
        self.draw_city_growth = TRUE
        self.draw_city_productions = FALSE
        self.draw_city_buycost = FALSE
        self.draw_city_traderoutes = FALSE
        self.draw_terrain = TRUE
        self.draw_coastline = FALSE
        self.draw_roads_rails = TRUE
        self.draw_irrigation = TRUE
        self.draw_mines = TRUE
        self.draw_fortress_airbase = TRUE
        self.draw_huts = TRUE
        self.draw_resources = TRUE
        self.draw_pollution = TRUE
        self.draw_cities = TRUE
        self.draw_units = TRUE
        self.draw_focus_unit = FALSE
        self.draw_fog_of_war = TRUE
        self.draw_borders = TRUE
        self.draw_full_citybar = TRUE
        self.draw_unit_shields = TRUE
        self.player_dlg_show_dead_players = TRUE
        self.reqtree_show_icons = TRUE
        self.reqtree_curved_lines = FALSE

        # /* gui-gtk-2.0 client specific options. */
        self.gui_gtk2_map_scrollbars = FALSE
        self.gui_gtk2_dialogs_on_top = TRUE
        self.gui_gtk2_show_task_icons = TRUE
        self.gui_gtk2_enable_tabs = TRUE
        self.gui_gtk2_better_fog = TRUE
        self.gui_gtk2_show_chat_message_time = FALSE
        self.gui_gtk2_split_bottom_notebook = FALSE
        self.gui_gtk2_new_messages_go_to_top = FALSE
        self.gui_gtk2_show_message_window_buttons = TRUE
        self.gui_gtk2_metaserver_tab_first = FALSE
        self.gui_gtk2_allied_chat_only = FALSE
        self.gui_gtk2_small_display_layout = FALSE

    def register_all_handlers(self):
        self.register_handler(164, "handle_server_setting_control")
        self.register_handler(165, "handle_server_setting_const")
        self.register_handler(166, "handle_server_setting_bool")
        self.register_handler(167, "handle_server_setting_int")
        self.register_handler(168, "handle_server_setting_str")
        self.register_handler(169, "handle_server_setting_enum")
        self.register_handler(170, "handle_server_setting_bitwise")

    def handle_server_setting_const(self, packet):
        """
        Receive general information about a server setting.
        Setting data type specific information comes in a follow up packet.
        """

        # The data type specific follow up packets needs to look up a setting by
        # its id. */
        self.server_settings[packet['id']] = packet

        # /* Make it possible to look up a setting by its name. */
        self.server_settings[packet['name']] = packet

    def handle_server_setting_int(self, packet):
        """
        Receive general information about a server setting.
        This is a follow up packet with data type specific information.
        """
        self.server_settings[packet['id']].update(packet)

    def handle_server_setting_enum(self, packet):
        """
        Receive general information about a server setting.
        This is a follow up packet with data type specific information.
        """
        self.server_settings[packet['id']].update(packet)

    def handle_server_setting_bitwise(self, packet):
        """
        Receive general information about a server setting.
        This is a follow up packet with data type specific information.
        """
        self.server_settings[packet['id']].update(packet)

    def handle_server_setting_bool(self, packet):
        """
        Receive general information about a server setting.
        This is a follow up packet with data type specific information.
        """
        self.server_settings[packet['id']].update(packet)

    def handle_server_setting_str(self, packet):
        """
        Receive general information about a server setting.
        This is a follow up packet with data type specific information.
        """
        self.server_settings[packet['id']].update(packet)

    def handle_server_setting_control(self, packet):
        # /* TODO: implement */
        pass
