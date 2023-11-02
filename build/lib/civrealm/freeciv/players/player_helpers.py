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


import civrealm.freeciv.players.player_const as player_const


def government_max_rate(govt_id):
    """
        Returns the max tax rate for a given government.
        FIXME: This shouldn't be hardcoded, but instead fetched
        from the effects.
    """
    if govt_id in [player_const.GOV_ANARCHY, player_const.GOV_DEMOCRACY]:
        return 100
    elif govt_id == player_const.GOV_DESPOTISM:
        return 60
    elif govt_id == player_const.GOV_MONARCHY:
        return 70
    elif govt_id in [player_const.GOV_COMMUNISM, player_const.GOV_REPUBLIC]:
        return 80
    else:
        return 100  # // this should not happen
