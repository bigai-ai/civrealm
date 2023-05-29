'''
Created on 23.03.2018

@author: christian
'''

from bot.dqn_bot import Agent_Bot, REWARD_INVALID_ACTION
from civclient import CivClient
from connectivity.clinet import CivConnection

import numpy as np

import cPickle as pickle
import tensorflow as tf
import matplotlib.pyplot as plt
import math


class ModelAgent:
    def __init__(self, state_size, action_size, action_ids, numH):
        self.state_size = state_size
        self.action_size = action_size
        self.Hmodel = numH*4
        self.Hpolicy = numH
        self.action_ids = action_ids

        self.gamma = 0.99    # discount rate
        self.decay_rate = 0.99  # decay factor for RMSProp leaky sum of grad^2
        self.learning_rate = 1e-2

        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()

        model_bs = 3  # Batch size when learning from model
        real_bs = 3  # Batch size when learning from real environment

        self.xs, self.drs, self.ys, self.ds = [], [], [], []
        self.running_reward = None
        self.reward_sum = 0
        self.episode_number = 1
        self.real_episodes = 1

        self.batch_size = real_bs

        drawFromModel = False  # When set to True, will use model for observations
        trainTheModel = True  # Whether to train the model
        trainThePolicy = False  # Whether to train the policy
        switch_point = 1

    def _build_policy_network(self):
        tf.reset_default_graph()
        observations = tf.placeholder(tf.float32, [None, self.state_size], name="input_x")
        W1 = tf.get_variable("W1", shape=[self.state_size, self.Hpolicy],
                             initializer=tf.contrib.layers.xavier_initializer())
        layer1 = tf.nn.relu(tf.matmul(observations, W1))
        W2 = tf.get_variable("W2", shape=[self.Hpolicy, 1], initializer=tf.contrib.layers.xavier_initializer())
        score = tf.matmul(layer1, W2)
        probability = tf.nn.sigmoid(score)

        tvars = tf.trainable_variables()
        input_y = tf.placeholder(tf.float32, [None, 1], name="input_y")
        advantages = tf.placeholder(tf.float32, name="reward_signal")
        adam = tf.train.AdamOptimizer(learning_rate=self.learning_rate)
        W1Grad = tf.placeholder(tf.float32, name="batch_grad1")
        W2Grad = tf.placeholder(tf.float32, name="batch_grad2")
        batchGrad = [W1Grad, W2Grad]
        loglik = tf.log(input_y*(input_y - probability) + (1 - input_y)*(input_y + probability))
        loss = -tf.reduce_mean(loglik * advantages)
        newGrads = tf.gradients(loss, tvars)
        updateGrads = adam.apply_gradients(zip(batchGrad, tvars))

    def _build_model_network(self):
        input_data = tf.placeholder(tf.float32, [None, self.state_size+1])
        with tf.variable_scope('rnnlm'):
            softmax_w = tf.get_variable("softmax_w", [self.Hmodel, 50])
            softmax_b = tf.get_variable("softmax_b", [50])

        previous_state = tf.placeholder(tf.float32, [None, 5], name="previous_state")
        W1M = tf.get_variable("W1M", shape=[5, self.Hmodel],
                              initializer=tf.contrib.layers.xavier_initializer())
        B1M = tf.Variable(tf.zeros([mH]), name="B1M")
        layer1M = tf.nn.relu(tf.matmul(previous_state, W1M) + B1M)
        W2M = tf.get_variable("W2M", shape=[mH, mH],
                              initializer=tf.contrib.layers.xavier_initializer())
        B2M = tf.Variable(tf.zeros([mH]), name="B2M")
        layer2M = tf.nn.relu(tf.matmul(layer1M, W2M) + B2M)
        wO = tf.get_variable("wO", shape=[mH, 4],
                             initializer=tf.contrib.layers.xavier_initializer())
        wR = tf.get_variable("wR", shape=[mH, 1],
                             initializer=tf.contrib.layers.xavier_initializer())
        wD = tf.get_variable("wD", shape=[mH, 1],
                             initializer=tf.contrib.layers.xavier_initializer())

        bO = tf.Variable(tf.zeros([4]), name="bO")
        bR = tf.Variable(tf.zeros([1]), name="bR")
        bD = tf.Variable(tf.ones([1]), name="bD")

        predicted_observation = tf.matmul(layer2M, wO, name="predicted_observation") + bO
        predicted_reward = tf.matmul(layer2M, wR, name="predicted_reward") + bR
        predicted_done = tf.sigmoid(tf.matmul(layer2M, wD, name="predicted_done") + bD)

        true_observation = tf.placeholder(tf.float32, [None, 4], name="true_observation")
        true_reward = tf.placeholder(tf.float32, [None, 1], name="true_reward")
        true_done = tf.placeholder(tf.float32, [None, 1], name="true_done")

        predicted_state = tf.concat([predicted_observation, predicted_reward, predicted_done], 1)

        observation_loss = tf.square(true_observation - predicted_observation)

        reward_loss = tf.square(true_reward - predicted_reward)

        done_loss = tf.multiply(predicted_done, true_done) + tf.multiply(1-predicted_done, 1-true_done)
        done_loss = -tf.log(done_loss)

        model_loss = tf.reduce_mean(observation_loss + done_loss + reward_loss)

        modelAdam = tf.train.AdamOptimizer(learning_rate=learning_rate)
        updateModel = modelAdam.minimize(model_loss)

    def _huber_loss(self, target, prediction):
        # sqrt(1+error^2)-1
        error = prediction - target
        return K.mean(K.sqrt(1+K.square(error))-1, axis=-1)

    def _build_model(self):
        # Launch the graph
        init = tf.global_variables_initializer()

        with tf.Session() as sess:

            self.rendering = False
            sess.run(init)
            observation = env.reset()
            x = observation
            gradBuffer = sess.run(tvars)
            gradBuffer = resetGradBuffer(gradBuffer)

        self._build_model_network()
        self._build_policy_network()

    def update_target_model(self):
        # copy weights from model to target_model
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, reward, actor_id, action_list):
        valid_acts = action_list.get_valid_actions(actor_id, self.action_ids)
        if np.random.rand() <= self.epsilon or reward == REWARD_INVALID_ACTION:
            act_values = np.multiply(np.array(valid_acts), np.random.uniform(size=self.action_size))
        else:
            tfprob = sess.run(probability, feed_dict={observations: state})
            act_values = np.multiply(np.array(valid_acts), tfprob)

        ix = np.argmax(act_values)
        imax = act_values[ix]
        id_max = self.action_ids[ix]

        return id_max, ix, imax  # returns action

        # step the  model or real environment and get new measurements
        if drawFromModel == False:
            observation, reward, done, info = env.step(action)
        else:
            observation, reward, done = stepModel(sess, xs, action)

        reward_sum += reward

        if done:

            if drawFromModel == False:
                real_episodes += 1
            episode_number += 1

            # stack together all inputs, hidden states, action gradients, and rewards for this episode
            epx = np.vstack(xs)
            epy = np.vstack(ys)
            epr = np.vstack(drs)
            epd = np.vstack(ds)
            xs, drs, ys, ds = [], [], [], []  # reset array memory

            if trainTheModel == True:
                actions = np.array([np.abs(y-1) for y in epy][:-1])
                state_prevs = epx[:-1, :]
                state_prevs = np.hstack([state_prevs, actions])
                state_nexts = epx[1:, :]
                rewards = np.array(epr[1:, :])
                dones = np.array(epd[1:, :])
                state_nextsAll = np.hstack([state_nexts, rewards, dones])

                feed_dict = {previous_state: state_prevs, true_observation: state_nexts,
                             true_done: dones, true_reward: rewards}
                loss, pState, _ = sess.run([model_loss, predicted_state, updateModel], feed_dict)
            if trainThePolicy == True:
                discounted_epr = discount_rewards(epr).astype('float32')
                discounted_epr -= np.mean(discounted_epr)
                discounted_epr /= np.std(discounted_epr)
                tGrad = sess.run(newGrads, feed_dict={observations: epx, input_y: epy, advantages: discounted_epr})

                # If gradients becom too large, end training process
                if np.sum(tGrad[0] == tGrad[0]) == 0:
                    break
                for ix, grad in enumerate(tGrad):
                    gradBuffer[ix] += grad

            if switch_point + batch_size == episode_number:
                switch_point = episode_number
                if trainThePolicy == True:
                    sess.run(updateGrads, feed_dict={W1Grad: gradBuffer[0], W2Grad: gradBuffer[1]})
                    gradBuffer = resetGradBuffer(gradBuffer)

                running_reward = reward_sum if running_reward is None else running_reward * 0.99 + reward_sum * 0.01
                if drawFromModel == False:
                    print('World Perf: Episode %f. Reward %f. action: %f. mean reward %f.' %
                          (real_episodes, reward_sum/real_bs, action, running_reward/real_bs))
                    if reward_sum/batch_size > 200:
                        break
                reward_sum = 0

                # Once the model has been trained on 100 episodes, we start alternating between training the policy
                # from the model and training the model from the real environment.
                if episode_number > 100:
                    drawFromModel = not drawFromModel
                    trainTheModel = not trainTheModel
                    trainThePolicy = not trainThePolicy

            if drawFromModel == True:
                observation = np.random.uniform(-0.1, 0.1, [4])  # Generate reasonable starting point
                batch_size = model_bs
            else:
                observation = env.reset()
                batch_size = real_bs

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

    def resetGradBuffer(gradBuffer):
        for ix, grad in enumerate(gradBuffer):
            gradBuffer[ix] = grad * 0
        return gradBuffer

    def discount_rewards(r):
        """ take 1D float array of rewards and compute discounted reward """
        discounted_r = np.zeros_like(r)
        running_add = 0
        for t in reversed(xrange(0, r.size)):
            running_add = running_add * gamma + r[t]
            discounted_r[t] = running_add
        return discounted_r

    # This function uses our model to produce a new state when given a previous state and action
    def stepModel(sess, xs, action):
        toFeed = np.reshape(np.hstack([xs[-1][0], np.array(action)]), [1, 5])
        myPredict = sess.run([predicted_state], feed_dict={previous_state: toFeed})
        reward = myPredict[0][:, 4]
        observation = myPredict[0][:, 0:4]
        observation[:, 0] = np.clip(observation[:, 0], -2.4, 2.4)
        observation[:, 2] = np.clip(observation[:, 2], -0.4, 0.4)
        doneP = np.clip(myPredict[0][:, 5], 0, 1)
        if doneP > 0.1 or len(xs) >= 300:
            done = True
        else:
            done = False
        return observation, reward, done


my_bot = Agent_Bot(ModelAgent)
my_civ_client = CivClient(my_bot, "chrisrocks", client_port=6000)
CivConnection(my_civ_client, 'http://localhost')
