'''
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
'''

import json
import websocket
import urllib
import docker
from tornado import ioloop
from math import ceil
from time import sleep

from freecivbot.connectivity.webclient import WebSocketClient
from freecivbot.utils.fc_types import packet_chat_msg_req
from freecivbot import init_server

from freecivbot.utils.freeciv_logging import logger


class CivWSClient(WebSocketClient):
    def __init__(self, civ_controller, **kwargs):
        WebSocketClient.__init__(self, **kwargs)
        self.civ_controller = civ_controller
        self.read_packs = []
        self.wait_for_packs = []
        self.send_queue = []

    def _on_message(self, msg):
        # TODO: Add logging for server messages
        self.read_packs = json.loads(msg)
        packet_id_list = []
        for p in self.read_packs:
            if p is None:
                continue
            packet_id_list.append(p['pid'])
        logger.info(('Received packets id: ', packet_id_list))
        self.civ_controller.assign_packets(self.read_packs)
        self.read_packs = []
        self.clear_send_queue()
        logger.info(('Wait_for_packs: ', self.wait_for_packs))

    def _on_connection_success(self):
        logger.info('Connected!')
        self.civ_controller.init_control(self)

    def _on_connection_close(self):
        logger.info('Connection to server is closed. Please reload the page to restart. Sorry!')

    def _on_connection_error(self, exception):
        logger.info('Network error', 'Problem %s occured with the ' % exception + self.ws_conn.protocol +
                    ' WebSocket connection to the server: ' + self.ws_conn.request.url)

    def send_request(self, packet_payload, wait_for_pid=None):
        '''
        Sends a request to the server, with a JSON packet.
        '''
        self.send_queue.append(packet_payload)
        # logger.info('Before send_request', self.read_packs)
        if wait_for_pid is not None:
            self.wait_for_packs.append(wait_for_pid)
        if self.read_packs == []:
            return self.clear_send_queue()
        else:
            return -1

    def send_message(self, message):
        packet = {'pid': packet_chat_msg_req,
                  'message': message}
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

    def close(self):
        self.send_queue = []
        self.wait_for_packs = []
        self.read_packs = []
        WebSocketClient.close(self)
        ioloop.IOLoop.instance().stop()

    def is_waiting_for_responses(self):
        return len(self.wait_for_packs) > 0

    def stop_waiting(self, pid):
        try:
            self.wait_for_packs.remove(pid)
        except ValueError:
            pass

class CivConnection():
    def __init__(
            self, civ_controller, base_url='http://localhost', restart_server_if_down=True, wait_for_server=120,
            retry_interval=5):
        '''
            restart_server_if_down - True if server should be restarted if down
            wait_for_server - Overall time waiting for server being up
            retry_interval - Wait for X seconds until retrying
        '''
        self.civserverport = civ_controller.client_port
        self.civ_controller = civ_controller
        self.proxyport = 1000 + self.civserverport
        self.base_url = base_url
        self._restart_server_if_down = restart_server_if_down
        self._retry_interval = retry_interval
        self._num_retries = int(ceil(wait_for_server/retry_interval))

        self._restarting_server = False
        self._cur_retry = 0

        self.network_init()

    def _retry(self):
        self._cur_retry += 1
        sleep(self._retry_interval)
        return self._detect_server_up()

    def _detect_server_up(self):
        try:
            ws = websocket.WebSocket()
            # , http_proxy_host='proxy_host_name', http_proxy_port=3128)
            ws.connect('ws://localhost:8080/civsocket/%i' % self.proxyport)
            return True
        except Exception as err:
            logger.info('Connect not successful:' + str(err) + ' retrying in %s seconds.' % self._retry_interval)
            if self._restart_server_if_down and not self._restarting_server:
                self._restart_server()
                return self._detect_server_up()

            if self._cur_retry < self._num_retries:
                return self._retry()

            return False

    def network_init(self):
        self._cur_retry = 0
        self._restarting_server = False
        logger.info('Connecting to server at %s ...' % self.base_url)
        if self._detect_server_up():
            self.websocket_init()
        else:
            logger.info('Connection could not be established!')

    def websocket_init(self):
        '''
          Initialized the WebSocket connection.
        '''
        civ_ws_client = CivWSClient(self.civ_controller)
        civ_ws_client.connect('ws://localhost:8080/civsocket/%i' % self.proxyport)

        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            civ_ws_client.close()

    def _restart_server(self):
        try:
            self._restarting_server = True
            init_server.init_freeciv_docker()
        except docker.errors.APIError as err:
            logger.info(err)
            logger.info('---------------------------')
            logger.info('Most likely key ports (80, 8080, 6000-3, 7000-3) on host machine are blocked by existing processes!')
            logger.info('Run: sudo netstat -pant to identify respective processes (e.g., nginx, Apache)')
            logger.info('and kill them via htop, top, or "kill process_pid"')
            logger.info('---------------------------')
            exit()
