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

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.utils.fc_types import packet_spaceship_launch
from civrealm.freeciv.utils.base_action import Action

SSHIP_NONE = 0
SSHIP_STARTED = 1
SSHIP_LAUNCHED = 2
SSHIP_ARRIVED = 3

SSHIP_PLACE_STRUCTURAL = 0
SSHIP_PLACE_FUEL = 1
SSHIP_PLACE_PROPULSION = 2
SSHIP_PLACE_HABITATION = 3
SSHIP_PLACE_LIFE_SUPPORT = 4
SSHIP_PLACE_SOLAR_PANELS = 5


class SpaceCtrl(CivPropController):
    """ Controls spaceship information collection from server and state/actions towards spaceship"""

    def __init__(self, ws_client, rule_ctrl):
        super().__init__(ws_client)
        self.rule_ctrl = rule_ctrl
        self.spaceship_info = {}

    def register_all_handlers(self):
        self.register_handler(137, "handle_spaceship_info")

    def get_current_state(self, pplayer):
        spaceship = self.spaceship_info[pplayer['playerno']]
        state = {}
        info_keys = ['sship_state', 'success_rate', 'travel_time', 'components',
                     'energy_rate', 'support_rate', 'habitation', 'life_support',
                     'mass', 'modules', 'population', 'propulsion', 'solar_panels',
                     'structurals', 'launch_yer']

        for key in info_keys:
            if key in spaceship:
                state[key] = spaceship[key]
            else:
                state[key] = None

        state["spaceship_wins"] = self.rule_ctrl.game_info['victory_conditions'] != 0

        return spaceship

    def get_current_options(self, pplayer):
        return LaunchSpaceship(self.spaceship_info[pplayer['playerno']])

    def handle_spaceship_info(self, packet):
        """Stores spaceship info received from server"""
        self.spaceship_info[packet['player_num']] = packet

    @staticmethod
    def get_spaceship_state_text(state_id):
        """Returns text describing the current spaceship state"""
        if state_id == SSHIP_NONE:
            return "Not started"
        if state_id == SSHIP_STARTED:
            return "Started"
        if state_id == SSHIP_LAUNCHED:
            return "Launched"
        if state_id == SSHIP_ARRIVED:
            return "Arrived"


class LaunchSpaceship(Action):
    """ Launch Spaceship """

    def __init__(self, spaceship_playerinfo):
        super().__init__()
        self.spaceship_playerinfo = spaceship_playerinfo

    def is_action_valid(self):
        """ Launch is valid if spaceship is not started yet and there is any chance of success """
        return not (self.spaceship_playerinfo['sship_state'] != SSHIP_STARTED or
                    self.spaceship_playerinfo['success_rate'] == 0)

    def _action_packet(self):
        packet = {"pid": packet_spaceship_launch}
        return packet
