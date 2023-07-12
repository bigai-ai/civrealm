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

from math import floor, sqrt
import functools
import numpy as np
from BitVector import BitVector

from freeciv_gym.freeciv.utils.base_controller import CivPropController
from freeciv_gym.freeciv.utils.utility import FC_WRAP, byte_to_bit_array, sign
from freeciv_gym.freeciv.utils.base_action import NoActions
from freeciv_gym.freeciv.map.map_state import MapState
from freeciv_gym.freeciv.game.ruleset import RulesetCtrl

from freeciv_gym.freeciv.connectivity.civ_connection import CivConnection

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger


DIR8_STAY = -1
DIR8_NORTHWEST = 0
DIR8_NORTH = 1
DIR8_NORTHEAST = 2
DIR8_WEST = 3
DIR8_EAST = 4
DIR8_SOUTHWEST = 5
DIR8_SOUTH = 6
DIR8_SOUTHEAST = 7
DIR8_LAST = 8
DIR8_COUNT = DIR8_LAST

DIR8_NAMES = ['NW', 'N', 'NE', 'W', 'E', 'SW', 'S', 'SE']

DIR8_ORDER = [DIR8_NORTHWEST, DIR8_NORTH, DIR8_NORTHEAST, DIR8_WEST,
              DIR8_EAST, DIR8_SOUTHWEST, DIR8_SOUTH, DIR8_SOUTHEAST]

# Dict for the next direction clock-wise
DIR8_CW = {DIR8_NORTHWEST: DIR8_NORTH,
           DIR8_NORTH: DIR8_NORTHEAST,
           DIR8_NORTHEAST: DIR8_EAST,
           DIR8_EAST: DIR8_SOUTHEAST,
           DIR8_SOUTHEAST: DIR8_SOUTH,
           DIR8_SOUTH: DIR8_SOUTHWEST,
           DIR8_SOUTHWEST: DIR8_WEST,
           DIR8_WEST: DIR8_NORTHWEST}

# Dict for the next direction counter clock-wise
DIR8_CCW = {DIR8_NORTHWEST: DIR8_WEST,
            DIR8_NORTH: DIR8_NORTHWEST,
            DIR8_NORTHEAST: DIR8_NORTH,
            DIR8_EAST: DIR8_NORTHEAST,
            DIR8_SOUTHEAST: DIR8_EAST,
            DIR8_SOUTH: DIR8_SOUTHEAST,
            DIR8_SOUTHWEST: DIR8_SOUTH,
            DIR8_WEST: DIR8_SOUTHWEST}

TF_WRAPX = 1
TF_WRAPY = 2
TF_ISO = 4
TF_HEX = 8

"""used to compute neighboring tiles.
 *
 * using
 *   x1 = x + DIR_DX[dir]
 *   y1 = y + DIR_DY[dir]
 * will give you the tile as shown below.
 *   -------
 *   |0|1|2|
 *   |-+-+-|
 *   |3| |4|
 *   |-+-+-|
 *   |5|6|7|
 *   -------
 * Note that you must normalize x1 and y1 yourself.
"""

DIR_DX = [-1, 0, 1, -1, 1, -1, 0, 1]
DIR_DY = [-1, -1, -1, 0, 0, 1, 1, 1]


