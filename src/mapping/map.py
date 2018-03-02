'''
    Freeciv-web - the web version of Freeciv. http://play.freeciv.org/
    Copyright (C) 2009-2015  The Freeciv-web project

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from connectivity.Basehandler import CivEvtHandler
from math import floor
from utils.utility import FC_WRAP, byte_to_bit_array
from BitVector import BitVector
from mapping.tile import TileState, TILE_UNKNOWN, TILE_KNOWN_SEEN
import numpy as np

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

DIR8_NAMES = ["NW", "N", "NE", "W", "E", "SW", "S", "SE"]

DIR8_ORDER = [DIR8_NORTH, DIR8_NORTHEAST, DIR8_EAST, DIR8_SOUTHEAST,
              DIR8_SOUTH, DIR8_SOUTHWEST, DIR8_WEST, DIR8_NORTHWEST]

DIR8_CW = dict(zip(DIR8_ORDER, DIR8_ORDER[1:] + [DIR8_ORDER[0]]))
DIR8_CCW = dict(zip(DIR8_ORDER, [DIR8_ORDER[-1]] + DIR8_ORDER[:-1]))

TF_WRAPX = 1
TF_WRAPY = 2
TF_ISO = 4
TF_HEX = 8

T_NONE = 0 #/* A special flag meaning no terrain type. */
T_UNKNOWN = 0 #/* An unknown terrain. */

T_FIRST = 0#/* The first terrain value. */

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

DIR_DX = [ -1, 0, 1, -1, 1, -1, 0, 1 ]
DIR_DY = [ -1, -1, -1, 0, 0, 1, 1, 1 ]

class MapCtrl(CivEvtHandler):
    def __init__(self, ws_client, rule_ctrl):
        CivEvtHandler.__init__(self, ws_client)
        self.map = {}
        self.tiles = {}
        self.rule_ctrl = rule_ctrl
        self.register_handler(15, "handle_tile_info")
        self.register_handler(17, "handle_map_info")
        self.register_handler(253, "handle_set_topology")

    def topo_has_flag(self, flag):
        return ((self.map['topology_id'] & (flag)) != 0)

    def city_tile(self, pcity):
        if pcity == None:
            return None

        return self.index_to_tile(pcity['tile'])

    def map_allocate(self):
        """
            Allocate space for mapping, and initialise the tiles.
            Uses current mapping.xsize and mapping.ysize.
        """

        self.tiles = {}
        """
        Note this use of whole_map_iterate may be a bit sketchy, since the
        tile values (ptile->index, etc.) haven't been set yet.  It might be
        better to do a manual loop here.
        """

        for x in range(self.map['xsize']):
            for y in range(self.map['ysize']):

                tile = {}
                tile['index'] = x + y * self.map['xsize']
                tile['x'] = x
                tile['y'] = y
                tile['height'] = 0
                tile = self.tile_init(tile)
                self.tiles[tile['index']] = tile

        #/* TODO: generate_city_map_indices() */
        #/* TODO: generate_map_indices() */

        self.map['startpos_table'] = {}
        #init_overview()

    def tile_init(self, tile):
        tile['known'] = None  #/* tile_known in C side */
        tile['seen'] = {}     #/* tile_seen in C side */
        tile['specials'] = []
        tile['resource'] = None
        tile['terrain'] = T_UNKNOWN
        tile['units'] = []
        tile['owner'] = None
        tile['claimer'] = None
        tile['worked'] = None
        tile['spec_sprite'] = None
        tile['goto_dir'] = None
        tile['nuke'] = 0
        return tile

    def map_init_topology(self, set_sizes):
        self.map["valid_dirs"] = {}
        self.map["cardinal_dirs"] = {}

        self.map["num_valid_dirs"] = 0
        self.map["num_cardinal_dirs"] = 0

        for dir8 in range(DIR8_COUNT):
            if self.is_valid_dir(dir8):
                self.map["valid_dirs"] [self.map["num_valid_dirs"]] = dir8
                self.map["num_valid_dirs"] += 1
            if self.is_cardinal_dir(dir8):
                self.map["cardinal_dirs"][self.map["num_cardinal_dirs"]] = dir8
                self.map["num_cardinal_dirs"] += 1

    def set_tile_worked(self, packet):
        if packet['tile'] in self.tiles:
            self.tiles[packet['tile']]['worked'] = packet['id']

    def is_valid_dir(self, dir8):
        if dir8 in [DIR8_SOUTHEAST, DIR8_NORTHWEST]:
            #/* These directions are invalid in hex topologies. */
            return not (self.topo_has_flag(TF_HEX) and not self.topo_has_flag(TF_ISO))
        elif dir8 in [DIR8_NORTHEAST, DIR8_SOUTHWEST]:
            #/* These directions are invalid in iso-hex topologies. */
            return not (self.topo_has_flag(TF_HEX) and self.topo_has_flag(TF_ISO))
        elif dir8 in [DIR8_NORTH, DIR8_EAST, DIR8_SOUTH, DIR8_WEST]:
            return True
        else:
            return False

    def is_cardinal_dir(self, dir8):
        if dir8 in [DIR8_NORTH, DIR8_EAST, DIR8_SOUTH, DIR8_WEST]:
            return True
        elif dir8 in [DIR8_SOUTHEAST, DIR8_NORTHWEST]:
            #/* These directions are cardinal in iso-hex topologies. */
            return self.topo_has_flag(TF_HEX) and self.topo_has_flag(TF_ISO)
        elif dir8 in [DIR8_NORTHEAST, DIR8_SOUTHWEST]:
            #/* These directions are cardinal in hexagonal topologies. */
            return self.topo_has_flag(TF_HEX) and not self.topo_has_flag(TF_ISO)
        else:
            return False

    def map_pos_to_tile(self, x, y):
        """ Return the tile for the given cartesian (mapping) position."""
        if x >= self.map['xsize']:
            y -= 1
        elif (x < 0):
            y += 1
        return self.tiles[x + y * self.map['xsize']]

    def index_to_tile(self, index):
        """Return the tile for the given index."""
        return self.tiles[index]


    def NATIVE_TO_MAP_POS(self, nat_x, nat_y):
        """Obscure math.  See explanation in doc/HACKING."""
        pmap_x = floor(((nat_y) + ((nat_y) & 1)) / 2 + (nat_x))
        pmap_y = floor(nat_y - pmap_x + self.map['xsize'])
        return {'map_x' : pmap_x, 'map_y' : pmap_y}

    def MAP_TO_NATIVE_POS(self, map_x, map_y):
        pnat_y = floor(map_x + map_y - self.map['xsize'])
        pnat_x = floor((2 * map_x - pnat_y - (pnat_y & 1)) / 2)
        return {'nat_y': pnat_y, 'nat_x': pnat_x}


    def NATURAL_TO_MAP_POS(self, nat_x, nat_y):
        pmap_x = floor(((nat_y) + (nat_x)) / 2)
        pmap_y = floor(nat_y - pmap_x + self.map['xsize'])
        return {'map_x' : pmap_x, 'map_y' : pmap_y}

    def MAP_TO_NATURAL_POS(self, map_x, map_y):
        pnat_y = floor((map_x) + (map_y) - self.map['xsize'])
        pnat_x = floor(2 * (map_x) - pnat_y)

        return {'nat_y' : pnat_y, 'nat_x' : pnat_x}

    def map_vector_to_sq_distance(self, dx, dy):
        """Return the squared distance for a mapping vector"""
        if self.topo_has_flag(TF_HEX):
            d = self.map_vector_to_distance(dx, dy)
            return d*d
        else:
            return dx*dx + dy*dy

    def map_vector_to_distance(self, dx, dy):
        """Return the squared distance for a mapping vector"""
        if self.topo_has_flag(TF_HEX):
            if (self.topo_has_flag(TF_ISO) and (dx*dy < 0)) or \
            (not self.topo_has_flag(TF_ISO) and (dx*dy > 0)):
                return abs(dx) + abs(dy)
            else:
                return max(abs(dx), abs(dy))
        else:
            return max(abs(dx), abs(dy))

    def map_distance_vector(self, tile0, tile1):
        """Return a vector of minimum distance between tiles."""
        dx = tile1.x - tile0.x
        if self.topo_has_flag(TF_WRAPX):
            half_world = floor(self.map["xsize"] / 2)
            dx = FC_WRAP(dx + half_world, self.map["xsize"]) - half_world

        dy = tile1.y - tile0.y
        if self.topo_has_flag(TF_WRAPY):
            half_world = floor(self.map["ysize"] / 2)
            dx = FC_WRAP(dy + half_world, self.map["ysize"]) - half_world

        return [dx, dy]

    def mapstep(self, ptile, dir8):
        """
          Step from the given tile in the given direction.  The new tile is returned,
          or None if the direction is invalid or leads off the mapping.
        """
        if not self.is_valid_dir(dir8):
            return None

        return self.map_pos_to_tile(DIR_DX[dir8] + ptile['x'], DIR_DY[dir8] + ptile['y'])

    def get_direction_for_step(self, start_tile, end_tile):
        """
            Return the direction which is needed for a step on the mapping from
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
        except:
            return "[undef]"

    @staticmethod
    def dir_cw(dir8):
        """Returns the next direction clock-wise."""
        try:
            return DIR8_CW[dir8]
        except:
            return -1

    @staticmethod
    def dir_ccw(dir8):
        """Returns the next direction counter clock-wise."""
        try:
            return DIR8_CCW[dir8]
        except:
            return -1

    def clear_goto_tiles(self):
        """Removes goto lines and clears goto tiles."""

        for x in range(self.map['xsize']):
            for y in range(self.map['ysize']):
                self.tiles[x + y * self.map['xsize']]['goto_dir'] = None

    def handle_tile_info(self, packet):
        if self.tiles != None:
            packet['extras'] = BitVector(bitlist=byte_to_bit_array(packet["extras"]))
            if self.tiles[packet['tile']] == None:
                self.tiles[packet['tile']] = {}

            self.tiles[packet['tile']].update(packet)

    def handle_set_topology(self, packet):
        """
        Server requested topology change.
        """
        pass
        #/* TODO */

    def handle_map_info(self, packet):
        self.map = packet
        self.map_init_topology(False)
        self.map_allocate()

        #/* TODO: init_client_goto()*/

        #mapdeco_init()

        #/* TODO: generate_citydlg_dimensions()*/

        #/* TODO: calculate_overview_dimensions()*/

    def tile_terrain_near(self, ptile):
        tterrain_near = []
        for dir8 in range(DIR8_LAST):
            tile1 = self.mapstep(ptile, dir8)
            if tile1 != None and TileState.tile_get_known(tile1) != TILE_UNKNOWN:
                terrain1 = self.rule_ctrl.tile_terrain(tile1)

                if terrain1 != None:
                    tterrain_near[dir8] = terrain1
                    continue
            """
            /* At the edges of the (known) mapping, pretend the same terrain continued
             * past the edge of the mapping. */
            """
            tterrain_near[dir8] = self.rule_ctrl.tile_terrain(ptile)
            #FIXME: BV_CLR_ALL(tspecial_near[dir])
        return tterrain_near

    def get_current_options(self, pplayer):
        return CivEvtHandler.get_current_options(self, pplayer)

    def get_current_state(self, pplayer):
        num_extras = len(self.tiles[0]["extras"])
        player_map = {}
        player_map["status"] = np.zeros((self.map['xsize'], self.map['ysize']))
        player_map["terrain"] = np.zeros((self.map['xsize'], self.map['ysize']))
        player_map["extras"] = np.zeros((self.map['xsize'], self.map['ysize'], num_extras)) 

        for x in range(self.map['xsize']):
            for y in range(self.map['ysize']):
                player_map["status"][x, y] = self.tiles[x + y * self.map['xsize']]["known"]
                player_map["terrain"][x, y] = self.tiles[x + y * self.map['xsize']]["terrain"]
                player_map["extras"][x, y, :] = self.tiles[x + y * self.map['xsize']]["extras"]

        return player_map

if __name__ == "__main__":
    print(MapCtrl.dir_get_name(7))
    print(MapCtrl.dir_get_name(MapCtrl.dir_ccw(7)))
    print(MapCtrl.dir_get_name(MapCtrl.dir_cw(7)))
