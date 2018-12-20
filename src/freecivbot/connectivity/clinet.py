"""
***********************************************************************
    Freeciv-web - the web version of Freeciv. http://play.freeciv.org/
    Copyright (C) 2009-2015  The Freeciv-web project

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

***********************************************************************
"""

import json
from tornado import ioloop
from freecivbot.connectivity.webclient import WebSocketClient
from freecivbot.utils.fc_types import packet_chat_msg_req

class CivWSClient(WebSocketClient):
    def __init__(self,civ_client,**kwargs):
        WebSocketClient.__init__(self, **kwargs)
        self.civ_client = civ_client
        self.read_packs = []
        self.send_queue = []

    def _on_message(self, msg):
        self.read_packs = json.loads(msg)
        self.civ_client.assign_packets(self.read_packs)
        self.read_packs = []
        self.clear_send_queue()

    def _on_connection_success(self):
        print('Connected!')
        self.civ_client.init_control(self)

    def _on_connection_close(self):
        print('Connection to server is closed. Please reload the page to restart. Sorry!')

    def _on_connection_error(self, exception):
        print("Network error", "Problem %s occured with the " % exception + self.ws_conn.protocol +
              " WebSocket connection to the server: " + self.ws_conn.request.url)

    def send_request(self, packet_payload):
        """
        Sends a request to the server, with a JSON packet.
        """
        self.send_queue.append(packet_payload)
        if self.read_packs == []:
            return self.clear_send_queue()
        else:
            return -1

    def send_message(self, message):
        packet = {"pid" : packet_chat_msg_req,
                  "message" : message}
        self.send_request(packet)

    def clear_send_queue(self):
        msges = len(self.send_queue)
        if msges == 1:
            self.send(self.send_queue[0])
        elif msges == 0:
            pass
        else:
            for pack in self.send_queue:
                self.send(pack)
        self.send_queue = []
        return msges

class CivConnection():
    def __init__(self, civclient, base_url='http://localhost'):
        self.civserverport = civclient.client_port
        self.client = civclient
        self.proxyport= 1000 + self.civserverport
        self.base_url = base_url
        self.network_init()

    def network_init(self):
        """
            with sessions.Session() as session:
            civclient_request_url = base_url + "/civclientlauncher"
            civclient_request_url = "&civserverport=" + str(civserverport)
            req = session.request(method="POST", url=civclient_request_url)
        """

        self.websocket_init()
        #load_game_check()
        #setInterval(ping_check, pingtime_check)

    def websocket_init(self):
        '''
          Initialized the WebSocket connection.
        '''
        client = CivWSClient(self.client)
        client.connect('ws://localhost/civsocket/%i' % self.proxyport)

        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            client.close()

