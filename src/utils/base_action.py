'''
Created on 16.02.2018

@author: christian
'''

class Action(object):
    """ Baseclass for all actions that can be send to the server -
        validity of actions needs to be ensured prior to triggering action"""
    action_key = None
    def __init__(self, ws_client):
        self.ws_client = ws_client

    def trigger_action(self):
        """Trigger validated action"""
        packet = self._action_packet()
        self.ws_client.send_request(packet)

    def is_action_valid(self):
        """Check if action is valid - abstract function should be overwritten"""
        raise Exception("Abstract function - To be overwritten by %s" % self.__class__)

    def _action_packet(self):
        """returns the packet that should be sent to the server to carry out action -
        abstract function should be overwritten"""
        raise Exception("Abstract function - To be overwritten by %s" % self.__class__)

class ActionList(object):
    def __init__(self):
        self._action_dict = {}
    
    def add_actor(self, actor_id):
        if actor_id not in self._action_dict:
            self._action_dict[actor_id] = {}
    
    def add_action(self, actor_id, a_action):
        if actor_id not in self._action_dict:
            raise Exception("Add actor %s first!!!" % actor_id)
        if a_action.action_key in self._action_dict[actor_id]:
            raise Exception("action_key %s should be unique for each actor" % a_action.action_key)
        
        self._action_dict[actor_id][a_action.action_key] = a_action
    
    def actor_exists(self, actor_id):
        return actor_id in self._action_dict

    def get_actions(self):
        return self._action_dict