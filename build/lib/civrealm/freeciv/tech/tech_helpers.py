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


import civrealm.freeciv.tech.tech_const as tech_const
from civrealm.freeciv.utils.fc_types import VUT_ADVANCE


def is_tech_known(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == tech_const.TECH_KNOWN


def is_tech_unknown(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == tech_const.TECH_UNKNOWN


def is_tech_prereq_known(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == tech_const.TECH_PREREQS_KNOWN


def player_invention_state(pplayer, tech_id):
    """
      Returns state of the tech for current pplayer.
      This can be: TECH_KNOWN, TECH_UNKNOWN, or TECH_PREREQS_KNOWN
      Should be called with existing techs or A_FUTURE

      If pplayer is None this checks whether any player knows the tech (used
      by the client).
    """
    if (pplayer is None) or ('inventions' not in pplayer) or tech_id >= len(pplayer['inventions']):
        return tech_const.TECH_UNKNOWN
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


def recreate_old_tech_req(packet):
    """
    Recreate the old req[] field of ruleset_tech packets.
    This makes it possible to delay research_reqs support.
    """

    # /* Recreate the field it self. */
    packet['req'] = []

    # /* Add all techs in research_reqs. */
    for requirement in packet['research_reqs']:
        if requirement["kind"] == VUT_ADVANCE and requirement["range"] == tech_const.REQ_RANGE_PLAYER and \
                requirement["present"]:
            packet['req'].append(requirement["value"])

    # /* Fill in A_NONE just in case Freeciv-web assumes its size is 2. */
    while len(packet['req']) < 2:
        packet['req'].append(tech_const.A_NONE)
