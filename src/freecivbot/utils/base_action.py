'''
Created on 16.02.2018

@author: christian
'''
from freecivbot.bot.base_bot import ACTION_UNWANTED

class Action(object):
    """ Baseclass for all actions that can be send to the server -
        validity of actions needs to be ensured prior to triggering action"""
    action_key = None

    def trigger_action(self, ws_client):
        """Trigger validated action"""
        packet = self._action_packet()
        print(packet)
        return ws_client.send_request(packet)

    def is_action_valid(self):
        """Check if action is valid - abstract function should be overwritten"""
        raise Exception("Abstract function - To be overwritten by %s" % self.__class__)

    def _action_packet(self):
        """returns the packet that should be sent to the server to carry out action -
        abstract function should be overwritten"""
        raise Exception("Abstract function - To be overwritten by %s" % self.__class__)

class ActionList(object):
    def __init__(self, ws_client):
        self._action_dict = {}
        self.ws_client = ws_client

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
    
    def get_valid_actions(self, actor_id, act_keys):
        if self.actor_exists(actor_id):
            act_list = [False for key in self._action_dict[actor_id]]
            if self._can_actor_act(actor_id):
                act_list = [self._action_dict[actor_id][action_key].is_action_valid() for 
                            action_key in act_keys]
            return act_list

    def _can_actor_act(self, actor_id):
        raise Exception("To be overwritten with function returning True/False %i" % actor_id)
    
    def trigger_single_action(self, actor_id, action_id):
        act = self._action_dict[actor_id][action_id]
        if not self._can_actor_act(actor_id):
            return None 
        if act.is_action_valid():
            act.trigger_action(self.ws_client)
            return True
        return False
    
    def trigger_validated_action(self, act):
        act.trigger_action(self.ws_client)
    
    def trigger_wanted_actions(self, controller_wants):
        for a_actor in self._action_dict:
            if a_actor not in controller_wants:
                raise("Wants for actor %s should have been defined." % a_actor)
            actor_wants = controller_wants[a_actor]
            if actor_wants == {}:
                print("No actions wanted for actor %s" % a_actor)
                continue
            if type(actor_wants) is list:
                raise("Wants for actor %s should be a dictionary not a list" % a_actor)
            
            action_most_wanted = max(actor_wants.iterkeys(), key=(lambda x: actor_wants[x]))
            
            if actor_wants[action_most_wanted] != ACTION_UNWANTED:
                print(action_most_wanted)
                self._action_dict[a_actor][action_most_wanted].trigger_action(self.ws_client)
    
    def update(self, pplayer):
        raise Exception("To be implemented by class %s for player %s" % (self, pplayer))

    def get_num_actions(self):
        a_actor = self._action_dict[self._action_dict.keys()[0]]
        return len(a_actor.keys())
    
    def get_action_list(self):
        a_actor = self._action_dict[self._action_dict.keys()[0]]
        return a_actor.keys()

class NoActions(ActionList):
    def update(self, pplayer):
        pass
    
    def _can_actor_act(self, actor_id):
        return False