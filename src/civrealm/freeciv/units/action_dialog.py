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

PROB_SURE = 0
PROB_RANGE = 1
PROB_LACK_OF_INFO = 2


def action_prob_possible(aprob):
    """Returns true iff the given action probability belongs to an action that
    may be possible."""
    return 0 < aprob['max'] or action_prob_not_impl(aprob)


def action_prob_not_impl(probability):
    """Returns TRUE iff the given action probability represents that support
    for finding this action probability currently is missing from freeciv."""
    return probability['min'] == 254 and probability['max'] == 0


def encode_building_id(building_id):
    """
        Encode a building ID for transfer in the value field of
        packet_unit_do_action for targeted sabotage city.
    """
    # Building ID is encoded in the value field by adding one so the
    # building ID -1 (current production) can be transferred. */
    return building_id + 1


def format_act_prob_part(prob):
    """Returns a part of an action probability in a user readable format."""
    return (prob / 2)


def get_probability_type(probability):
    """Get type of success_rate"""

    if probability['min'] == probability['max']:
        # This is a regular and simple chance of success.
        return PROB_SURE, probability['max'], probability['min']
    elif (probability['min'] < probability['max']):
        # /* This is a regular chance of success range. */
        if probability['max'] - probability['min'] > 1:
            """The interval is wide enough to not be caused by rounding. It is
            * therefore imprecise because the player doesn't have enough
            * information. """
            return PROB_RANGE, probability['max'], probability['min']
        else:
            return PROB_LACK_OF_INFO, probability['max'], probability['min']
    else:
        # The remaining action probabilities shouldn't be displayed.
        raise Exception("Min prob should always be lower than Max prob: %f %f" % (probability["max"],
                                                                                  probability["min"]))
