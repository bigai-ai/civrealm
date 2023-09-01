# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


from typing import Dict
from BitVector import BitVector

from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
from freeciv_gym.freeciv.map.map_ctrl import MapCtrl

from freeciv_gym.freeciv.utils.fc_types import O_LUXURY, O_SCIENCE, O_GOLD, O_TRADE, O_SHIELD,\
    O_FOOD, FC_INFINITY, VUT_UTYPE, VUT_IMPROVEMENT

from math import floor
from freeciv_gym.freeciv.utils.base_state import ListState

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger

FEELING_BASE = 0  # /* before any of the modifiers below */
FEELING_LUXURY = 1  # /* after luxury */
FEELING_EFFECT = 2  # /* after building effects */
FEELING_NATIONALITY = 3  # /* after citizen nationality effects */
FEELING_MARTIAL = 4  # /* after units enforce martial order */
FEELING_FINAL = 5  # /* after wonders (final result) */

citizen_types = ['angry', 'unhappy', 'content', 'happy']


class CityState(ListState):
    def __init__(self, city_dict: Dict[int, Dict], ruleset: RulesetCtrl, map_ctrl: MapCtrl):
        super().__init__()
        self.city_dict = city_dict
        self.rule_ctrl = ruleset
        self.map_ctrl = map_ctrl

    def _update_state(self, pplayer):
        self._state = {}
        for city_id in self.city_dict:
            pcity = self.city_dict[city_id]
            self._state[city_id] = self._get_city_state(pcity, pcity['owner'] == pplayer['playerno'])

    def _get_city_state(self, pcity, city_owned):
        city_state = {}

        city_state['id'] = pcity['id']
        city_state['owner'] = pcity['owner']
        city_state['size'] = pcity['size']

        tile = self.map_ctrl.index_to_tile(pcity['tile'])
        city_state['x'] = tile['x']
        city_state['y'] = tile['y']

        if city_owned:
            city_state.update(self._get_own_city_state(pcity))
        else:
            for property in [
                'food_stock', 'granary_size', 'granary_turns', 'production_kind', 'production_value', 'luxury',
                'science', 'prod_food', 'surplus_food', 'prod_gold', 'surplus_gold', 'prod_shield', 'surplus_shield',
                'prod_trade', 'surplus_trade', 'bulbs', 'city_waste', 'city_corruption', 'city_pollution', 'state',
                'growth_in', 'turns_to_prod_complete', 'prod_process', 'ppl_angry', 'ppl_unhappy', 'ppl_content',
                    'ppl_happy']:
                city_state[property] = -1
            city_state['can_build_unit'] = BitVector(intVal=0, size=self.rule_ctrl.ruleset_control['num_unit_types'])
            city_state['improvements'] = BitVector(intVal=0, size=self.rule_ctrl.ruleset_control['num_impr_types'])

        return city_state

    def _get_own_city_state(self, pcity):
        city_state = {}
        for cp in ['food_stock', 'granary_size', 'granary_turns', 'production_kind', 'production_value']:
            city_state[cp] = pcity[cp]

        city_state['luxury'] = pcity['prod'][O_LUXURY]
        city_state['science'] = pcity['prod'][O_SCIENCE]

        for str_item, o_item in [('food', O_FOOD), ('gold', O_GOLD), ('shield', O_SHIELD), ('trade', O_TRADE)]:
            city_state['prod_'+str_item] = pcity['prod'][o_item]
            city_state['surplus_'+str_item] = pcity['surplus'][o_item]

        city_state['bulbs'] = pcity['prod'][O_SHIELD]
        city_state['city_waste'] = pcity['waste'][O_SHIELD]
        city_state['city_corruption'] = pcity['waste'][O_TRADE]
        city_state['city_pollution'] = pcity['pollution']
        city_state['state'] = CityState.get_city_state(pcity)
        if 'granary_turns' in pcity:
            city_state['growth_in'] = CityState.city_turns_to_growth_text(pcity)
        else:
            city_state['growth_in'] = -1
        city_state['turns_to_prod_complete'] = self.get_city_production_time(pcity)
        city_state['prod_process'] = self.get_production_progress(pcity)

        for citizen in citizen_types:
            cur_citizen = 'ppl_' + citizen
            city_state[cur_citizen] = 0
            if pcity[cur_citizen] != None:
                city_state[cur_citizen] = pcity['ppl_' + citizen][FEELING_FINAL]

        city_state['can_build_unit'] = pcity['can_build_unit']
        city_state['improvements'] = pcity['improvements']
        return city_state

    @staticmethod
    def get_named_city_improvements(self, pcity):
        city_state: Dict[str, bool] = {}
        for improvement_i in range(self.rule_ctrl.ruleset_control['num_impr_types']):
            tech_tag = 'impr_int_%s_%i' % (self.rule_ctrl.improvements[improvement_i]['name'], improvement_i)
            city_state[tech_tag] = False
            if 'improvements' in pcity and pcity['improvements'][improvement_i] == 1:
                city_state[tech_tag] = True
        return city_state

    @staticmethod
    def get_city_tile_outputs(pcity):
        city_state = {}
        # The following information will be available in the maps, hence we currently omit them in the individual city states
        for tile_num, (output_food, output_shield, output_trade) in enumerate(
            zip(pcity['output_food'],
                pcity['output_shield'],
                pcity['output_trade'])):
            city_state['pos_output_food_%i' % tile_num] = output_food
            city_state['pos_output_shield_%i' % tile_num] = output_shield
            city_state['pos_output_trade_%i' % tile_num] = output_trade
        return city_state

    @staticmethod
    def is_city_center(city, tile):
        return (city['tile'] == tile['index'])

    @staticmethod
    def is_free_worked(city, tile):
        return (city['tile'] == tile['index'])

    @staticmethod
    def city_owner_player_id(pcity):
        if pcity is None:
            return None
        return pcity['owner']

    def does_city_have_improvement(self, pcity, improvement_name):
        if pcity is None or 'improvements' not in pcity:
            return False

        for z in range(self.rule_ctrl.ruleset_control['num_impr_types']):
            if (pcity['improvements'] is not None
                    and pcity['improvements'][z] == 1
                    and self.rule_ctrl.improvements[z] is not None
                    and self.rule_ctrl.improvements[z]['name'] == improvement_name):
                return True
        return False

    @staticmethod
    def city_turns_to_build(pcity, target, include_shield_stock):
        """
         Calculates the turns which are needed to build the requested
         improvement in the city.  GUI Independent.
        """

        city_shield_surplus = pcity['surplus'][O_SHIELD]
        city_shield_stock = pcity['shield_stock'] if include_shield_stock else 0
        cost = RulesetCtrl.universal_build_shield_cost(target)

        if include_shield_stock and (pcity['shield_stock'] >= cost):
            return 1
        elif (pcity['surplus'][O_SHIELD] > 0):
            return floor((cost - city_shield_stock - 1) / city_shield_surplus + 1)
        else:
            return FC_INFINITY

    def get_city_production_time(self, pcity):
        """Returns the number of turns to complete current city production."""

        if pcity is None:
            return FC_INFINITY

        if pcity['production_kind'] == VUT_UTYPE:
            punit_type = self.rule_ctrl.unit_types[pcity['production_value']]
            return self.city_turns_to_build(pcity, punit_type, True)

        if pcity['production_kind'] == VUT_IMPROVEMENT:
            improvement = self.rule_ctrl.improvements[pcity['production_value']]
            if improvement['name'] == 'Coinage':
                return FC_INFINITY
            return self.city_turns_to_build(pcity, improvement, True)

        return FC_INFINITY

    @staticmethod
    def city_turns_to_growth_text(pcity):
        """Create text describing city growth."""
        turns = pcity['granary_turns']

        if turns == 0:
            return 'blocked'
        elif turns > 1000000:
            return 'never'
        elif turns < 0:
            return 'Starving in ' + str(turns) + ' turns'
        else:
            return str(turns) + ' turns'

    @staticmethod
    def city_population(pcity):
        """Returns how many thousand citizen live in this city."""
        # /*  Sum_{i=1}^{n} i  ==  n*(n+1)/2  */
        return pcity['size'] * (pcity['size'] + 1) * 5

    @staticmethod
    def get_city_state(pcity):
        """Returns the city state: Celebrating, Disorder or Peace."""
        if pcity is None:
            return -1
        if pcity['was_happy'] and pcity['size'] >= 3:
            return 3  # 'Celebrating'
        elif 'unhappy' in pcity and pcity['unhappy']:
            return 1  # 'Disorder'
        else:
            return 2  # 'Peace'

    @staticmethod
    def is_wonder(improvement):
        return improvement['soundtag'][0] == 'w'

    def get_production_progress(self, pcity):
        """ Returns city production progress, eg. the string "5 / 30"""

        if pcity is None:
            return FC_INFINITY

        if pcity['production_kind'] == VUT_UTYPE:
            punit_type = self.rule_ctrl.unit_types[pcity['production_value']]
            return pcity['shield_stock'] / RulesetCtrl.universal_build_shield_cost(punit_type)

        if pcity['production_kind'] == VUT_IMPROVEMENT:
            improvement = self.rule_ctrl.improvements[pcity['production_value']]
            if improvement['name'] == 'Coinage':
                return FC_INFINITY
            return pcity['shield_stock'] / RulesetCtrl.universal_build_shield_cost(improvement)

        return FC_INFINITY
