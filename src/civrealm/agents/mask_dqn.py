import random
import numpy as np
import collections
from tqdm import tqdm
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent
from civrealm.configs import fc_args
import civrealm
import gymnasium
import warnings
# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings('ignore', message='.*The obs returned by the .* method.*')

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = collections.deque(maxlen=capacity) 

    def add(self, state, action, reward, next_state, done, mask):  
        self.buffer.append((state, action, reward, next_state, done, mask))

    def sample(self, batch_size):  
        transitions = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, done, mask = zip(*transitions)
        return np.array(state), action, reward, np.array(next_state), done, np.array(mask)

    def size(self):  
        return len(self.buffer)

class Qnet(torch.nn.Module):
    def __init__(self, state_dim, hidden_dim, action_dim):
        super(Qnet, self).__init__()
        self.fc1 = torch.nn.Linear(state_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, action_dim)

    def forward(self, x, action_mask):
        x = F.relu(self.fc1(x)) 
        q_values = self.fc2(x)
        masked_q_values = q_values + (action_mask * -1e9)  
        return masked_q_values


class DQN:
    def __init__(self, state_dim, hidden_dim, action_dim, learning_rate, gamma, epsilon, target_update, device):
        self.action_dim = action_dim
        self.q_net = Qnet(state_dim, hidden_dim, self.action_dim).to(device)  
        self.target_q_net = Qnet(state_dim, hidden_dim, self.action_dim).to(device)
        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=learning_rate)
        self.gamma = gamma  
        self.epsilon = epsilon 
        self.target_update = target_update  
        self.count = 0  
        self.device = device

    def take_action(self, state, action_mask):  
        if np.random.random() < self.epsilon:
            action_mask = np.atleast_1d(action_mask)
            valid_idxs = np.where(action_mask == 0)[0]
            idx = np.random.choice(valid_idxs)
            action = idx
        else:
            state = torch.tensor([state], dtype=torch.float).to(self.device)
            action_mask = torch.tensor([action_mask], dtype=torch.float).to(self.device)
            action = self.q_net(state, action_mask).argmax(dim=-1).item()
        return action

    def update(self, transition_dict):
        states = torch.tensor(transition_dict['states'].astype(np.int64),
                              dtype=torch.float).to(self.device)
        actions = torch.tensor(transition_dict['actions']).view(-1, 1).to(self.device)
        rewards = torch.tensor(transition_dict['rewards'],
                               dtype=torch.float).view(-1, 1).to(self.device)
        next_states = torch.tensor(transition_dict['next_states'].astype(np.int64),dtype=torch.float).to(self.device)
        dones = torch.tensor(transition_dict['dones'], dtype=torch.float).view(-1, 1).to(self.device)
        action_mask = torch.tensor(transition_dict['masks'], dtype=torch.float).to(self.device)

        q_values = self.q_net(states, action_mask).gather(1, actions)  
        max_next_q_values = self.target_q_net(next_states, action_mask).max(1)[0].view(-1, 1)
        q_targets = rewards + self.gamma * max_next_q_values * (1 - dones) 
        masked_q_targets = q_targets + (action_mask * -1e9)  
        dqn_loss = torch.mean(F.mse_loss(q_values, masked_q_targets))  
        self.optimizer.zero_grad()  
        dqn_loss.backward()  
        self.optimizer.step()

        if self.count % self.target_update == 0:
            self.target_q_net.load_state_dict(
                self.q_net.state_dict())  
        self.count += 1

class DQNAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        if "debug.agentseed" in fc_args:
            self.set_agent_seed(fc_args["debug.agentseed"])
        self.unit_agent = DQN(state_dim, hidden_dim, action_dim, lr, gamma, epsilon, target_update, device)
        self.unit_buffer = ReplayBuffer(buffer_size)
        self.action_choose = 1  # record action choose output by policy for replaybuffer
        self.action_ctrl = 'unit' # record which kind of type 
        max_action_dim = 40
        self.action_mask =  np.random.randint(0, 2, max_action_dim)
        self.unit_action_dict = {'disband': 'disband', 'transform': 'transform', 'mine': 'mine', 'cultivate': 'cultivate', 
        'plant': 'plant', 'fortress': 'fortress', 'airbase': 'airbase', 'irrigation': 'irrigation', 
        'fallout': 'fallout', 'pollution': 'pollution', 'autosettlers': 'autosettlers', 'explore': 'explore', 
        'paradrop': 'paradrop', 
        'build_city': 'build_city', 'fortify': 'fortify', 'build_road': 'build_road', 'build_railroad': 'build_railroad', 
        'pillage': 'pillage', 'homecity': 'homecity', 'airlift': 'airlift', 'upgrade': 'upgrade', 'unit_load': 'unit_load', 
        'unit_unload': 'unit_unload', 'no_orders': 'no_orders', 'goto_0': 'goto_0', 'goto_1': 'goto_1', 'goto_2': 'goto_2', 
        'goto_3': 'goto_3', 'goto_4': 'goto_4', 'goto_5': 'goto_5', 'goto_6': 'goto_6', 'goto_7': 'goto_7', 
        'attack_0': 'attack_0', 'attack_1': 'attack_1', 'attack_2': 'attack_2', 'attack_3': 'attack_3', 
        'attack_4': 'attack_4','attack_5': 'attack_5', 'attack_6': 'attack_6', 'attack_7': 'attack_7'}
    
    def make_mask(self, valid_action_dict):
        action_mask = [0 if action in valid_action_dict else 1 for action in self.unit_action_dict]
        return action_mask

    # Each act() lets one actor perform an action.
    def act(self, observations, obs, info):
        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():
            # ctrl_type: 'unit', 'city', 'tile', 'player'
            self.action_ctrl = ctrl_type
            valid_actor_id, valid_action_dict = self.get_next_valid_actor(observations, info, ctrl_type)
            if not valid_actor_id:
                continue
            if self.action_ctrl == 'unit':
                self.action_mask = self.make_mask(valid_action_dict)
                action_name = self.unit_agent.take_action(obs, self.action_mask)
                self.action_choose = action_name #save policy output to replybuffer

                print('action_name: ', list(self.unit_action_dict.values())[action_name])
                return valid_action_dict[list(self.unit_action_dict.values())[action_name]]
            else:
                calculate_func = getattr(self, f'calculate_{ctrl_type}_actions')
                action_name = calculate_func(valid_action_dict)             
                if action_name:
                    return valid_action_dict[action_name]
        return None

    def sample_action_by_prob(self, action_probabilities):
        action_list = list(action_probabilities.keys())
        action_probabilities = list(action_probabilities.values())
        try:
            action_name = random.choices(action_list, weights=action_probabilities, k=1)[0]
            fc_logger.info(f'Action sampled: {action_name}')
            return action_name
        except ValueError:
            # This happens when all action_probabilities are 0.0.
            return None

    def sample_desired_actions(self, action_dict, desired_actions):
        # Use desired_actions = {'': 0.0} for random sample
        action_probabilities = {}
        for action_key in action_dict:
            action_probabilities[action_key] = 0.0
            for desired_action_key in desired_actions:
                if desired_action_key in action_key:
                    action_probabilities[action_key] = desired_actions[desired_action_key]
                    break
        return self.sample_action_by_prob(action_probabilities)

    def calculate_unit_actions(self, action_dict):
        desired_actions = {'explore': 0.0,
                           'goto': 0.0,
                           'road': 0.0,
                           'irrigation': 0.0,
                           'mine': 0.0,
                           'cultivate': 0.0,
                           'plant': 0.0,
                           'pillage': 0.0,
                           'fortress': 0.0,
                           'railroad': 0.0,
                           'airbase': 0.0,
                           'build': 0.0,}
        
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_city_actions(self, action_dict):
        desired_actions = {'city_work': random.random() * 0.2,
                           'city_unwork': random.random() * 0.2,
                           'change_improve_prod': random.random() * 0.2,
                           'change_unit_prod': random.random() * 0.2,
                           'city_buy_production': random.random() * 0.2,
                           'city_sell_improvement': random.random() * 0.2,
                           'city_change_specialist': random.random() * 0.2, }
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_player_actions(self, action_dict):
        desired_actions = {}
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_dipl_actions(self, action_dict):
        desired_actions = {'start_negotiation': random.random(),
                           'accept_treaty': random.random(),
                           'cancel_treaty': random.random(),
                           'cancel_vision': random.random(),
                           'stop_negotiation': random.random(),
                           'remove_clause': random.random(),
                           'add_clause': random.random(),
                           'trade_tech_clause': random.random(),
                           'trade_gold_clause': random.random(),
                           'trade_city_clause': random.random(), }
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_tech_actions(self, action_dict):
        desired_actions = {'research_tech': random.random(),
                           'set_tech_goal': random.random(), }
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_gov_actions(self, action_dict):
        desired_actions = {'change_gov': random.random(),
                           'increase_sci': random.random(),
                           'decrease_sci': random.random(),
                           'increase_lux': random.random(),
                           'decrease_lux': random.random(),
                           'increase_tax': random.random(),
                           'decrease_tax': random.random(), }
        return self.sample_desired_actions(action_dict, desired_actions)
   
# class DQNAgent:
if __name__ == "__main__":
    lr = 2e-3
    num_episodes = 10
    hidden_dim = 1024
    gamma = 0.98
    epsilon = 0.01
    target_update = 10
    buffer_size = 10000
    minimal_size = 50
    batch_size = 16
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


    env = gymnasium.make('freeciv/FreecivBase-v0')
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    replay_buffer = ReplayBuffer(buffer_size)
    state_dim = 4056 # 78*52
    action_dim =  40
    agent = DQN(state_dim, hidden_dim, action_dim, lr, gamma, epsilon, target_update, device)
    agent = DQNAgent()


    def select_obs(observation):
        # choose map-terain in observation as obs, flat the input observation map into tensor
        obs = observation['map']['terrain'].reshape(-1)
        return obs

'''
for i_episode in range(num_episodes):
    observations, info = env.reset()
    obs = select_obs(observations)
    done = False
    episode_reward = 0
    while not done:
        action = agent.act(observations, obs, info)
        next_observations, reward, terminated, truncated, info = env.step(action)
        next_obs = select_obs(next_observations)
        done = terminated or truncated
        if agent.action_ctrl == 'unit':
            agent.unit_buffer.add(obs, agent.action_choose, reward, next_obs, done, agent.action_mask)
        observations = next_observations
        obs = next_obs
        episode_reward += reward
        # when the buffer size is large enough, start to update the network
        if agent.unit_buffer.size() > minimal_size:
            b_s, b_a, b_r, b_ns, b_d, b_mask = agent.unit_buffer.sample(batch_size)
            transition_dict = {
                'states': b_s,
                'actions': b_a,
                'next_states': b_ns,
                'rewards': b_r,
                'dones': b_d,
                'masks': b_mask
            }
            agent.unit_agent.update(transition_dict)
            print('success update')
    print('episode_reward',episode_reward)
'''