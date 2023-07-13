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

from freeciv_gym.freeciv.utils.fc_types import MAX_NUM_ADVANCES

TECH_UNKNOWN = 0
TECH_PREREQS_KNOWN = 1
TECH_KNOWN = 2


A_NONE = 0
A_FIRST = 1
A_LAST = MAX_NUM_ADVANCES + 1
A_UNSET = A_LAST + 1
A_FUTURE = A_LAST + 2
A_UNKNOWN = A_LAST + 3
A_LAST_REAL = A_UNKNOWN

A_NEVER = None
U_NOT_OBSOLETED = None


def is_tech_known(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == TECH_KNOWN


def is_tech_unknown(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == TECH_UNKNOWN


def is_tech_prereq_known(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == TECH_PREREQS_KNOWN


def player_invention_state(pplayer, tech_id):
    """
      Returns state of the tech for current pplayer.
      This can be: TECH_KNOWN, TECH_UNKNOWN, or TECH_PREREQS_KNOWN
      Should be called with existing techs or A_FUTURE

      If pplayer is None this checks whether any player knows the tech (used
      by the client).
    """
    if (pplayer is None) or ('inventions' not in pplayer) or tech_id >= len(pplayer['inventions']):
        return TECH_UNKNOWN
    else:
        # /* Research can be None in client when looking for tech_leakage
        # * from player not yet received. */
        return int(pplayer['inventions'][tech_id])

    # /* FIXME: add support for global advances
    # if (tech != A_FUTURE and game.info.global_advances[tech_id]) {
    #  return TECH_KNOWN
    # } else {
    #  return TECH_UNKNOWN
    # }*/


def can_player_build_unit_direct(pplayer, punittype):
    """
    Whether player can build given unit somewhere,
    ignoring whether unit is obsolete and assuming the
    player has a coastal city.
    """
    if not is_tech_known(pplayer, punittype['build_reqs'][0]['value']):
        return False

    # FIXME: add support for global advances, check for building reqs etc.*/

    return True