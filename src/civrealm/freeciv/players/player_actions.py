# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from civrealm.freeciv.utils import base_action
from civrealm.freeciv.utils.base_action import ActionList
from civrealm.freeciv.utils.fc_types import packet_player_rates
import civrealm.freeciv.players.player_helpers as player_helpers


class PlayerOptions(ActionList):
    def __init__(self, ws_client, rule_ctrl, city_ctrl, players):
        super().__init__(ws_client)

        self.rule_ctrl = rule_ctrl
        self.city_ctrl = city_ctrl
        self.players = players

    def _can_actor_act(self, actor_id):
        return True

    def update(self, pplayer):
        player_id = pplayer['playerno']
        if pplayer['is_alive'] and not self.actor_exists(player_id):
            self.add_actor(player_id)
            self.update_player_options(player_id, pplayer)

    def update_player_options(self, counter_id, cur_player):

        # these actions change lux sci tax with a step = 10 as in Freeciv-web.
        # Instead, we implement SetSciLuxTax to adjust lux sci tax more flexibly.
        # Moved to government
        """
        self.add_action(counter_id, IncreaseLux(cur_player))
        self.add_action(counter_id, DecreaseLux(cur_player))
        self.add_action(counter_id, IncreaseSci(cur_player))
        self.add_action(counter_id, DecreaseSci(cur_player))
        self.add_action(counter_id, IncreaseTax(cur_player))
        self.add_action(counter_id, DecreaseTax(cur_player))
        """


class IncreaseSci(base_action.Action):
    action_key = "increase_sci"

    def __init__(self, cur_player):
        super().__init__()
        self.cur_player = cur_player
        self.playerno = cur_player['playerno']

    def is_action_valid(self):
        return self.cur_player["science"] + 10 <= player_helpers.government_max_rate(self.cur_player['government'])

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.sci += 10
        if self.lux > 0:
            self.lux -= 10
        else:
            self.tax -= 10

    def _action_packet(self):
        self._change_rate()
        packet = {"pid": packet_player_rates,
                  "tax": self.tax,
                  "luxury": self.lux,
                  "science": self.sci}
        self.wait_for_pid = (51, self.playerno)
        return packet


class DecreaseSci(IncreaseSci):
    action_key = "decrease_sci"

    def is_action_valid(self):
        return 0 <= self.cur_player["science"] - 10

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.sci -= 10
        if self.lux < player_helpers.government_max_rate(self.cur_player['government']):
            self.lux += 10
        else:
            self.tax += 10


class IncreaseLux(IncreaseSci):
    action_key = "increase_lux"

    def is_action_valid(self):
        return self.cur_player["luxury"] + 10 <= player_helpers.government_max_rate(self.cur_player['government'])

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.lux += 10
        if self.tax > 0:
            self.tax -= 10
        else:
            self.sci -= 10


class DecreaseLux(IncreaseSci):
    action_key = "decrease_lux"

    def is_action_valid(self):
        return 0 <= self.cur_player["luxury"] - 10

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.lux -= 10
        if self.tax < player_helpers.government_max_rate(self.cur_player['government']):
            self.tax += 10
        else:
            self.sci += 10


class IncreaseTax(IncreaseSci):
    action_key = "increase_tax"

    def is_action_valid(self):
        return self.cur_player["tax"] + 10 <= player_helpers.government_max_rate(self.cur_player['government'])

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.tax += 10
        if self.lux > 0:
            self.lux -= 10
        else:
            self.sci -= 10


class DecreaseTax(IncreaseSci):
    action_key = "decrease_tax"

    def is_action_valid(self):
        return 0 <= self.cur_player["tax"] - 10

    def _change_rate(self):
        self.sci = self.cur_player["science"]
        self.tax = self.cur_player["tax"]
        self.lux = self.cur_player["luxury"]

        self.tax -= 10
        if self.lux < player_helpers.government_max_rate(self.cur_player['government']):
            self.lux += 10
        else:
            self.sci += 10
