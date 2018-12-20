'''
Created on 07.03.2018

@author: christian
'''
import unittest
from freecivbot.utils.base_action import Action

class MockClient(object):
    def send_request(self, packet):
        print("Sending packet")
        print(packet)
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
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()