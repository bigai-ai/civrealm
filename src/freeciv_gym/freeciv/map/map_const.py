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

DIR8_NAMES = ['NorthWest', 'North', 'NorthEast', 'West', 'East', 'SouthWest', 'South', 'SouthEast']

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

TERRAIN_NAMES = ['Inaccessible', 'Lake', 'Ocean', 'Deep Ocean', 'Glacier',
                 'Desert', 'Forest', 'Grassland', 'Hills', 'Jungle',
                 'Mountains', 'Plains', 'Swamp', 'Tundra']

EXTRA_NAMES = ['Irrigation', 'Mine', 'Oil Well', 'Pollution', 'Minor Tribe Village',
               'Farmland', 'Fallout', 'Fortress', 'Airbase', 'Buoy', 'Ruins', 'Road',
               'Railroad', 'River', 'Gold', 'Iron', 'Game', 'Furs', 'Coal', 'Fish', 'Fruit',
               'Gems', 'Buffalo', 'Wheat', 'Oasis', 'Peat', 'Pheasant', 'Resources',
               'Ivory', 'Silk', 'Spice', 'Whales', 'Wine', 'Oil']
