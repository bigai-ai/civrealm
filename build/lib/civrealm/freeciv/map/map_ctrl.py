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


from math import floor, sqrt
import functools
import numpy as np

from civrealm.freeciv.connectivity.civ_connection import CivConnection
from civrealm.freeciv.game.ruleset import RulesetCtrl

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.utils.utility import FC_WRAP, sign
from civrealm.freeciv.utils.base_action import NoActions
from civrealm.freeciv.map.map_state import MapState
import civrealm.freeciv.map.map_const as map_const

from civrealm.freeciv.utils.freeciv_logging import fc_logger


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

    # Return the adjacent tiles of the given tile
    def get_adjacent_tiles(self, tile):
        tile_dict = {}
        for dir8 in map_const.DIR8_ORDER:
            adj_tile = self.mapstep(tile, dir8)
            if adj_tile is None:
                continue
            tile_dict[dir8] = adj_tile
        return tile_dict

    def city_tile(self, pcity):
        if pcity == None:
            return None
        return self.index_to_tile(pcity['tile'])

    def map_init_topology(self):
        self.map_info['valid_dirs'] = {}
        self.map_info['cardinal_dirs'] = {}

        self.map_info['num_valid_dirs'] = 0
        self.map_info['num_cardinal_dirs'] = 0

        for dir8 in range(map_const.DIR8_COUNT):
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
        if dir8 in [map_const.DIR8_SOUTHEAST, map_const.DIR8_NORTHWEST]:
            # /* These directions are invalid in hex topologies. */
            return not (self.topo_has_flag(map_const.TF_HEX) and not self.topo_has_flag(map_const.TF_ISO))
        elif dir8 in [map_const.DIR8_NORTHEAST, map_const.DIR8_SOUTHWEST]:
            # /* These directions are invalid in iso-hex topologies. */
            return not (self.topo_has_flag(map_const.TF_HEX) and self.topo_has_flag(map_const.TF_ISO))
        elif dir8 in [map_const.DIR8_NORTH, map_const.DIR8_EAST, map_const.DIR8_SOUTH, map_const.DIR8_WEST]:
            return True
        else:
            return False

    def is_cardinal_dir(self, dir8):
        if dir8 in [map_const.DIR8_NORTH, map_const.DIR8_EAST, map_const.DIR8_SOUTH, map_const.DIR8_WEST]:
            return True
        elif dir8 in [map_const.DIR8_SOUTHEAST, map_const.DIR8_NORTHWEST]:
            # /* These directions are cardinal in iso-hex topologies. */
            return self.topo_has_flag(map_const.TF_HEX) and self.topo_has_flag(map_const.TF_ISO)
        elif dir8 in [map_const.DIR8_NORTHEAST, map_const.DIR8_SOUTHWEST]:
            # /* These directions are cardinal in hexagonal topologies. */
            return self.topo_has_flag(map_const.TF_HEX) and not self.topo_has_flag(map_const.TF_ISO)
        else:
            return False

    def map_pos_to_tile(self, x, y):
        """ Return the tile for the given cartesian (map) position."""
        # Here assume the map has TF_WRAPX flag
        if y >= self.map_info['ysize'] or y < 0:
            return None
        if x >= self.map_info['xsize']:
            y -= 1
        elif (x < 0):
            y += 1
        return self.prop_state.tiles[x + y * self.map_info['xsize']]

    def is_out_of_map(self, x, y):
        wrap_has_flag = self.wrap_has_flag
        if wrap_has_flag(map_const.TF_WRAPX) and wrap_has_flag(map_const.TF_WRAPY):
            return False
        elif wrap_has_flag(map_const.TF_WRAPX):
            return y >= self.map_info['ysize'] or y < 0
        elif wrap_has_flag(map_const.TF_WRAPY):
            return x >= self.map_info['xsize'] or x < 0
        else:
            return x >= self.map_info['xsize'] or y >= self.map_info['ysize'] or x < 0 or y < 0

    def index_to_tile(self, index):
        """Return the tile for the given index."""
        # print(f"index: {1219}")
        # tile = self.prop_state.tiles[1219]
        # print(f"({tile['x']}, {tile['y']})")
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
        if self.topo_has_flag(map_const.TF_HEX):
            d = self.map_vector_to_distance(dx, dy)
            return d*d
        else:
            return dx*dx + dy*dy

    def map_vector_to_distance(self, dx, dy):
        """Return the squared distance for a map vector"""
        if self.topo_has_flag(map_const.TF_HEX):
            if (self.topo_has_flag(map_const.TF_ISO) and (dx*dy < 0)) or \
                    (not self.topo_has_flag(map_const.TF_ISO) and (dx*dy > 0)):
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
        if self.wrap_has_flag(map_const.TF_WRAPX):
            dx = min((dx + xsize) % xsize, (- dx + xsize) % xsize)

        dy = tile1['y'] - tile0['y']
        ysize = self.map_info['ysize']
        if self.wrap_has_flag(map_const.TF_WRAPY):
            dy = min((dy + ysize) % ysize, (- dy + ysize) % ysize)

        return dx, dy

    def map_distances(self, dx, dy):
        if self.wrap_has_flag(map_const.TF_WRAPX):
            half_world = floor(self.map_info['xsize'] / 2)
            dx = FC_WRAP(dx + half_world, self.map_info['xsize']) - half_world

        if self.wrap_has_flag(map_const.TF_WRAPY):
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

        return self.map_pos_to_tile(map_const.DIR_DX[dir8] + ptile['x'], map_const.DIR_DY[dir8] + ptile['y'])

    def get_direction_for_step(self, start_tile, end_tile):
        """
            Return the direction which is needed for a step on the map from
            start_tile to end_tile.
        """
        for dir8 in range(map_const.DIR8_LAST):
            test_tile = self.mapstep(start_tile, dir8)
            # if test_tile is None:
            #     continue

            if test_tile == end_tile:
                return dir8
        # DIR8_STAY is -1
        return map_const.DIR8_STAY

    @staticmethod
    def dir_get_name(dir8):
        """Return the debugging name of the direction."""
        try:
            return map_const.DIR8_NAMES[dir8]
        except KeyError:
            return '[undef]'

    @staticmethod
    def dir_cw(dir8):
        """Returns the next direction clock-wise."""
        try:
            return map_const.DIR8_CW[dir8]
        except KeyError:
            return -1

    @staticmethod
    def dir_ccw(dir8):
        """Returns the next direction counter clock-wise."""
        try:
            return map_const.DIR8_CCW[dir8]
        except KeyError:
            return -1

    def clear_goto_tiles(self):
        """Removes goto lines and clears goto tiles."""

        for x in range(self.map_info['xsize']):
            for y in range(self.map_info['ysize']):
                self.prop_state.tiles[x + y * self.map_info['xsize']]['goto_dir'] = None

    def handle_tile_info(self, packet):
        self.prop_state.update_tile(packet)

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

    def __init__(self, radius_sq: int, map_ctrl: MapCtrl):
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
        if wrap_has_flag(map_const.TF_WRAPX) and wrap_has_flag(map_const.TF_WRAPY):
            return self.maps[0]

        r = self.radius
        if wrap_has_flag(map_const.TF_WRAPX):  # Cylinder with N-S axis
            d = self.delta_tile_helper(y, r, self.map_ctrl.map_info['ysize'])
            if d[2] not in self.maps:
                self.maps[d[2]] = self.build_city_tile_map_with_limits(-r, r, d[0], d[1])
            return self.maps[d[2]]

        if wrap_has_flag(map_const.TF_WRAPY):  # Cylinder with E-W axis
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
            return None
        return a_map[city_tile_map_index]


if __name__ == '__main__':
    fc_logger.info(MapCtrl.dir_get_name(7))
    fc_logger.info(MapCtrl.dir_get_name(MapCtrl.dir_ccw(7)))
    fc_logger.info(MapCtrl.dir_get_name(MapCtrl.dir_cw(7)))
