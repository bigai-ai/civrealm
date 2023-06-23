
from freecivbot.utils.freeciv_logging import logger

ACTION_UNWANTED = 0
ACTION_WANTED = 1


class BaseBot:
    def __init__(self):
        self.turn_history = []

        self._turn_active = False
        self._turn_player = None
        self._turn_ctrls = None
        self._turn_state = None
        self._turn_opts = None
        self._end_turn_hook = None

        self.cur_state = {}
        self.action_options = {}
        self.action_wants = None
        self.game_turn = None
        self._end_game = False

    def close_game(self):
        self._end_game = True

    def wants_to_end(self):
        return self._end_game

    def _acquire_ctrl_state(self, ctrl_type):
        ctrl = self._turn_ctrls[ctrl_type]
        self._turn_state[ctrl_type] = ctrl.get_current_state(self._turn_player)
        self._turn_opts[ctrl_type] = ctrl.get_current_options(self._turn_player)

    def _acquire_state(self):
        logger.debug("Acquiring state and action options for: ")
        for ctrl_type in self._turn_ctrls:
            logger.debug("....: " + ctrl_type)
            self._acquire_ctrl_state(ctrl_type)

    def _conduct_moves(self, turn_wants):
        logger.info("Carry out controller moves")
        for ctrl_type in self._turn_ctrls:
            self._turn_opts[ctrl_type].trigger_wanted_actions(turn_wants[ctrl_type])

    def _save_history(self, turn_wants):
        bot_turns = len(self.turn_history)
        self.game_turn = self.civ

        if self.game_turn == bot_turns:
            self.turn_history.append({})
        elif self.game_turn == bot_turns + 1:
            self.turn_history.append({})
        else:
            raise Exception("Bot has not calculated some of the previous moves. \
                             Game turns: %i, Bot turns %i" % (self.game_turn+1, bot_turns))

        for key in self._turn_state.keys():
            self.turn_history[self.game_turn-1][key] = (self._turn_state[key],
                                                        self._turn_opts[key], turn_wants[key])

    def calculate_next_move(self):
        logger.info(('Bot calculates next move, turn_active: ', self._turn_active))
        if self._turn_active:
            self._acquire_state()
            turn_wants = self._calculate_want_of_move()
            self._conduct_moves(turn_wants)
            self._save_history(turn_wants)
            self.end_turn()

    def conduct_turn(self, pplayer, info_controls, end_turn_hook):
        '''
        Main starting point for Freeciv-web Bot - to be called when game is ready
        '''
        logger.info("Starting Turn")
        self._turn_active = True
        self._turn_ctrls = info_controls
        self._turn_player = pplayer
        self._turn_state = {}
        self._turn_opts = {}
        self._end_turn_hook = end_turn_hook

    def end_turn(self):
        logger.info("Finish turn - sleep for 4 seconds")
        self._turn_active = False
        self._turn_ctrls = None
        self._turn_player = None
        self._turn_state = None
        self._turn_opts = None
        self._end_turn_hook()

    def _calculate_want_of_move_of_ctrl(self, ctrl_type):
        if ctrl_type == "turn":
            return {}
        elif ctrl_type == "city":
            return self.calculate_city_actions()
        elif ctrl_type == "unit":
            return self.calculate_unit_actions()
        elif ctrl_type == "player":
            return self.calculate_player_actions()
        elif ctrl_type == "dipl":
            return self.calculate_dipl_actions()
        elif ctrl_type == "tech":
            return self.calculate_tech_actions()
        elif ctrl_type == "gov":
            return self.calculate_gov_actions()
        else:
            return self.calculate_non_supported_actions(self._turn_opts[ctrl_type])

    def _calculate_want_of_move(self):
        logger.info("Bot calculates want for controller moves")
        self.action_wants = {}

        for key in self._turn_ctrls.keys():
            self.action_wants[key] = self._calculate_want_of_move_of_ctrl(key)
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

    def calculate_city_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["city"])

    def calculate_unit_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["unit"])

    def calculate_player_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["player"])

    def calculate_dipl_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["dipl"])

    def calculate_tech_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["tech"])

    def calculate_gov_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["gov"])


class StateBot(BaseBot):
    def __init__(self):
        BaseBot.__init__(self)
        self.cur_state = {"ctrl": None,
                          "actor": None}
        self.ctrl_types = None

    def _acquire_ctrl_state(self, ctrl_type):
        ctrl = self._turn_ctrls[ctrl_type]
        self._turn_state[ctrl_type] = ctrl.get_current_state(self._turn_player)
        self._turn_opts[ctrl_type] = ctrl.get_current_options(self._turn_player)

    def _acquire_state(self):
        logger.info("Acquiring state and action options for: ")
        for ctrl_type in self._turn_ctrls:
            logger.info("....: " + ctrl_type)
            self._acquire_ctrl_state(ctrl_type)

    def calculate_next_move(self):
        if self._turn_active:
            self.update_state()
            new_state = self._calculate_want_of_move_of_ctrl(self.ctrl_types[self.cur_state["ctrl"]])
            if self.change_state(new_state):
                self.end_turn()
            else:
                logger.info(len(self._turn_ctrls["game"].ws_client.send_queue))

                if len(self._turn_ctrls["game"].ws_client.send_queue) == 0:
                    self.calculate_next_move()

    def conduct_turn(self, pplayer, info_controls, end_turn_hook):
        BaseBot.conduct_turn(self, pplayer, info_controls, end_turn_hook)
        self.ctrl_types = info_controls.keys()
        self.change_state({"ctrl": 0, "actor": None})

    def change_state(self, new_state):
        logger.info(new_state, self.cur_state)
        end_turn = False
        if new_state["ctrl"] != self.cur_state["ctrl"]:
            if new_state["ctrl"] >= len(self.ctrl_types):
                end_turn = True
            else:
                self._acquire_ctrl_state(self.ctrl_types[new_state["ctrl"]])
                self.cur_state = new_state
        elif new_state["actor"] != self.cur_state["actor"]:
            self.cur_state = new_state
        return end_turn

    def update_state(self):
        self._acquire_ctrl_state(self.ctrl_types[self.cur_state["ctrl"]])

    def _go_to_next_ctrl(self):
        return {"ctrl": self.cur_state["ctrl"] + 1, "actor": None}

    def _calculate_want_of_move_of_ctrl(self, ctrl_type):
        logger.info(ctrl_type)
        if ctrl_type in ["turn", "map", "rules", "options", "game", "client"]:
            return self._go_to_next_ctrl()
        else:
            return BaseBot._calculate_want_of_move_of_ctrl(self, ctrl_type)

    def calculate_dipl_actions(self):
        return self._go_to_next_ctrl()

    def calculate_gov_actions(self):
        return self._go_to_next_ctrl()

    def calculate_player_actions(self):
        return self._go_to_next_ctrl()

    def calculate_tech_actions(self):
        return self._go_to_next_ctrl()
