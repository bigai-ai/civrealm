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

from abc import ABC, abstractmethod

from civrealm.freeciv.utils.freeciv_logging import fc_logger


class Action(ABC):
    """ Baseclass for all actions that can be send to the server -
        validity of actions needs to be ensured prior to triggering action"""
    action_key = None
    wait_for_pid = None

    def __repr__(self):
        return self.action_key

    def encode_to_json(self):
        """Encode action to json - abstract function should be overwritten"""
        fc_logger.warning(f'encode_to_json not implemented for {self.__class__}')
        return self._action_packet()

    def trigger_action(self, ws_client):
        """Trigger validated action"""
        packet = self._action_packet()
        if type(packet) == list:
            for pac in packet:
                fc_logger.info(f"trigger_action. {pac}. Packet in list.")
                ws_client.send_request(pac, self.wait_for_pid)
            return self.refresh_state_after_action(ws_client)
        else:
            # if 'unit_id' in packet:
            #     if packet['unit_id'] == 103:
            #         print(packet)
            fc_logger.info(f"trigger_action. {packet}")
            ws_client.send_request(packet, self.wait_for_pid)
            return self.refresh_state_after_action(ws_client)

    def refresh_state_after_action(self, ws_client):
        """Refresh state after action"""
        packet = self._refresh_state_packet()
        if packet:
            return ws_client.send_request(packet)

    @abstractmethod
    def is_action_valid(self):
        """Check if action is valid - abstract function should be overwritten"""
        raise Exception(f'Abstract function - To be overwritten by {self.__class__}')

    @abstractmethod
    def _action_packet(self):
        """returns the packet that should be sent to the server to carry out action -
        abstract function should be overwritten"""
        raise Exception(f'Abstract function - To be overwritten by {self.__class__}')

    def _refresh_state_packet(self):
        return None


