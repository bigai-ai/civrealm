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
UNSEEN_SIGNAL = 'u'

def map_parser(map_data):
    """ parse map string from sav file to 2-d array """
    return [[element for element in line.split('=')[1] if element != '"'] 
            for line in map_data.split('\n') if line > '']

def align_to_map(player_map, total_map):
    """ align to the goal map """
    for x in range(len(player_map)):
        for y in range(len(player_map[x])):
            if  player_map[x][y] != total_map[x][y] and player_map[x][y] != UNSEEN_SIGNAL:
                player_map[x][y] = total_map[x][y]
    return player_map
