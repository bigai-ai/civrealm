'''
Created on 16.02.2018

@author: christian
'''

class Action(object):
    """ Baseclass for all actions that can be send to the server -
        validity of actions needs to be ensured prior to triggering action"""

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
