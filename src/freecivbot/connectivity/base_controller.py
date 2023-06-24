# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from freecivbot.connectivity.civ_connection import CivConnection

from freecivbot.utils.base_action import ActionList
from freecivbot.utils.base_state import PropState

from freecivbot.utils.freeciv_logging import logger


class CivPropController():
    """ Controller for certain properties of the Civilization "Board
        The controller processes messages from the freeciv server (e.g., stores data)
        and can send information back to  
    """

    def __init__(self, ws_client: CivConnection):
        self.hdict = {}
        self.ws_client = ws_client
        self.prop_state = PropState()
        self.prop_actions = ActionList(ws_client)
        self.register_all_handlers()

        # Packets that are filtered when logging debug messages
        self.unlogged_packets = set()
        # Packet id 165 are informative packets about server commands
        server_setting_packets = {165, 166, 167, 168, 169, 170}
        ruleset_packets = {148, 246, 143, 229, 140, 260, 144, 235, 226, 152,
                           175, 232, 151, 150, 149, 240, 512, 145, 230, 227, 252, 228, 177}
        info_packets = {15, 51}
        self.unlogged_packets = self.unlogged_packets.union(ruleset_packets, server_setting_packets, info_packets)

    def register_all_handlers(self):
        raise Exception(f'Abstract function - To be overwritten by {self.__class__}')

    def register_with_parent(self, parent):
        for key in self.hdict.keys():
            if key in parent.hdict:
                raise Exception("Event already controlled by Parent: %s" % key)
            parent.hdict[key] = self.hdict[key]

    def register_handler(self, pid, func):
        self.hdict[pid] = (self, func)

    def handle_pack(self, pid, data):
        if pid in self.hdict:
            if pid not in self.unlogged_packets:
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
