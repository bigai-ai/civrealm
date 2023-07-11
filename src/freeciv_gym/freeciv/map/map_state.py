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

import gymnasium

from freeciv_gym.freeciv.utils.base_state import PlainState


class MapState(PlainState):
    def __init__(self, player_map):
        super().__init__()
        self._state = player_map

    def get_observation_space(self):
        map_shape = self._state['status'].shape
        extras_shape = self._state['status'].shape
        # FIXME: confirm the range of the observation space
        self._observation_space = gymnasium.spaces.Dict({
            'status': gymnasium.spaces.Box(low=0, high=1, shape=map_shape, dtype=int),
            'terrain': gymnasium.spaces.Box(low=0, high=12, shape=map_shape, dtype=int),
            'extras': gymnasium.spaces.Box(low=0, high=1, shape=extras_shape, dtype=int),
        })
        return self._observation_space

    def encode_to_json(self):
        return dict([(key, self._state[key].to_list()) for key in self._state.keys()])

    def _update_state(self, pplayer):
        return self._state
