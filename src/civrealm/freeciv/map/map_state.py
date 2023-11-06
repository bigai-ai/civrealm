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

import gymnasium
import numpy as np
from BitVector import BitVector

from civrealm.freeciv.utils.base_state import PlainState
from civrealm.freeciv.utils.utility import byte_to_bit_array
from civrealm.freeciv.game.ruleset import RulesetCtrl
from civrealm.configs import fc_args


class MapState(PlainState):
    def __init__(self, rule_ctrl: RulesetCtrl):
        super().__init__()

        self.rule_ctrl = rule_ctrl
        self._extra_num = 0
        self._extra_num = 0
        self._tiles = []

        # Type: dict[str, np.ndarray]
        self._state = {}
        self._state['status'] = None
        self._state['terrain'] = None
        self._state['extras'] = None
        self._state['output'] = None
        self._state['tile_owner'] = None
        self._state['city_owner'] = None
        self._state['unit'] = None
        self._state['unit_owner'] = None

        self._before_first_update = True

    @property
    def tiles(self):
        return self._tiles

    def map_allocate(self, x_size, y_size):
        """
            Allocate space for map, and initialise the tiles.
            Uses current map.xsize and map.ysize.
            NOTE: generate_city_map_indices() and generate_map_indices() are not implemented in freeciv-web
        """
        # The "extras" variable in the ruleset controller stores duplicated extra types, keys are the extra names and extra ids.
        self._extra_num = len(self.rule_ctrl.extras)//2
        self._unit_type_num = len(self.rule_ctrl.unit_types)

        self._state['status'] = np.full((x_size, y_size), 0, dtype=np.ushort)
        self._state['terrain'] = np.full((x_size, y_size), 255, dtype=np.ushort)
        self._state['extras'] = np.full((x_size, y_size, self._extra_num), 0, dtype=np.bool_)
        self._state['output'] = np.full((x_size, y_size, 6), 0, dtype=np.ushort)
        self._state['tile_owner'] = np.full((x_size, y_size), 255, dtype=np.ushort)
        self._state['city_owner'] = np.full((x_size, y_size), 255, dtype=np.ushort)
        self._state['unit'] = np.full((x_size, y_size, self._unit_type_num), 0, dtype=np.ushort)
        self._state['unit_owner'] = np.full((x_size, y_size), 255, dtype=np.ushort)

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
        # Tile information will be updated no matter the tile is seen or not. The _state that will be passed to the agent is the state of the tiles that are seen.
        # Transform 16-bytes extra data to 128-bits data
        tile_packet['extras'] = BitVector(bitlist=byte_to_bit_array(tile_packet['extras']))

        tile_index = tile_packet['tile']
        assert self.tiles != None
        assert self.tiles[tile_index] != None

        x = self.tiles[tile_index]['x']
        y = self.tiles[tile_index]['y']

        self.tiles[tile_index].update(tile_packet)

        # Update the state for tiles according to the known state.
        self._state['status'][x, y] = tile_packet['known']
        if self._before_first_update and tile_packet['known'] == 1:
            # At the start of the game, the agent can seen some fogged tiles around the starting position.
            self._state['terrain'][x, y] = tile_packet['terrain']
            self._state['extras'][x, y, :] = tile_packet['extras'][:self._extra_num]

        if tile_packet['known'] == 2:
            # Tile state should be updated when the tile is seen.
            self._state['terrain'][x, y] = tile_packet['terrain']
            self._state['extras'][x, y, :] = tile_packet['extras'][:self._extra_num]
            self._state['tile_owner'][x, y] = tile_packet['owner']

            # Compute output for the tile without improvements.
            self._state['output'][x, y, :] = self.rule_ctrl.terrains[tile_packet['terrain']]['output']
            # Tiles with no resource will have resource value 128.
            if tile_packet['resource'] != 128:
                self._state['output'][x, y, :] += self.rule_ctrl.resources[tile_packet['resource']]['output']

    def encode_to_json(self):
        return dict([(key, self._state[key].to_list()) for key in self._state.keys()])

    def _update_state(self, pplayer, *args):
        if self._before_first_update:
            self._before_first_update = False

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
            self._state['unit'][unit_tile['x'], unit_tile['y'], unit['type']] += 1
            self._state['unit_owner'][unit_tile['x'], unit_tile['y']] = unit['owner']

        return

    def get_observation_space(self):
        map_shape = self._state['status'].shape
        self._observation_space = gymnasium.spaces.Dict({
            'status': gymnasium.spaces.Box(
                low=0, high=2, shape=map_shape, dtype=np.uint8),
            'terrain': gymnasium.spaces.Box(
                low=0, high=len(self.rule_ctrl.terrains) - 1,
                shape=map_shape, dtype=np.uint8),
            'extras': gymnasium.spaces.Box(
                low=0, high=1, shape=(*map_shape, self._extra_num),
                dtype=np.uint8),
            'output': gymnasium.spaces.Box(
                low=0, high=255, shape=(*map_shape, 6),
                dtype=np.uint8),
            'tile_owner': gymnasium.spaces.Box(
                low=0, high=255, shape=map_shape, dtype=np.uint8),
            'city_owner': gymnasium.spaces.Box(
                low=0, high=255, shape=map_shape, dtype=np.uint8),
            'unit': gymnasium.spaces.Box(
                low=0, high=255, shape=(*map_shape, self._unit_type_num),
                dtype=np.uint8),
            'unit_owner': gymnasium.spaces.Box(
                low=0, high=255, shape=map_shape, dtype=np.uint8), })
        return self._observation_space