class ActionList(object):
    def __init__(self, ws_client):
        self._action_dict = {}
        self.ws_client = ws_client
        # This dict only stores the actions which query action probability from the server.
        self._get_pro_action_dict = {}

    def encode_to_json(self):
        return dict(
            [(actor_id,
              dict(
                  [(action_key, self._action_dict[actor_id][action_key].is_action_valid())
                   for action_key in self._action_dict[actor_id]])) for actor_id in self._action_dict])

    def add_actor(self, actor_id):
        if actor_id not in self._action_dict:
            self._action_dict[actor_id] = {}
        if actor_id not in self._get_pro_action_dict:
            self._get_pro_action_dict[actor_id] = {}

    def remove_actor(self, actor_id):
        if actor_id in self._action_dict:
            del self._action_dict[actor_id]
        else:
            # This can happen when a unit is destroyed right after it is born.
            fc_logger.info("strange - trying to remove non-existent actor: %s" % actor_id)

        if actor_id in self._get_pro_action_dict:
            del self._get_pro_action_dict[actor_id]
        else:
            # This can happen when a unit is destroyed right after it is born.
            fc_logger.info("strange - trying to remove non-existent actor: %s" % actor_id)

    def add_action(self, actor_id, a_action):
        if actor_id not in self._action_dict:
            raise Exception("Add actor %s first!!!" % actor_id)
        if a_action.action_key in self._action_dict[actor_id]:
            raise Exception("action_key %s should be unique for each actor" % a_action.action_key)

        self._action_dict[actor_id][a_action.action_key] = a_action

    def update_action(self, actor_id, a_action):
        if actor_id not in self._action_dict:
            raise Exception("Add actor %s first!!!" % actor_id)
        self._action_dict[actor_id][a_action.action_key] = a_action

    # Used to remove the action added dynamically (due to dynamic target units)
    def remove_action(self, actor_id, action_key):
        # if actor_id not in self._action_dict:
        #     raise Exception(f'Add actor {actor_id} first!!!')
        # if action_key not in self._action_dict[actor_id]:
        #     raise Exception(f'Action_key {action_key} does not exist')

        # It is possible that a unit has been removed due to packet-62
        if actor_id in self._action_dict:
            if action_key not in self._action_dict[actor_id]:
                raise Exception(f'Action_key {action_key} does not exist')
            del self._action_dict[actor_id][action_key]

    def add_get_pro_action(self, actor_id, a_action):
        if actor_id not in self._get_pro_action_dict:
            raise Exception("Add actor %s first!!!" % actor_id)
        if a_action.action_key in self._get_pro_action_dict[actor_id]:
            raise Exception("action_key %s should be unique for each actor" % a_action.action_key)

        self._get_pro_action_dict[actor_id][a_action.action_key] = a_action

    def actor_exists(self, actor_id):
        return actor_id in self._action_dict

    def get_actors(self):
        return self._action_dict.keys()

    def get_actions(self, actor_id, valid_only=False):
        if self.actor_exists(actor_id):
            if valid_only:
                act_dict = {}
            else:
                act_dict = dict([(key, None) for key in self._action_dict[actor_id]])
            if self._can_actor_act(actor_id):
                for action_key in self._action_dict[actor_id]:
                    action = self._action_dict[actor_id][action_key]
                    if action.is_action_valid():
                        act_dict[action_key] = action
            return act_dict
        return {}

    def get_valid_actions(self, actor_id, act_keys):
        # FIXME: unsed function. May be useful for creating action masks.
        if self.actor_exists(actor_id):
            act_list = [False for key in self._action_dict[actor_id]]
            if self._can_actor_act(actor_id):
                act_list = [self._action_dict[actor_id][action_key].is_action_valid() for
                            action_key in act_keys]
            return act_list

    def _can_actor_act(self, actor_id):
        raise Exception("To be overwritten with function returning True/False %i" % actor_id)

    def trigger_single_action(self, actor_id, action_id):
        # FIXME: unsed function
        act = self._action_dict[actor_id][action_id]
        if not self._can_actor_act(actor_id):
            raise Exception('_can_actor_act error')
        if act.is_action_valid():
            act.trigger_action(self.ws_client)
            return True
        return False

    def trigger_wanted_actions(self, controller_wants):
        # FIXME: unsed function
        for a_actor in self._action_dict:
            if a_actor not in controller_wants:
                raise ("Wants for actor %s should have been defined." % a_actor)
            actor_wants = controller_wants[a_actor]
            if actor_wants == {}:
                fc_logger.info("No actions wanted for actor %s" % a_actor)
                continue
            if type(actor_wants) is list:
                raise ("Wants for actor %s should be a dictionary not a list" % a_actor)

            action_most_wanted = max(list(actor_wants.keys()), key=(lambda x: actor_wants[x]))

            if actor_wants[action_most_wanted] > 0:
                fc_logger.info(action_most_wanted)
                self._action_dict[a_actor][action_most_wanted].trigger_action(self.ws_client)

    def update(self, pplayer):
        raise Exception("To be implemented by class %s for player %s" % (self, pplayer))

    def get_num_actions(self):
        a_actor = self._action_dict[self._action_dict.keys()[0]]
        return len(a_actor.keys())

    def get_action_list(self):
        a_actor = self._action_dict[self._action_dict.keys()[0]]
        return a_actor.keys()

    def get_num_get_pro_actions(self):
        a_actor = self._get_pro_action_dict[self._get_pro_action_dict.keys()[0]]
        return len(a_actor.keys())

    def get_get_pro_action_list(self):
        a_actor = self._get_pro_action_dict[self._get_pro_action_dict.keys()[0]]
        return a_actor.keys()

    def get_action_info(self):
        action_info = {}
        for actor_id in self._action_dict:
            if not self._can_actor_act(actor_id):
                continue
            action_info[actor_id] = {}
            for action_key, action in self._action_dict[actor_id].items():
                action_info[actor_id][action_key] = action.is_action_valid()
        return action_info


class NoActions(ActionList):
    def update(self, pplayer):
        pass

    def _can_actor_act(self, actor_id):
        return False
