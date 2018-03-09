'''
Created on 06.02.2018

@author: christian
'''

from time import sleep

ACTION_UNWANTED = 0
ACTION_WANTED = 1

class BaseBot:
    def __init__(self):
        self.turn = 0
        self.turn_history = []
        self.cur_state = {}
        self.action_options = {}
        self.action_wants = None
        self.game_turn = None
    
    def _acquire_state(self, pplayer, info_controls):
        print("Acquiring state and action options for: ")
        turn_state = {}
        turn_opts = {}
        for ctrl_type in info_controls:
            print("....: " + ctrl_type)
            ctrl = info_controls[ctrl_type]
            turn_state[ctrl_type] = ctrl.get_current_state(pplayer)
            turn_opts[ctrl_type] = ctrl.get_current_options(pplayer)
        
        return turn_state, turn_opts
    
    def _conduct_moves(self, info_controls, turn_opts, turn_wants):
        print("Carry out controller moves")
        for ctrl_type in info_controls:
            turn_opts[ctrl_type].trigger_wanted_actions(turn_wants[ctrl_type])

    def _save_history(self, turn_no, turn_state, turn_opts, turn_wants):
        bot_turns = len(self.turn_history)
        self.game_turn = turn_no

        if self.game_turn == bot_turns:
            self.turn_history.append({})
        elif self.game_turn == bot_turns + 1:
            self.turn_history.append({})
        else:
            raise Exception("Bot has not calculated some of the previous moves. \
                             Game turns: %i, Bot turns %i" % (self.game_turn+1, bot_turns))
        
        for key in turn_state.keys():
            self.turn_history[self.game_turn-1][key] = (turn_state[key], turn_opts[key], turn_wants[key])

    def conduct_turn(self, pplayer, info_controls):
        '''
        Main starting point for Freeciv-web Bot - to be called when game is ready
        '''
        print("Starting Turn")
        self.turn += 1
        turn_state, turn_opts = self._acquire_state(pplayer, info_controls)
        turn_wants = self._calculate_want_of_move(self.turn, turn_state, turn_opts)
        self._conduct_moves(info_controls, turn_opts, turn_wants)
        self._save_history(self.turn, turn_state, turn_opts, turn_wants)
        
        print("Finish turn - sleep for 4 seconds")
        sleep(4)

    def _calculate_want_of_move(self, turn_no, turn_state, action_options):
        print("Bot calculates want for controller moves")
        self.cur_state = turn_state
        self.action_options = action_options
        self.action_wants = {}
        
        for key in self.cur_state.keys():
            if key == "turn":
                continue
            elif key == "city":
                want = self.calculate_city_actions(turn_no, turn_state, action_options[key])
            elif key == "unit":
                want = self.calculate_unit_actions(turn_no, turn_state, action_options[key])
            elif key == "player":
                want = self.calculate_player_actions(turn_no, turn_state, action_options[key])
            elif key == "dipl":
                want = self.calculate_dipl_actions(turn_no, turn_state, action_options[key])
            elif key == "tech":
                want = self.calculate_tech_actions(turn_no, turn_state, action_options[key])
            elif key == "gov":
                want = self.calculate_gov_actions(turn_no, turn_state, action_options[key])
            else:
                want = self.calculate_non_supported_actions(action_options[key])
            
            self.action_wants[key] = want
        return self.action_wants
    
    def calculate_non_supported_actions(self, a_options):
        """Ensures that non supported actions are "UNWANTED", i.e., will not be triggered"""
        action_wants = {}
        if a_options != None:
            for a_actor in a_options.get_actors():
                action_wants[a_actor] = {}
                for a_action in a_options.get_actions(a_actor):
                    action_wants[a_actor][a_action] = ACTION_UNWANTED
        return action_wants
    
    def calculate_city_actions(self, turn_no, full_state, action_options):
        return self.calculate_non_supported_actions(action_options)
    
    def calculate_unit_actions(self, turn_no, full_state, action_options):
        return self.calculate_non_supported_actions(action_options)
    
    def calculate_player_actions(self, turn_no, full_state, action_options):
        return self.calculate_non_supported_actions(action_options)
    
    def calculate_dipl_actions(self, turn_no, full_state, action_options):
        return self.calculate_non_supported_actions(action_options)
    
    def calculate_tech_actions(self, turn_no, full_state, action_options):
        return self.calculate_non_supported_actions(action_options)
    
    def calculate_gov_actions(self, turn_no, full_state, action_options):
        return self.calculate_non_supported_actions(action_options)