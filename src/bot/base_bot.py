'''
Created on 06.02.2018

@author: christian
'''
from mapping.map import DIR8_STAY
from random import random

ACTION_UNWANTED = 0
ACTION_WANTED = 1

class FreeCivBot:
    def __init__(self):
        self.turn = 0
        self.turn_history = []
        self.cur_state = {}
        self.action_options = {}
        self.action_wants = None
        self.game_turn = None

    def calculate_want_of_move(self, turn_no, turn_state, action_options):
        self.cur_state = turn_state
        self.action_options = action_options
        self.action_wants = {}

        bot_turns = len(self.turn_history)

        self.game_turn = turn_no

        if self.game_turn == bot_turns:
            self.turn_history.append({})
        elif self.game_turn == bot_turns + 1:
            pass
        else:
            raise Exception("Bot has not calculated some of the previous moves. \
                             Game turns: %i, Bot turns %i" % (self.game_turn+1, bot_turns))

        for key in self.cur_state.keys():
            if key == "turn":
                continue
            elif key == "city":
                self.action_wants[key] = self.calculate_city_actions(action_options[key])
            elif key == "unit":
                self.action_wants[key] = self.calculate_unit_actions(action_options[key])
            else:
                self.action_wants[key] = self.calculate_non_supported_actions(action_options[key])

            self.turn_history[self.game_turn][key] = (turn_state[key], action_options[key], self.action_wants[key])

        return self.action_wants

    def calculate_unit_actions(self, a_options):
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

    def calculate_city_actions(self, a_options):
        return self.calculate_non_supported_actions(a_options)

    def calculate_non_supported_actions(self, a_options):
        action_wants = {}
        if a_options != None and a_options != []:
            for a_actor in a_options:
                action_wants[a_actor] = {}
                for a_action in a_options[a_actor]:
                    action_wants[a_actor][a_action] = ACTION_UNWANTED
        return action_wants
