'''
Created on 29.12.2017

@author: christian
'''
from freecivbot.utils.base_action import ActionList
from freecivbot.utils.base_state import PropState

from freecivbot.utils.freeciv_logging import logger


class CivPropController():
    """ Controller for certain properties of the Civilization "Board
        The controller processes messages from the freeciv server (e.g., stores data)
        and can send information back to  
    """

    def __init__(self, ws_client):
        self.hdict = {}
        self.ws_client = ws_client
        self.prop_state = PropState()
        self.prop_actions = ActionList(ws_client)

    def register_with_parent(self, parent):
        for key in self.hdict.keys():
            if key in parent.hdict:
                raise Exception("Event already controlled by Parent: %s" % key)
            parent.hdict[key] = self.hdict[key]

    def register_handler(self, pid, func):
        self.hdict[pid] = (self, func)

    def handle_pack(self, pid, data):
        if pid in self.hdict:
            logger.debug('Receiving packet: {}'.format(data))
            handle_func = getattr(self.hdict[pid][0], self.hdict[pid][1])
            handle_func(data)
        else:
            logger.warning("Handler function for pid %i not yet implemented" % pid)

    def get_current_state(self, pplayer):
        self.prop_state.update(pplayer)
        return self.prop_state.get_state()

    def get_current_state_vec(self, pplayer, item=None):
        self.prop_state.update(pplayer)
        return self.prop_state.get_state_vec(item)

    def get_current_options(self, pplayer):
        self.prop_actions.update(pplayer)
        return self.prop_actions
