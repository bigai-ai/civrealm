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


DIR = [
    (0, 0), (0, -1), (0, 1), (1, 0), (-1, 0), (1, -1), (-1, -1), (1, 1), (-1, 1), (0, -2), (1, -2), (-1, -2),
    (2, -2), (-2, -2), (0, 2), (1, 2), (-1, 2), (2, 2), (-2, 2), (2, 0), (2, -1), (2, 1), (-2, 0), (-2, -1),
    (-2, 1)
]


def action_mask(keywords, avail_action_set):
    action_names = []
    for act in avail_action_set:
        for keyword in keywords:
            if keyword in act:
                action_names.append(act)
    return action_names


def get_valid_actions(info, ctrl_type, actor_id):
    action_dict = info['available_actions'][ctrl_type]
    avail_action_list = []

    for actor_act in action_dict[actor_id]:
        if action_dict[actor_id][actor_act]:
            avail_action_list.append(actor_act)
    return avail_action_list


def make_action_list_readable(action_list, action_names):
    readable_action_list = []
    for action in action_list:
        if action in action_names.keys():
            readable_action_list.append(action_names[action])
        else:
            readable_action_list.append(action)

    for i, action in enumerate(readable_action_list):
        readable_action = ''
        for j, char in enumerate(action):
            if char == '_':
                readable_action += ' '
            elif char == ' ':
                readable_action += '_'
            else:
                readable_action += char

        readable_action_list[i] = readable_action
    return readable_action_list


def get_action_from_readable_name(readable_action, action_keys):

    action = ''
    for j, char in enumerate(readable_action):
        if char == '_':
            action += ' '
        elif char == ' ':
            action += '_'
        else:
            action += char
    if action in action_keys.keys():
        action = action_keys[action]

    return action



