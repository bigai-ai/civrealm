'''
Created on 12.03.2018

@author: Christian - inspired by keon.io/ddqn
'''
# -*- coding: utf-8 -*-

from bot.base_bot import StateBot

REWARD_INVALID_ACTION = -10


class Agent_Bot(StateBot):
    def __init__(self, agent_class):
        StateBot.__init__(self)
        self.agents = {}
        self.done = {}
        self.batches = {}
        self.rewards = {}
        self.old_state = {}
        self.last_action = {}
        self.agent_class = agent_class

    def env_step(self, ctrl_type, item=None):
        next_state = self._turn_ctrls[ctrl_type].get_current_state_vec(self._turn_player, item)
        if ctrl_type in self.rewards and self.rewards[ctrl_type] == REWARD_INVALID_ACTION:
            reward = REWARD_INVALID_ACTION
        else:
            reward = self._turn_state["player"]["score"]
        done = False
        return next_state, reward, done

    def init_agent(self, ctrl_type, next_state, hidden_size=30):
        act_num = self._turn_opts[ctrl_type].get_num_actions()
        act_list = self._turn_opts[ctrl_type].get_action_list()
        state_num = next_state.size
        self.agents[ctrl_type] = self.agent_class(state_num, act_num, act_list, hidden_size)
        self.batches[ctrl_type] = 32
        self.last_action[ctrl_type] = None

    def calculate_city_actions(self):
        return self.calculate_list_action_actions("city", 30)

    def calculate_unit_actions(self):
        return self.calculate_list_action_actions("unit", 40)

    def _update_state_info(self, ctrl_type, next_state, reward, done):
        self.old_state[ctrl_type] = next_state
        self.rewards[ctrl_type] = reward
        self.done[ctrl_type] = done

    def calculate_list_action_actions(self, ctrl_type, hidden_size=30):
        focus_actor = self.cur_state["actor"]
        cur_actors = self._turn_opts[ctrl_type].get_actors()

        if focus_actor is None:
            if cur_actors == []:
                return self._go_to_next_ctrl()
            else:
                self.cur_state["actor"] = 0
                focus_actor = 0
        elif focus_actor >= len(cur_actors):
            return self._go_to_next_ctrl()

        if not self._turn_opts[ctrl_type]._can_actor_act(cur_actors[focus_actor]):
            return {"ctrl": self.cur_state["ctrl"], "actor": focus_actor + 1}

        next_state, reward, done = self.env_step(ctrl_type, cur_actors[focus_actor])

        if ctrl_type not in self.agents:
            self.init_agent(ctrl_type, next_state, hidden_size)
        else:
            actor_id, action_num = self.last_action[ctrl_type]
            self.agents[ctrl_type].remember(self.old_state[ctrl_type], action_num,
                                            reward, next_state, done)

            if len(self.agents[ctrl_type].memory) > self.batches[ctrl_type]:
                self.agents[ctrl_type].replay(self.batches[ctrl_type])

        self._update_state_info(ctrl_type, next_state, reward, done)

        action_id, action_num, prob = self.agents[ctrl_type].act(self.old_state[ctrl_type],
                                                                 self.rewards[ctrl_type],
                                                                 cur_actors[focus_actor],
                                                                 self._turn_opts[ctrl_type])

        print("Found highest probability for: %s %f" % (action_id, prob))
        if prob < 0.25:
            print("Highest probability for - Ignoring: %s %f" % (action_id, prob))
            return {"ctrl": self.cur_state["ctrl"], "actor": focus_actor + 1}

        act_valid = self._turn_opts[ctrl_type].trigger_single_action(cur_actors[focus_actor], action_id)
        if act_valid is None:
            return {"ctrl": self.cur_state["ctrl"], "actor": focus_actor + 1}

        self.last_action[ctrl_type] = (cur_actors[focus_actor], action_num)
        if not act_valid:
            self.rewards[ctrl_type] = REWARD_INVALID_ACTION
            return self.calculate_list_action_actions(ctrl_type, hidden_size)
        else:
            self.rewards[ctrl_type] = reward
            print("Valid action")
            return {"ctrl": self.cur_state["ctrl"], "actor": focus_actor}
