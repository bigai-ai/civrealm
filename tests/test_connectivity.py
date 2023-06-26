# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# #  Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
# import asyncio
from freeciv_gym.freeciv.civ_controller import CivController


def test_login_fail_with_underscore_in_name():
    controller = CivController('test_controller')
    controller.init_network()
    controller.lock_control()
    # assert False


# def main():
#     test_login_fail_with_underscore_in_name()


# if __name__ == '__main__':
#     main()
    

@pytest.fixture
def controller():
    controller = CivController('testcontroller')    
    yield controller
    controller.close()

# Test whether server is up
def test_server_up(controller):
    # There is a _detect_server_up() method inside init_network()
    controller.init_network()

# Test whether login is success
def test_login_success(controller):
    controller.init_network()
    controller.lock_control()



# # async def test_websocket_connection(websocket_client):
# #     await websocket_client.write_message("Hello")
# #     response = await websocket_client.read_message()
# #     assert response == "World"

# # def connect_success():
# #     assert(False)

# @pytest.mark.gen_test
# # @pytest.mark.asyncio
# async def test_controller_init_network(controller):
#     # assert(False)
#     # print(type(controller))
#     await controller.init_game()


# @pytest.mark.asyncio
# async def test_websocket_connection():
#     connection_event = asyncio.Event()
    
#     def connect_callback():
#         print('*************')
#         connection_event.set()

#     async def connect():
#         controller = CivController('test_controller')
#         controller.init_network()
#         async with controller.lock_control() as conn:            
#             connect_callback()

#     await connect()
#     await connection_event.wait()
#     assert connection_event.is_set()

# @pytest.mark.asyncio


# def test_game_login():
#     controller = CivController('test_controller')
#     controller.init_network()
#     controller.get_observations()

# def test_first_observation():
#     controller = CivController('test_controller')
#     controller.init_network()
#     obs = controller.get_observations()
#     assert(obs != None)

# class A:
#     def __init__(self):
#         self.b = B()

# class B:
#     # def my_function():
#     #     return "Original without self"

#     def my_function(self):
#         return "Original"

# def test_modify_function_of_b(monkeypatch):
#     # Create an instance of class A
#     a = A()

#     # Define a mock function for B
#     def mock_function(self):
#         return "Modified"

#     # Monkeypatch the function of object b within object a
#     monkeypatch.setattr(a.b, "my_function", mock_function)

#     # Call the modified function
#     result = a.b.my_function()
#     print(result)

#     # # Assert the result
#     # assert result == "Modified"