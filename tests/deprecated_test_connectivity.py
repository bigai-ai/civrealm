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


import pytest
# import asyncio
from civrealm.freeciv.civ_controller import CivController

import pytest
import asyncio
import tornado.ioloop

# @pytest.fixture
# def event_loop():
#     loop = tornado.ioloop.IOLoop()
#     yield loop
#     loop.close()


# The callback function that raises an exception
# def callback():
#     time.sleep(2)
#     raise RuntimeError("Log in rejected")

# # The test function
# @pytest.mark.asyncio
# async def test_callback_exception():
#     with pytest.raises(RuntimeError):
#         await asyncio.sleep(0)  # Allow other coroutines to run
#         callback()


# def callback():
#     print('aaa')
#     tornado.ioloop.IOLoop.current().stop()
#     raise RuntimeError(f"Log in rejected")

# def test_main():
#     # Schedule the callback to be executed after 2 seconds
#     tornado.ioloop.IOLoop.current().call_later(2, callback)
#     # Start the event loop
#     try:
#         tornado.ioloop.IOLoop.current().start()
#     except RuntimeError as e:
#         pytest.fail(str(e))  # Fail the test if an exception occurs


# @pytest.mark.asyncio
# async def test_login_fail_with_underscore_in_name(event_loop):
#     event = asyncio.Event()
#     controller = CivController(fc_args['username'])
#     controller.init_network()
#     with pytest.raises(Exception):
#         await event.wait()

# from tornado import httpclient
# from tornado import httputil
# from tornado import websocket
# @pytest.mark.asyncio
# async def test_login_fail_with_underscore_in_name():
#     event = asyncio.Event()
#     controller = CivController('test_controller')
#     controller.ws_client.ws_address
#     headers = httputil.HTTPHeaders({'Content-Type': 'application/json'})
#     request = httpclient.HTTPRequest(url=controller.ws_client.ws_address,
#                                          connect_timeout=300,
#                                          request_timeout=300,
#                                          headers=headers)
#     with pytest.raises(Exception):
#         websocket.websocket_connect(request, callback=controller.ws_client._connect_callback, on_message_callback=controller.ws_client._on_message)
#         await event.wait()
# controller.lock_control()


def test_get_first_obs_fail_with_underscore_in_name():
    controller = CivController('test_controller')
    controller.init_network()
    with pytest.raises(Exception):
        controller.get_info_and_observation()
        controller.end_game()
        # controller.lock_control()


# def main():
#     test_login_fail_with_underscore_in_name()


# if __name__ == '__main__':
#     main()


# @pytest.fixture
# def controller():
#     controller = CivController(fc_args['username'])
#     yield controller
#     controller.close()

# # Test whether server is up
# def test_server_up(controller):
#     # There is a _detect_server_up() method inside init_network()
#     controller.init_network()

# # Test whether login is success
# def test_login_success(controller):
#     controller.init_network()
#     controller.lock_control()
