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

import numpy as np
import json

from civrealm.freeciv.utils.freeciv_logging import fc_logger


def sets_equal(set_a, set_b):
    """Returns true if sets are equal and raises Exception showing keys added/removed in case they
       are not equal"""
    if set_a != set_b:
        shared_keys = set_a & set_b
        keys_added = set_a - set_b
        keys_removed = set_b - set_a
        return shared_keys, keys_added, keys_removed
    return set_a, None, None


class PropState(ABC):
    def __init__(self):
        self._state = {}
        self._locked_props = []
        self._locked_set = None
        self._num_vars = -1

    def __repr__(self):
        return json.dumps(self._state, sort_keys=True)

    @abstractmethod
    def _update_state(self, pplayer):
        raise Exception(f'Abstract function - To be overwritten by {self.__class__}')

    @abstractmethod
    def _lock_properties(self):
        raise Exception(f'Abstract function - To be overwritten by {self.__class__}')

    @abstractmethod
    def _state_has_locked_properties(self):
        raise Exception(f'Abstract function - To be overwritten by {self.__class__}')

    def update(self, pplayer, *args):
        self._update_state(pplayer, *args)
        if self._locked_props == []:
            self._lock_properties()
            self._locked_set = set(self._locked_props)
            self._set_num_vars()

    @abstractmethod
    def _set_num_vars(self):
        raise Exception(f'Abstract function - To be overwritten by {self.__class__}')

    def get_state(self):
        """Get state ensures that the returned state only contains the properties that
        are locked in the first time update has been called"""
        if self._state_has_locked_properties():
            return self._state

    def get_num_vars(self):
        return self._num_vars

    @abstractmethod
    def get_state_vec(self, item=None):
        raise Exception(f'Abstract function - To be overwritten by {self.__class__}')


class PlainState(PropState):
    def _lock_properties(self):
        self._locked_props = self._state.keys()
        for key in self._locked_props:
            if type(self._state[key]) is dict or type(self._state[key]) is list:
                fc_logger.debug(self._locked_props)
                raise Exception("Lists/Dicts should not be values in a PlainState %s \n \
                                 key: %s val: %s " % (self, key, self._state[key]))

    def _state_has_locked_properties(self):
        cur_set = set(self._state.keys())
        return sets_equal(cur_set, self._locked_set)

    def _set_num_vars(self):
        self._num_vars = len(self._locked_props)

    def get_state_vec(self, item=None):
        vec = np.zeros([1, self._num_vars])
        for knum, key in enumerate(self._locked_props):
            vec[0, knum] = self._state[key]
        return vec


class DictState(PlainState):

    def _lock_properties(self):
        if self._state == {}:
            return
        first_element = self._state[list(self._state.keys())[0]]
        self._locked_props = first_element.keys()

    def _state_has_locked_properties(self):
        for item in self._state.keys():
            cur_set = set(self._state[item].keys())
            shared_keys, keys_added, keys_removed = sets_equal(cur_set, self._locked_set)
            if keys_removed is not None:
                if len(keys_removed) != 0:
                    raise Exception("State properties have changed from initially locked properties:\n\
                                             shared_keys: %s\n keys_added: %s\n keys_removed: %s\n" %
                                    (shared_keys, keys_added, keys_removed))

            elif keys_added is not None:
                for item in keys_added:
                    del self._state[item]
        return True

    def _set_num_vars(self):
        self._num_vars = len(self._locked_props)

    def get_state_vec(self, item):
        vec = np.zeros([1, self._num_vars])
        err = False
        for knum, key in enumerate(self._locked_props):
            try:
                vec[0, knum] = self._state[item][key]
                if np.isnan(vec[0, knum]):
                    raise Exception("No nan allowed for key: %s" % key)
            except:
                fc_logger.error("Incompatible string/int %s %s" % (key, self._state[item][key]))
                err = True

        if err:
            raise Exception("Change state to be compatible")
        return vec

    def remove_dict_item(self, item_id):
        if item_id in self._state.keys():
            del self._state[item_id]
        else:
            fc_logger.warning("Strange - Trying to delete unit that is not there: %s" % item_id)


class EmptyState(PlainState):
    def _update_state(self, pplayer):
        return
