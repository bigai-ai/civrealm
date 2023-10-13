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

from civrealm.freeciv.utils.base_state import PlainState, DictState


class GameState(PlainState):
    def __init__(self, scenario_info, calendar_info):
        super().__init__()
        self.scenario_info = scenario_info
        self.calendar_info = calendar_info

    def _update_state(self, pplayer):
        if pplayer != None:
            self._state.update(self.calendar_info)
            del self._state["calendar_fragment_name"]
            self._state.update(self.scenario_info)


class ServerState(DictState):
    def __init__(self, server_settings):
        super().__init__()
        self.server_settings = server_settings

    def _update_state(self, pplayer):
        if pplayer != None:
            pass
            # TODO: Treating fields that are lists to be treated later on
            # self._state.update(self.server_settings)


class RuleState(PlainState):
    def __init__(self, game_info):
        super().__init__()
        self.game_info = game_info

    def _update_state(self, pplayer):
        if pplayer != None:
            self._state.update(self.game_info)
            # TODO: Treating fields that are lists to be treated later on
            for key in ["global_advances", "granary_food_ini", "great_wonder_owners",
                        "min_city_center_output", "diplchance_initial_odds"]:
                del self._state[key]