class MapCtrl(CivPropController):
    def __init__(self, ws_client: CivConnection, rule_ctrl: RulesetCtrl):
        super().__init__(ws_client)

        self.map_info = {}

        self.prop_state = MapState(rule_ctrl)
        self.prop_actions = NoActions(ws_client)

    def register_all_handlers(self):
        self.register_handler(15, 'handle_tile_info')
        self.register_handler(17, 'handle_map_info')
        self.register_handler(253, 'handle_set_topology')

    def __repr__(self):
        return 'MapCtrl __repr__() unimplemented.'

    def topo_has_flag(self, flag):
        return ((self.map_info['topology_id'] & (flag)) != 0)

    def wrap_has_flag(self, flag):
        return ((self.map_info['wrap_id'] & (flag)) != 0)

    def city_tile(self, pcity):
        if pcity == None:
            return None
        return self.index_to_tile(pcity['tile'])

    def map_init_topology(self):
        self.map_info['valid_dirs'] = {}
        self.map_info['cardinal_dirs'] = {}

        self.map_info['num_valid_dirs'] = 0
        self.map_info['num_cardinal_dirs'] = 0

        for dir8 in range(DIR8_COUNT):
            if self.is_valid_dir(dir8):
                self.map_info['valid_dirs'][self.map_info['num_valid_dirs']] = dir8
                self.map_info['num_valid_dirs'] += 1
            if self.is_cardinal_dir(dir8):
                self.map_info['cardinal_dirs'][self.map_info['num_cardinal_dirs']] = dir8
                self.map_info['num_cardinal_dirs'] += 1

    def set_tile_worked(self, packet):
        if packet['tile'] < len(self.prop_state.tiles) and self.prop_state.tiles[packet['tile']] != None:
            self.prop_state.tiles[packet['tile']]['worked'] = packet['id']

    def is_valid_dir(self, dir8):
        if dir8 in [DIR8_SOUTHEAST, DIR8_NORTHWEST]:
            # /* These directions are invalid in hex topologies. */
            return not (self.topo_has_flag(TF_HEX) and not self.topo_has_flag(TF_ISO))
        elif dir8 in [DIR8_NORTHEAST, DIR8_SOUTHWEST]:
            # /* These directions are invalid in iso-hex topologies. */
            return not (self.topo_has_flag(TF_HEX) and self.topo_has_flag(TF_ISO))
        elif dir8 in [DIR8_NORTH, DIR8_EAST, DIR8_SOUTH, DIR8_WEST]:
            return True
        else:
            return False

    def is_cardinal_dir(self, dir8):
        if dir8 in [DIR8_NORTH, DIR8_EAST, DIR8_SOUTH, DIR8_WEST]:
            return True
        elif dir8 in [DIR8_SOUTHEAST, DIR8_NORTHWEST]:
            # /* These directions are cardinal in iso-hex topologies. */
            return self.topo_has_flag(TF_HEX) and self.topo_has_flag(TF_ISO)
        elif dir8 in [DIR8_NORTHEAST, DIR8_SOUTHWEST]:
            # /* These directions are cardinal in hexagonal topologies. */
            return self.topo_has_flag(TF_HEX) and not self.topo_has_flag(TF_ISO)
        else:
            return False

    def map_pos_to_tile(self, x, y):
        """ Return the tile for the given cartesian (map) position."""
        if x >= self.map_info['xsize']:
            y -= 1
        elif (x < 0):
            y += 1
        return self.prop_state.tiles[x + y * self.map_info['xsize']]

    def index_to_tile(self, index):
        """Return the tile for the given index."""
        return self.prop_state.tiles[index]

    def NATIVE_TO_MAP_POS(self, nat_x, nat_y):
        """Obscure math.  See explanation in doc/HACKING."""
        pmap_x = floor(((nat_y) + ((nat_y) & 1)) / 2 + (nat_x))
        pmap_y = floor(nat_y - pmap_x + self.map_info['xsize'])
        return {'map_x': pmap_x, 'map_y': pmap_y}

    def MAP_TO_NATIVE_POS(self, map_x, map_y):
        pnat_y = floor(map_x + map_y - self.map_info['xsize'])
        pnat_x = floor((2 * map_x - pnat_y - (pnat_y & 1)) / 2)
        return {'nat_y': pnat_y, 'nat_x': pnat_x}

    def NATURAL_TO_MAP_POS(self, nat_x, nat_y):
        pmap_x = floor(((nat_y) + (nat_x)) / 2)
        pmap_y = floor(nat_y - pmap_x + self.map_info['xsize'])
        return {'map_x': pmap_x, 'map_y': pmap_y}

    def MAP_TO_NATURAL_POS(self, map_x, map_y):
        pnat_y = floor((map_x) + (map_y) - self.map_info['xsize'])
        pnat_x = floor(2 * (map_x) - pnat_y)

        return {'nat_y': pnat_y, 'nat_x': pnat_x}

    def map_vector_to_sq_distance(self, dx, dy):
        """Return the squared distance for a map vector"""
        if self.topo_has_flag(TF_HEX):
            d = self.map_vector_to_distance(dx, dy)
            return d*d
        else:
            return dx*dx + dy*dy

    def map_vector_to_distance(self, dx, dy):
        """Return the squared distance for a map vector"""
        if self.topo_has_flag(TF_HEX):
            if (self.topo_has_flag(TF_ISO) and (dx*dy < 0)) or \
                    (not self.topo_has_flag(TF_ISO) and (dx*dy > 0)):
                return abs(dx) + abs(dy)
            else:
                return max(abs(dx), abs(dy))
        else:
            return max(abs(dx), abs(dy))

    def map_distance_vector(self, tile0, tile1):
        """
            A more straightforward way to compute distance vector compared with the below one
        """
        dx = tile1['x'] - tile0['x']
        xsize = self.map_info['xsize']
        if self.wrap_has_flag(TF_WRAPX):
            dx = min((dx + xsize) % xsize, (- dx + xsize) % xsize)

        dy = tile1['y'] - tile0['y']
        ysize = self.map_info['ysize']
        if self.wrap_has_flag(TF_WRAPY):
            dy = min((dy + ysize) % ysize, (- dy + ysize) % ysize)

        return dx, dy

    def map_distances(self, dx, dy):
        if self.wrap_has_flag(TF_WRAPX):
            half_world = floor(self.map_info['xsize'] / 2)
            dx = FC_WRAP(dx + half_world, self.map_info['xsize']) - half_world

        if self.wrap_has_flag(TF_WRAPY):
            half_world = floor(self.map_info['ysize'] / 2)
            dx = FC_WRAP(dy + half_world, self.map_info['ysize']) - half_world

        return [dx, dy]

    def mapstep(self, ptile, dir8):
        """
          Step from the given tile in the given direction.  The new tile is returned,
          or None if the direction is invalid or leads off the map.
        """
        if not self.is_valid_dir(dir8):
            return None

        return self.map_pos_to_tile(DIR_DX[dir8] + ptile['x'], DIR_DY[dir8] + ptile['y'])

    def get_direction_for_step(self, start_tile, end_tile):
        """
            Return the direction which is needed for a step on the map from
            start_tile to end_tile.
        """
        for dir8 in range(DIR8_LAST):
            test_tile = self.mapstep(start_tile, dir8)

            if test_tile == end_tile:
                return dir8

        return -1

    @staticmethod
    def dir_get_name(dir8):
        """Return the debugging name of the direction."""
        try:
            return DIR8_NAMES[dir8]
        except KeyError:
            return '[undef]'

    @staticmethod
    def dir_cw(dir8):
        """Returns the next direction clock-wise."""
        try:
            return DIR8_CW[dir8]
        except KeyError:
            return -1

    @staticmethod
    def dir_ccw(dir8):
        """Returns the next direction counter clock-wise."""
        try:
            return DIR8_CCW[dir8]
        except KeyError:
            return -1

    def clear_goto_tiles(self):
        """Removes goto lines and clears goto tiles."""

        for x in range(self.map_info['xsize']):
            for y in range(self.map_info['ysize']):
                self.prop_state.tiles[x + y * self.map_info['xsize']]['goto_dir'] = None

    def handle_tile_info(self, packet):
        packet['extras'] = BitVector(bitlist=byte_to_bit_array(packet['extras']))
        if self.prop_state.state['extras'] is None:
            extras_shape = (self.map_info['xsize'], self.map_info['ysize'], len(packet['extras']))
            self.prop_state.state['extras'] = np.zeros(extras_shape, dtype=np.bool_)

        ptile = packet['tile']
        assert self.prop_state.tiles != None
        assert self.prop_state.tiles[ptile] != None

        self.prop_state.tiles[ptile].update(packet)
        self.prop_state.state['status'][
            self.prop_state.tiles[ptile]['x'],
            self.prop_state.tiles[ptile]['y']] = packet['known']
        self.prop_state.state['terrain'][
            self.prop_state.tiles[ptile]['x'],
            self.prop_state.tiles[ptile]['y']] = packet['terrain']
        self.prop_state.state['extras'][
            self.prop_state.tiles[ptile]['x'],
            self.prop_state.tiles[ptile]['y'],
            :] = packet['extras']

    def handle_set_topology(self, packet):
        """
        Server requested topology change.
        # NOTE: currently not planned to be implemented
        """
        pass

    def handle_map_info(self, packet):
        # NOTE: init_client_goto(), generate_citydlg_dimensions(), calculate_overview_dimensions() are not implemented in freeciv-web
        self.map_info = packet
        self.map_init_topology()
        self.prop_state.map_allocate(self.map_info['xsize'], self.map_info['ysize'])
        self.map_info['startpos_table'] = {}


