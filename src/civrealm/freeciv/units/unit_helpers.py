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


def get_unit_moves_left(rule_ctrl, punit):
    """Returns a string saying how many moves a unit has left."""
    if punit is None:
        return 0

    return move_points_text(rule_ctrl, punit['movesleft'])


def move_points_text(rule_ctrl, moves):
    result = ""
    SINGLE_MOVE = rule_ctrl.SINGLE_MOVE
    if (moves % SINGLE_MOVE) != 0:
        if moves // SINGLE_MOVE > 0:
            result = f'{moves // SINGLE_MOVE} {moves % SINGLE_MOVE}/{SINGLE_MOVE}'
        else:
            result = f'{moves % SINGLE_MOVE}/{SINGLE_MOVE}'
    else:
        result = f'{moves // SINGLE_MOVE}'
    return result
