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
from math import floor, sqrt
import numpy as np
from BitVector import BitVector

from freecivbot.connectivity.Basehandler import CivPropController
from freecivbot.utils.utility import FC_WRAP, byte_to_bit_array, sign
from freecivbot.utils.base_action import NoActions
from freecivbot.map.tile import TileState, TILE_UNKNOWN
from freecivbot.map.map_state import MapState
import json


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

class MapCtrl(CivPropController):
    def __init__(self, ws_client, rule_ctrl):
        CivPropController.__init__(self, ws_client)
        self.map = {}
        self.tiles = []
        self.player_map = {}
        self.player_map["status"] = None
        self.player_map["terrain"] = None
        self.player_map["extras"] = None
         
        self.rule_ctrl = rule_ctrl
        self.prop_state = MapState(self.player_map)
        self.prop_actions = NoActions(ws_client)

        self.register_handler(15, "handle_tile_info")
        self.register_handler(17, "handle_map_info")
        self.register_handler(253, "handle_set_topology")

    def __repr__(self):
        return json.dumps(self.tiles, sort_keys=True)

    def topo_has_flag(self, flag):
        return ((self.map['topology_id'] & (flag)) != 0)

    def city_tile(self, pcity):
        if pcity == None:
            return None

        return self.index_to_tile(pcity['tile'])

    def map_allocate(self):
        """
            Allocate space for map, and initialise the tiles.
            Uses current map.xsize and map.ysize.
        """

        self.tiles = []
        """
        Note this use of whole_map_iterate may be a bit sketchy, since the
        tile values (ptile->index, etc.) haven't been set yet.  It might be
        better to do a manual loop here.
        """
        
        shape_map = (self.map['xsize'], self.map['ysize'])
        
        self.player_map["status"] = np.zeros(shape_map, dtype="B")
        self.player_map["terrain"] = np.zeros(shape_map, dtype="H")
        
        for y in range(self.map['ysize']):
            for x in range(self.map['xsize']):
                self.tiles.append(None)
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

    def map_init_topology(self):
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
        if packet['tile'] < len(self.tiles) and self.tiles[packet['tile']] != None:
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
        """ Return the tile for the given cartesian (map) position."""
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
        """Return a vector of minimum distance between tiles."""
        dx = tile1["x"] - tile0["x"]
        if self.topo_has_flag(TF_WRAPX):
            half_world = floor(self.map["xsize"] / 2)
            dx = FC_WRAP(dx + half_world, self.map["xsize"]) - half_world

        dy = tile1["y"] - tile0["y"]
        if self.topo_has_flag(TF_WRAPY):
            half_world = floor(self.map["ysize"] / 2)
            dx = FC_WRAP(dy + half_world, self.map["ysize"]) - half_world

        return dx, dy
    
    def map_distances(self, dx, dy):
        if self.topo_has_flag(TF_WRAPX):
            half_world = floor(self.map["xsize"] / 2)
            dx = FC_WRAP(dx + half_world, self.map["xsize"]) - half_world

        if self.topo_has_flag(TF_WRAPY):
            half_world = floor(self.map["ysize"] / 2)
            dx = FC_WRAP(dy + half_world, self.map["ysize"]) - half_world

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
            return "[undef]"

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

        for x in range(self.map['xsize']):
            for y in range(self.map['ysize']):
                self.tiles[x + y * self.map['xsize']]['goto_dir'] = None

    def handle_tile_info(self, packet):
        if self.tiles != None:
            packet['extras'] = BitVector(bitlist=byte_to_bit_array(packet["extras"]))
            if self.player_map["extras"] is None:
                extras_map = (self.map['xsize'], self.map['ysize'], len(packet['extras']))
                self.player_map["extras"] = np.zeros(extras_map, dtype="?")
                
            ptile = packet['tile']
            if self.tiles[ptile] == None:
                self.tiles[ptile] = {}

            self.tiles[ptile].update(packet)
            self.player_map["status"][self.tiles[ptile]['x'], self.tiles[ptile]['y']] = packet['known']
            self.player_map["terrain"][self.tiles[ptile]['x'], self.tiles[ptile]['y']] = packet['terrain']
            self.player_map["extras"][self.tiles[ptile]['x'], self.tiles[ptile]['y'], :] = packet['extras']  

    def handle_set_topology(self, packet):
        """
        Server requested topology change.
        """
        pass
        #/* TODO */

    def handle_map_info(self, packet):
        self.map = packet
        self.map_init_topology()
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
            /* At the edges of the (known) map, pretend the same terrain continued
             * past the edge of the map. */
            """
            tterrain_near[dir8] = self.rule_ctrl.tile_terrain(ptile)
        return tterrain_near
    
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
    def __init__(self, radius_sq, map_ctrl):
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
            import functools
            vectors = sorted(vectors, key=functools.cmp_to_key(get_dist))            
            base_map = [None for _ in range((2*r+1)*(2*r+1))]
            
            for vnum, vec in enumerate(vectors):
                base_map[vec[3]] = vnum
            
            # print(base_map)            
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
        clipped_map = [-1 for _ in range(vl*10)]
        max_ind = 0
        ind = 0
        for vi in range(vl):
            tile_data = v[vi]
            if dx_min <= tile_data[0] <= dx_max and dy_min <= tile_data[1] <= dy_max:
                clipped_map[tile_data[3]] = ind
                if max_ind < tile_data[3]:
                    max_ind = tile_data[3]
                ind += 1
        return clipped_map[:max_ind+1]
    
    def get_city_tile_map_for_pos(self, x, y):
        """Returns the map of position from city center to index in city_info."""
        topo_has_flag = self.map_ctrl.topo_has_flag
        if topo_has_flag(TF_WRAPX) and topo_has_flag(TF_WRAPY):
            return self.maps[0]
        
        r = self.radius
        limit_args = {"dx_min": -r, "dx_max": r, "dy_min": -r, "dy_max": r}
        target_map = None
        
        if topo_has_flag(TF_WRAPX):#Cylinder with N-S axis
            dy = self.delta_tile_helper(y, r, self.map_ctrl.map["ysize"])
            limit_args["dy_min"] = dy[0]
            limit_args["dy_max"] = dy[1]
            target_map = dy[2]
        
        if topo_has_flag(TF_WRAPY):#Cylinder with E-W axis
            dx = self.delta_tile_helper(x, r, self.map_ctrl.map["xsize"])
            limit_args["dx_min"] = dx[0]
            limit_args["dx_max"] = dx[1]
            # if target_map != None:
            #     target_map = (2*r + 1) * dx[2] + dy[2]
            # else:
            target_map = dx[2]

        if target_map == None: # Flat
            dx = self.delta_tile_helper(x, r, self.map_ctrl.map["xsize"])
            dy = self.delta_tile_helper(y, r, self.map_ctrl.map["xsize"])
            map_i = (2*r + 1) * dx[2] + dy[2]
            if map_i not in self.maps: 
                m = self.build_city_tile_map_with_limits(dx[0], dx[1], dy[0], dy[1])
                self.maps[map_i] = m            
            return self.maps[map_i]
        
        if target_map not in self.maps:
            self.maps[target_map] = self.build_city_tile_map_with_limits(**limit_args)
        return self.maps[target_map]

        # if topo_has_flag(TF_WRAPX):#Cylinder with N-S axis
        #     dy = self.delta_tile_helper(y, r, self.map_ctrl.map["ysize"])
        #     if self.maps[dy[2]] == None:
        #         m = self.build_city_tile_map_with_limits(-r, r, dy[0], dy[1])
        #         self.maps[dy[2]] = m;                        
        #     return self.maps[dy[2]]    

     
       
       
    




    def get_city_dxy_to_index(self, dx, dy, city_tile):
        """
          Converts from coordinate offset from city center (dx, dy),
          to index in the city_info['output_food'] packet.
        """
        city_tile_map_index = dxy_to_center_index(dx, dy, self.radius)
        a_map = self.get_city_tile_map_for_pos(city_tile["x"], city_tile["y"])
        return a_map[city_tile_map_index]

if __name__ == "__main__":
    print(MapCtrl.dir_get_name(7))
    print(MapCtrl.dir_get_name(MapCtrl.dir_ccw(7)))
    print(MapCtrl.dir_get_name(MapCtrl.dir_cw(7)))
