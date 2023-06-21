"""Simple Web socket client implementation using Tornado framework.
"""

import json
from typing import final
from tornado import httpclient
from tornado import httputil
from tornado import websocket
from tornado import ioloop

APPLICATION_JSON = 'application/json'

DEFAULT_CONNECT_TIMEOUT = 300
DEFAULT_REQUEST_TIMEOUT = 300


class WebSocketClient(object):
    """Base for web socket clients.
    """

    def __init__(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                 request_timeout=DEFAULT_REQUEST_TIMEOUT):
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self._ws_connection = None
        self._connection_closed = False

    @final
    def connect(self, url):
        """Connect to the server.
        :param str url: server URL.
        """
        headers = httputil.HTTPHeaders({'Content-Type': APPLICATION_JSON})
        request = httpclient.HTTPRequest(url=url,
                                         connect_timeout=self.connect_timeout,
                                         request_timeout=self.request_timeout,
                                         headers=headers)
        websocket.websocket_connect(request, callback=self._connect_callback, on_message_callback=self._on_message)

    @final
    def start_ioloop(self):
        """Start IO/Event loop.

        This method will block current thread, and only return after self.stop_loop() is called in a callback. The function should be started everytime the user wants to resume listening to the server or sending messages to the server.
        """
        if self._connection_closed:
            # This happens when the connection was closed intentionally before the call to start_loop, e.g., the user pressed Ctrl+C to stop the client, or the server closed the connection.
            return

        try:
            ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            self.close()

    @final
    def stop_ioloop(self):
        ioloop.IOLoop.current().stop()

    @final
    def send(self, data):
        """Send message to the server
        :param str data: message.
        """
        if not self._ws_connection:
            raise RuntimeError('Web socket connection is closed.')
        # TODO: check if we need to clear empty spaces
        msg = json.dumps(data)
        ret_future = self._ws_connection.write_message(msg)

    @final
    def close(self):
        """Close connection.
        """
        if not self._ws_connection:
            raise RuntimeError('Web socket connection is already closed.')

        self._connection_closed = True
        self._on_connection_close()
        self._ws_connection.close()
        ioloop.IOLoop.current().stop()

    @final
    def _connect_callback(self, future):
        if future.exception() is None:
            self._ws_connection = future.result()
            self._on_connection_success()
        else:
            self._on_connection_error(future.exception())

    def _on_message(self, message):
        """This is called when new message is available from the server.
        :param str msg: server message.
        """
        pass

    def _on_connection_success(self):
        """This is called on successful connection ot the server.
        """
        pass

    def _on_connection_close(self):
        """This is called when server closed the connection.
        This is called before socket is closed, should be overriden to clean up data before closing the connection. 
        """
        pass

    def _on_connection_error(self, exception):
        """This is called in case if connection to the server could
        not established.
        """
        pass
