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
import numpy as np
from BitVector import BitVector

from freeciv_gym.freeciv.utils.base_state import PlainState
from freeciv_gym.freeciv.utils.utility import byte_to_bit_array
from freeciv_gym.freeciv.game.ruleset import RulesetCtrl


class MapState(PlainState):
    def __init__(self, rule_ctrl: RulesetCtrl):
        super().__init__()

        self.rule_ctrl = rule_ctrl
        self._tiles = []

        # Type: dict[str, np.ndarray]
        self._state = {}
        self._state['status'] = None
        self._state['terrain'] = None
        self._state['extras'] = None

    @property
    def tiles(self):
        return self._tiles

    @property
    def state(self):
        return self._state

    def map_allocate(self, x_size, y_size):
        """
            Allocate space for map, and initialise the tiles.
            Uses current map.xsize and map.ysize.
            NOTE: generate_city_map_indices() and generate_map_indices() are not implemented in freeciv-web
        """
        self._state['status'] = np.zeros((x_size, y_size), dtype=np.ubyte)
        self._state['terrain'] = np.zeros((x_size, y_size), dtype=np.ushort)

        for y in range(y_size):
            for x in range(x_size):
                tile = {}
                tile['index'] = x + y * x_size
                tile['x'] = x
                tile['y'] = y
                tile['height'] = 0
                tile = self.tile_init(tile)
                self.tiles.append(tile)

    @staticmethod
    def tile_init(tile):
        tile['known'] = None  # /* tile_known in C side */
        tile['seen'] = {}  # /* tile_seen in C side */
        tile['specials'] = []
        tile['resource'] = None
        tile['terrain'] = None
        tile['units'] = []
        tile['owner'] = None
        tile['claimer'] = None
        tile['worked'] = None
        tile['spec_sprite'] = None
        tile['goto_dir'] = None
        tile['nuke'] = 0
        return tile

    def update_tile(self, tile_packet, map_info):
        tile_packet['extras'] = BitVector(bitlist=byte_to_bit_array(tile_packet['extras']))
        if self.state['extras'] is None:
            extras_shape = (map_info['xsize'], map_info['ysize'], len(tile_packet['extras']))
            self.state['extras'] = np.zeros(extras_shape, dtype=np.bool_)

        ptile = tile_packet['tile']
        assert self.tiles != None
        assert self.tiles[ptile] != None

        self.tiles[ptile].update(tile_packet)
        self.state['status'][
            self.tiles[ptile]['x'],
            self.tiles[ptile]['y']] = tile_packet['known']
        self.state['terrain'][
            self.tiles[ptile]['x'],
            self.tiles[ptile]['y']] = tile_packet['terrain']
        self.state['extras'][
            self.tiles[ptile]['x'],
            self.tiles[ptile]['y'], :] = tile_packet['extras']

    def get_observation_space(self):
        map_shape = self._state['status'].shape
        extras_shape = self._state['extras'].shape
        self._observation_space = gymnasium.spaces.Dict({
            'status': gymnasium.spaces.Box(low=0, high=1, shape=map_shape, dtype=int),
            'terrain': gymnasium.spaces.Box(low=0, high=len(self.rule_ctrl.terrains), shape=map_shape, dtype=int),
            'extras': gymnasium.spaces.Box(low=0, high=1, shape=extras_shape, dtype=int),
        })
        return self._observation_space

    def encode_to_json(self):
        return dict([(key, self._state[key].to_list()) for key in self._state.keys()])

    def _update_state(self, pplayer):
        return
