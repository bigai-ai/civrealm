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

import gymnasium
import numpy as np
from BitVector import BitVector

from freeciv_gym.freeciv.utils.type_const import UNIT_TYPES
from freeciv_gym.freeciv.utils.base_state import PlainState
from freeciv_gym.freeciv.utils.utility import byte_to_bit_array
from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
from freeciv_gym.configs import fc_args


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
        self._state['tile_owner'] = None
        self._state['city_owner'] = None
        self._state['unit'] = None
        self._state['unit_owner'] = None

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
        self._state['tile_owner'] = np.zeros((x_size, y_size), dtype=np.ushort)
        self._state['city_owner'] = np.zeros((x_size, y_size), dtype=np.ushort)
        self._state['unit'] = np.zeros((x_size, y_size, len(UNIT_TYPES)), dtype=np.ushort)
        self._state['unit_owner'] = np.zeros((x_size, y_size), dtype=np.ushort)

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

    def update_tile(self, tile_packet):
        # Transform 16-bytes extra data to 128-bits data
        tile_packet['extras'] = BitVector(bitlist=byte_to_bit_array(tile_packet['extras']))
        if self.state['extras'] is None:
            x_size, y_size = self._state['status'].shape
            extras_shape = (x_size, y_size, len(tile_packet['extras']))
            self.state['extras'] = np.zeros(extras_shape, dtype=np.bool_)

        tile_index = tile_packet['tile']
        assert self.tiles != None
        assert self.tiles[tile_index] != None

        self.tiles[tile_index].update(tile_packet)
        self.state['status'][
            self.tiles[tile_index]['x'],
            self.tiles[tile_index]['y']] = tile_packet['known']
        self.state['terrain'][
            self.tiles[tile_index]['x'],
            self.tiles[tile_index]['y']] = tile_packet['terrain']
        self.state['extras'][
            self.tiles[tile_index]['x'],
            self.tiles[tile_index]['y'], :] = tile_packet['extras']
        self.state['tile_owner'][
            self.tiles[tile_index]['x'],
            self.tiles[tile_index]['y']] = tile_packet['owner']

    def get_observation_space(self):
        map_shape = self._state['status'].shape
        extras_shape = self._state['extras'].shape
        self._observation_space = gymnasium.spaces.Dict({
            'status': gymnasium.spaces.Box(low=0, high=1, shape=map_shape, dtype=int),
            'terrain': gymnasium.spaces.Box(low=0, high=len(self.rule_ctrl.terrains)-1, shape=map_shape, dtype=int),
            'extras': gymnasium.spaces.Box(low=0, high=1, shape=extras_shape, dtype=int),
            'tile_owner': gymnasium.spaces.Box(low=0, high=255, shape=map_shape, dtype=int),
            'city_owner': gymnasium.spaces.Box(low=0, high=255, shape=map_shape, dtype=int),
            'unit': gymnasium.spaces.Box(low=0, high=1, shape=(*map_shape, len(UNIT_TYPES)), dtype=int),
            'unit_owner': gymnasium.spaces.Box(low=0, high=255, shape=map_shape, dtype=int),
        })
        return self._observation_space

    def encode_to_json(self):
        return dict([(key, self._state[key].to_list()) for key in self._state.keys()])

    def _update_state(self, pplayer, *args):
        cities = args[0]
        units = args[1]

        self._state['city_owner'].fill(255)
        self._state['unit'].fill(0)
        self._state['unit_owner'].fill(255)

        for _, city in cities.items():
            city_tile = self.tiles[city['tile']]
            self._state['city_owner'][city_tile['x'], city_tile['y']] = city_tile['owner']

        for _, unit in units.items():
            unit_tile = self.tiles[unit['tile']]
            self._state['unit'][unit_tile['x'], unit_tile['y'], unit['type']] = 1
            self._state['unit_owner'][unit_tile['x'], unit_tile['y']] = unit['owner']

        return
