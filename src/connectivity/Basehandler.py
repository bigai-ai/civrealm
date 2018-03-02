'''
Created on 29.12.2017

@author: christian
'''

class CivEvtHandler():
    def __init__(self, ws_client):
        self.hdict = {}
        self.ws_client = ws_client

    def register_with_parent(self, parent):
        for key in self.hdict.keys():
            if key in parent.hdict:
                raise Exception("Event already controlled by Parent: %s" % key)
            parent.hdict[key] = self.hdict[key]

    def register_handler(self, pid, func):
        self.hdict[pid] = (self, func)

    def handle_pack(self, pid, data):
        if pid in self.hdict:
            handle_func = getattr(self.hdict[pid][0], self.hdict[pid][1])
            handle_func(data)
        else:
            print("Handler function for pid %i not yet implemented" % pid)

    def get_current_state(self, pplayer):
        return None

    def get_current_options(self, pplayer):
        return None
