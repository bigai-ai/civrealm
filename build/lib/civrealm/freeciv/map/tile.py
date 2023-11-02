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


TILE_UNKNOWN = 0
TILE_KNOWN_UNSEEN = 1
TILE_KNOWN_SEEN = 2


class TileState:

    @staticmethod
    def tile_get_known(ptile):
        """
        Return a known_type enumeration value for the tile.
        Note that the client only has known data about its own player.
        """
        if ptile['known'] is None:
            return TILE_UNKNOWN
        else:
            return ptile['known']

    @staticmethod
    def tile_has_extra(ptile, extra):
        """Returns true iff the specified tile has the extra with the specified
          extra number."""
        if ptile['extras'] is None:
            return False

        # return extra in ptile['extras']
        return ptile['extras'][extra] == 1

    @staticmethod
    def tile_resource(tile):
        return tile['resource']

    @staticmethod
    def tile_set_resource(tile, resource):
        tile['resource'] = resource

    @staticmethod
    def tile_owner(tile):
        return tile['owner']

    @staticmethod
    def tile_set_owner(tile, owner, claimer):
        tile['owner'] = owner

    @staticmethod
    def tile_worked(tile):
        return tile['worked']

    @staticmethod
    def tile_set_worked(ptile, pwork):
        ptile['worked'] = pwork
