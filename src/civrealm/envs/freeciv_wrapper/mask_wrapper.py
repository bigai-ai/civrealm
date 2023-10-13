import torch
import numpy as np
from gymnasium.core import Wrapper, ObservationWrapper, Env, spaces

# info, obeservation=env.step(action) -> mask(info, action) -> agent

class MaskWarpper():
    '''
    Note: masks are 0 for padding, 1 for non-padding
    other_players_mask: (n_max_other_players, 1)
    units_mask: (n_max_units, 1)
    cities_mask: (n_max_cities, 1)
    other_units_mask: (n_max_other_units, 1)
    other_cities_mask: (n_max_other_cities, 1)
    actor_type_mask: (actor_type_dim) # TODO Different generalization for this mask
    city_id_mask: (n_max_cities, 1)
    city_action_type_mask: (n_max_cities, city_action_type_dim)
    unit_id_mask: (n_max_units, 1)
    unit_action_type_mask: (n_max_units, unit_action_type_dim)
    gov_action_type_mask: (gov_action_type_dim)
    '''
    def __init__(
        self,
        n_max_other_players,
        n_max_units,
        n_max_cities,
        n_max_other_units,
        n_max_other_cities,
        actor_type_dim,
        city_action_type_dim,
        unit_action_type_dim,
        gov_action_type_dim,
    ):  
        self.n_max_cities = n_max_cities
        self.gov_action_type_dim = gov_action_type_dim

        self.other_players_mask = torch.zeros(n_max_other_players, 1)
        self.units_mask = torch.zeros(n_max_units, 1)
        self.cities_mask = torch.ones(n_max_cities, 1)
        self.other_units_mask = torch.ones(n_max_other_units, 1)
        self.other_cities_mask = torch.ones(n_max_other_cities, 1)
        self.actor_type_mask = torch.ones(actor_type_dim)
        self.city_id_mask = torch.ones(n_max_cities, 1)
        self.city_action_type_mask = torch.ones(n_max_cities, city_action_type_dim)
        self.unit_id_mask = torch.ones(n_max_units, 1)
        self.unit_action_type_mask = torch.ones(n_max_units, unit_action_type_dim)
        self.gov_action_type_mask = torch.ones(gov_action_type_dim)
        
        self.turn = torch.zeros(1)

    def update_mask(self, observation, info, action, done): 
        '''
        input: observation: (observation_dim)
        output: mask: (new_mask)
        '''
        # other_players_mask
        other_players_num = len(info['available_actions']['player'].keys())
        self.other_players_mask[:, :other_players_num - 1, :] = 1
        # units_mask
        units_num = len(info['available_actions']['unit'].keys())
        self.units_mask[:, :units_num - 1, :] = 1
        # cities_mask
        if 'city' in info['available_actions']:
            cities_num = len(info['available_actions']['city'].keys())
            self.cities_mask[:, :cities_num - 1, :] = 1
        
        # TODO: need to get from observation
        # other_units_mask
        other_units_num = len(observation['other_units'].keys())
        self.other_units_mask[:, :other_units_num - 1, :] = 1
        # other_cities_mask
        other_cities_num = len(observation['other_cities'].keys())
        self.other_cities_mask[:, :other_cities_num - 1, :] = 1

        # city_action_type_mask
        # TODO check if in the same turn
        if 'city' in info['available_actions']:
            for i in info['available_actions']['city']:  
                if action['ctrl_type'] == 'city' and action['city_id'] == i:
                    info['available_actions']['city'][i][action['action_type']] = False
                    mask = [int(value) for value in info['available_actions']['city'][i].items()]
                    self.city_action_type_mask[i, :] = torch.tensor(mask)
        # city_id_mask
        for i in self.city_action_type_mask:
            if any(self.city_action_type_mask[i]):
                self.city_id_mask[i] = 1

        # unit_action_type_mask
        for i in info['available_actions']['unit']:
            self.unit_id_mask[i] = torch.tensor([int(value) for value in info['available_actions']['unit'][i].values()])
        # unit_id_mask
        for i in self.unit_action_type_mask:
            if any(self.unit_action_type_mask[i]):
                self.unit_id_mask[i] = 1

        # gov_action_type_mask
        if action['ctrl_type'] == 'gov':
            info['available_actions']['gov'][0][action['action_type']] = False
        self.gov_action_type_mask = torch.tensor([int(value) for value in info['available_actions']['gov'][0].values()])
        
        # actor_type_mask: [unit, city, gov]
        if self.unit_id_mask.any():
            self.actor_type_mask[0] = 1
        if self.city_id_mask.any():
            self.actor_type_mask[1] = 1  
        if self.gov_action_type_mask.any():
            self.actor_type_mask[2] = 1
    
    def reset_mask(self):
        # new turn some mask need to be reset
        self.city_id_mask = torch.zeros(self.n_max_cities, 1)
        self.gov_action_type_mask = torch.zeros(self.gov_action_type_dim)


    def get_mask(self, observation, info, action, done):
        '''
        Return all masks
        '''
        if info['turn'] != self.turn:
            self.turn = info['turn']
            self.reset_mask()
        
        self.update_mask(observation, info, action, done)
        return self.other_players_mask, self.units_mask, self.cities_mask, self.other_units_mask, self.other_cities_mask, self.actor_type_mask, self.city_id_mask, self.city_action_type_mask, self.unit_id_mask, self.unit_action_type_mask, self.gov_action_type_mask
