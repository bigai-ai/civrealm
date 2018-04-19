'''
Created on 23.03.2018

@author: christian
'''
import random
import numpy as np

from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from keras import backend as K

from civclient import CivClient
from connectivity.clinet import CivConnection

class DQNAgent:
    def __init__(self, state_size, action_size, action_ids, numH):
        self.state_size = state_size
        self.action_size = action_size
        self.numH = numH
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 0.1  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99
        self.learning_rate = 0.001
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
        self.action_ids = action_ids

    def _huber_loss(self, target, prediction):
        # sqrt(1+error^2)-1
        error = prediction - target
        return K.mean(K.sqrt(1+K.square(error))-1, axis=-1)

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(self.numH, input_dim=self.state_size, activation='relu'))
        model.add(Dense(self.numH, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss=self._huber_loss,
                      optimizer=Adam(lr=self.learning_rate))
        return model

    def update_target_model(self):
        # copy weights from model to target_model
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, reward, actor_id, action_list):
        valid_acts = action_list.get_valid_actions(actor_id, self.action_ids)
        if np.random.rand() <= self.epsilon or reward == REWARD_INVALID_ACTION:
            act_values = np.multiply(np.array(valid_acts),np.random.uniform(size=self.action_size))
        else:
            act_values = np.multiply(np.array(valid_acts),self.model.predict(state)[0])
        
        ix = np.argmax(act_values)
        imax = act_values[ix]
        id_max = self.action_ids[ix]
        
        return id_max, ix, imax  # returns action

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, a_action, reward, next_state, done in minibatch:
            target = self.model.predict(state)
            if done:
                target[0][a_action] = reward
            else:
                a = self.model.predict(next_state)[0]
                t = self.target_model.predict(next_state)[0]
                target[0][a_action] = reward + self.gamma * t[np.argmax(a)]
            self.model.fit(state, target, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)

from bot.dqn_bot import Agent_Bot, REWARD_INVALID_ACTION

my_bot = Agent_Bot(DQNAgent)
my_civ_client = CivClient(my_bot, "chrisrocks", client_port=6000)
CivConnection(my_civ_client, 'http://localhost')