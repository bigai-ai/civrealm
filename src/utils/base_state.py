'''
Created on 07.03.2018

@author: christian
'''

def sets_equal(set_a, set_b):
    if len(set_a) != len(set_b) or \
       len(set_a.intersection(set_b)) != 0:
        shared_keys = set_a & set_b
        keys_added = set_a - set_b
        keys_removed = set_b - set_a
        raise Exception("State properties have changed from initially locked properties:\n\
                         shared_keys: %s\n keys_added: %s\n keys_removed: %s\n" %
                         (shared_keys, keys_added, keys_removed))
    return True

class PropState():
    def __init__(self):
        self._state = {}
        self._locked_props = []
        self._locked_set = None
    
    def _update_state(self, pplayer):
        raise Exception("To be overwritten")
    
    def _lock_properties(self):
        raise Exception("To be overwritten")
    
    def _state_has_locked_properties(self):
        raise Exception("To be overwritten")
        
    def update(self, pplayer):
        self._update_state(pplayer)
        if self._locked_props == []:
            self._lock_properties()
            self._locked_set = set(self._locked_props)

    def get_state(self):
        """Get state ensures that the returned state only contains the properties that
        are locked in the first time update has been called"""
        if self._state_has_locked_properties():
            return self._state

class PlainState(PropState):
    def _lock_properties(self):
        self._locked_props = self._state.keys()
        for key in self._locked_props:
            if type(self._state[key]) is dict or type(self._state[key]) is list:
                print(self._locked_props)
                raise Exception("Lists/Dicts should not be values in a PlainState %s \n \
                                 key: %s val: %s " % (self, key, self._state[key]))

    def _state_has_locked_properties(self):
        cur_set = set(self._state.keys())
        return sets_equal(cur_set, self._locked_set)

class ListState(PlainState):
    def _lock_properties(self):
        first_element = self._state[self._state.keys()[0]]
        self._locked_props = first_element.keys()

    def _state_has_locked_properties(self):
        for item in self._state.keys():
            cur_set = set(self._state[item].keys())
            if not sets_equal(cur_set, self._locked_set):
                return False
        return True