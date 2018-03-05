'''
Created on 05.03.2018

@author: christian
'''
from bot.base_bot import ACTION_WANTED, ACTION_UNWANTED, BaseBot
from mapping.map_ctrl import DIR8_STAY
from random import random
from civclient import CivClient
from connectivity.clinet import CivConnection

class SimpleBot(BaseBot):
    def calculate_unit_actions(self, turn_no, full_state, a_options):
        action_wants = {}
        for punit in a_options: 
            action_wants[punit] = {}
            for a_option in a_options[punit]:
                if a_options[punit][a_option] is None:
                    continue
                if a_option[1] == DIR8_STAY and a_option[0] in ["explore"]:
                    action_wants[punit][a_option] = ACTION_WANTED
                elif a_option[1] != DIR8_STAY and a_option[0] == "goto":
                    action_wants[punit][a_option] = ACTION_WANTED*random()*0.25
                elif a_option[1] == DIR8_STAY and a_option[0] == "build":
                    action_wants[punit][a_option] = ACTION_WANTED*random()*0.75
                else:
                    action_wants[punit][a_option] = ACTION_UNWANTED
        return action_wants

my_bot = SimpleBot()
my_civ_client = CivClient(my_bot, "chrisrocks", client_port=6000)
CivConnection(my_civ_client, 'http://localhost')