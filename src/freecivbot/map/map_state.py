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

from freecivbot.utils.base_state import PlainState
import json


class MapState(PlainState):
    def __init__(self, player_map):
        PlainState.__init__(self)
        self._state = player_map

    def json_struct(self):
        return dict([(key, self._state[key].to_list()) for key in self._state.keys()])

    def _update_state(self, pplayer):
        return self._state