def get_dist(a, b):
    d = a[2] - b[2]
    if (d != 0):
        return sign(d)
    d = a[0] - b[0]
    if (d != 0):
        return sign(d)
    return sign(a[1] - b[1])


def dxy_to_center_index(dx, dy, r):
    """ Returns an index for a flat array containing x,y data.
        dx,dy are displacements from the center, r is the "radius" of the data
        in the array. That is, for r=0, the array would just have the center;
        for r=1 it'd be (-1,-1), (-1,0), (-1,1), (0,-1), (0,0), etc.
        There's no check for coherence.
    """
    return (dx + r) * (2 * r + 1) + dy + r


class CityTileMap():
    """Builds city_tile_map info for a given squared city radius."""

    def __init__(self, radius_sq, map_ctrl: MapCtrl):
        self.radius_sq = radius_sq
        self.radius = None
        self.base_sorted = None
        self.maps = None
        self.map_ctrl = map_ctrl

    def update_map(self, new_radius):
        if self.maps is None or self.radius_sq < new_radius:
            r = int(floor(sqrt(new_radius)))
            vectors = []

            for dx in range(-r, r+1):
                for dy in range(-r, r+1):
                    d_sq = self.map_ctrl.map_vector_to_sq_distance(dx, dy)

                    if d_sq <= new_radius:
                        vectors.append([dx, dy, d_sq, dxy_to_center_index(dx, dy, r)])

            vectors = sorted(vectors, key=functools.cmp_to_key(get_dist))
            base_map = [None for _ in range((2*r+1)*(2*r+1))]

            for vnum, vec in enumerate(vectors):
                base_map[vec[3]] = vnum

            # logger.info(base_map)
            self.radius_sq = new_radius
            self.radius = r
            self.base_sorted = vectors
            # change self.maps to dict type to support adding map based on position
            # self.maps = [base_map]
            self.maps = {}
            self.maps[0] = base_map

    @staticmethod
    def delta_tile_helper(pos, r, size):
        """ Helper for get_city_tile_map_for_pos.
            From position, radius and size, returns an array with delta_min,
            delta_max and clipped tile_map index.
        """
        d_min = -pos
        d_max = (size-1) - pos
        i = 0
        if d_min > -r:
            i = r + d_min
        elif d_max < r:
            i = 2*r - d_max
        return [d_min, d_max, i]

    def build_city_tile_map_with_limits(self, dx_min, dx_max, dy_min, dy_max):
        """Builds the city_tile_map with the given delta limits.
              Helper for get_city_tile_map_for_pos."""
        v = self.base_sorted
        vl = len(v)
        clipped_map = [-1 for _ in range(vl*100)]
        max_ind = 0
        ind = 0
        for vi in range(vl):
            tile_data = v[vi]
            if dx_min <= tile_data[0] <= dx_max and dy_min <= tile_data[1] <= dy_max:
                clipped_map[tile_data[3]] = ind
                if max_ind < tile_data[3]:
                    max_ind = tile_data[3]
                ind += 1
        assert (max_ind+1 <= vl*100)  # make sure vl*100 is enough
        return clipped_map[:max_ind+1]

    def get_city_tile_map_for_pos(self, x, y):
        """Returns the map of position from city center to index in city_info."""
        wrap_has_flag = self.map_ctrl.wrap_has_flag
        if wrap_has_flag(TF_WRAPX) and wrap_has_flag(TF_WRAPY):
            return self.maps[0]

        r = self.radius
        if wrap_has_flag(TF_WRAPX):  # Cylinder with N-S axis
            d = self.delta_tile_helper(y, r, self.map_ctrl.map_info['ysize'])
            if d[2] not in self.maps:
                self.maps[d[2]] = self.build_city_tile_map_with_limits(-r, r, d[0], d[1])
            return self.maps[d[2]]

        if wrap_has_flag(TF_WRAPY):  # Cylinder with E-W axis
            d = self.delta_tile_helper(x, r, self.map_ctrl.map_info['xsize'])
            if d[2] not in self.maps:
                self.maps[d[2]] = self.build_city_tile_map_with_limits(d[0], d[1], -r, r)
            return self.maps[d[2]]

        # Flat
        dx = self.delta_tile_helper(x, r, self.map_ctrl.map_info['xsize'])
        dy = self.delta_tile_helper(y, r, self.map_ctrl.map_info['ysize'])
        map_i = (2*r + 1) * dx[2] + dy[2]
        if map_i not in self.maps:
            m = self.build_city_tile_map_with_limits(dx[0], dx[1], dy[0], dy[1])
            self.maps[map_i] = m
        return self.maps[map_i]

    def get_city_dxy_to_index(self, dx, dy, city_tile):
        """
          Converts from coordinate offset from city center (dx, dy),
          to index.
        """
        city_tile_map_index = dxy_to_center_index(dx, dy, self.radius)
        a_map = self.get_city_tile_map_for_pos(city_tile['x'], city_tile['y'])
        # logger.info('get_city_dxy_to_index')
        # logger.info(len(a_map))
        # logger.info(a_map)
        # logger.info(city_tile_map_index)
        # logger.info('*'*10)
        if city_tile_map_index >= len(a_map):
            fc_logger.info('dx: {}, dy: {}, radius: {}, city_tile[x]: {}, city_tile[y]: {}'.format(
                dx, dy, self.radius, city_tile['x'], city_tile['y']))
            fc_logger.info('city_tile_map_index: {}, a_map length: {}'.format(city_tile_map_index, len(a_map)))
        return a_map[city_tile_map_index]


if __name__ == '__main__':
    fc_logger.info(MapCtrl.dir_get_name(7))
    fc_logger.info(MapCtrl.dir_get_name(MapCtrl.dir_ccw(7)))
    fc_logger.info(MapCtrl.dir_get_name(MapCtrl.dir_cw(7)))
