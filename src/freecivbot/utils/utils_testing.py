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

import unittest
from freecivbot.utils.base_action import Action

from freecivbot.utils.freeciv_logging import logger


class MockClient(object):
    def send_request(self, packet):
        logger.info("Sending packet")
        logger.info(packet)
        return 1


class TestAction(Action):
    def __init__(self, ws_client, state):
        Action.__init__(self, ws_client)
        self.state = state

    def is_action_valid(self):
        return self.state != -1

    def _action_packet(self):
        return {"testmsg": "Test packet sending..."}


class TestBaseAction(unittest.TestCase):

    def setUp(self):
        self.ws_client = MockClient()

    def testAction(self):
        act_test_1 = TestAction(self.ws_client, -1)
        self.assertEqual(act_test_1.is_action_valid(), False)
        act_test_2 = TestAction(self.ws_client, -2)
        self.assertEqual(act_test_2.is_action_valid(), True)
        self.assertEqual(act_test_2.trigger_action(), 1)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
