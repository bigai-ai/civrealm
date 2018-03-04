'''
Created on 03.03.2018

@author: christian
'''

import urllib
from utils.base_action import Action
from utils.fc_types import packet_city_make_specialist,\
    packet_city_change_specialist, packet_city_make_worker, packet_city_buy,\
    packet_city_sell, packet_city_change, packet_city_worklist, VUT_UTYPE,\
    VUT_IMPROVEMENT, packet_city_rename

MAX_LEN_WORKLIST = 64


class CityWorkTile(Action):
    action_key =  "city_work"
    def __init__(self, ws_client, pcity, dx, dy, city_map):
        Action.__init__(self, ws_client)
        self.pcity = pcity
        self.city_map = city_map
        self.city_map.update_map(pcity["city_radius_sq"])
        
        self.ctile = city_map.map_ctrl.city_tile(pcity)
        self.ptile = city_map.map_ctrl.map_pos_to_tile(self.ctile["x"] + dx, self.ctile["y"] + dy)
        
        self.output_idx = self.city_map.get_city_dxy_to_index(dx, dy, self.ctile)
        self.action_key += "_%i_%i" % (dx, dy)
    
    def is_action_valid(self):
        return "worked" in self.ptile and "food_output" in self.pcity and \
            self.ptile["worked"] == 0 and self.pcity["specialists_size"] > 0 and self.output_idx != -1 
    
    def get_output_at_tile(self):
        if "food_output" in self.pcity:
            idx = self.output_idx
            food_output = self.pcity['food_output'][idx]
            shield_output = self.pcity['shield_output'][idx]
            trade_output = self.pcity['trade_output'][idx]
            return food_output, shield_output, trade_output
    
    def _action_packet(self):
        packet = {"pid" : packet_city_make_worker,
                  "city_id" : self.pcity['id'],
                  "worker_x" : self.ptile['x'],
                  "worker_y" : self.ptile['y']}
        return packet
        
class CityUnworkTile(CityWorkTile):
    action_key =  "city_unwork"
    def is_action_valid(self):
        return "worked" in self.ptile and "food_output" in self.pcity and \
               self.ptile["worked"] == self.pcity["id"] and self.output_idx != -1
    
    def _action_packet(self):
        packet = {"pid" : packet_city_make_specialist,
                  "city_id" : self.pcity['id'],
                  "worker_x" : self.ptile['x'],
                  "worker_y" : self.ptile['y']}
        return packet

class CityChangeSpecialist(Action):
    action_key =  "city_change_specialist"
    def __init__(self, ws_client, pcity, specialist_num):
        Action.__init__(self, ws_client)
        self.specialist_num = specialist_num
        self.pcity = pcity
        self.action_key += "_%i" % specialist_num
        
    def is_action_valid(self):
        return self.pcity["specialists_size"] < self.specialist_num
        
    def _action_packet(self):
        from_specialist_id = self.pcity["specialists"][self.specialist_num][id]
        packet = {"pid": packet_city_change_specialist,
                  "city_id" : self.pcity["id"],
                  "from" : from_specialist_id,
                  "to" : (from_specialist_id + 1) % 3}
        return packet

class CityBuyProduction(Action):
    action_key = "city_buy_production"
    def __init__(self, ws_client, pcity, pplayer):
        Action.__init__(self, ws_client)
        self.pcity = pcity
        self.pplayer = pplayer

    def is_action_valid(self):
        return self.pplayer['gold'] >= self.pcity['buy_gold_cost']
    
    def _action_packet(self):
        """Buy whatever is being built in the city."""
        packet = {"pid" : packet_city_buy, "city_id" : self.pcity['id']}
        return packet

class CitySellImprovement(Action):
    """Sell city improvement"""
    action_key = "city_sell_improvement"
    def __init__(self, ws_client, pcity, improvement_id):
        Action.__init__(self, ws_client)
        self.pcity = pcity
        self.improvement_id = improvement_id
        self.action_key += "_%i" % improvement_id
    
    def is_action_valid(self):
        return 
    
    def _action_packet(self):
        packet = {"pid" : packet_city_sell, "city_id" : self.pcity['id'],
                  "build_id": self.improvement_id}
        return packet

class CityChangeProduction(Action):
    """Change city production."""
    action_key = "change_production"
    def __init__(self, ws_client, pcity, prod_kind, prod_value):
        Action.__init__(self, ws_client)
        self.pcity = pcity
        self.prod_kind = prod_kind
        self.prod_value = prod_value
        self.action_key += "_%s_%i" % (prod_kind, prod_value)

    def is_action_valid(self):
        if not self.worklist_not_empty(self.pcity):
            return False
        cur_item = self.pcity["worklist"][0]
        if not self.workitem_is_valid(cur_item):
            return False
        if cur_item["kind"] == self.prod_kind and cur_item["value"] == self.prod_value:
            return False
        return self._is_prod_valid()
        
    def _is_prod_valid(self):
        raise Exception("To be overwritten")
    
    @staticmethod
    def worklist_not_empty(pcity):
        return pcity['worklist'] != None and len(pcity['worklist']) != 0

    @staticmethod
    def workitem_is_valid(workitem):
        return not (workitem["kind"] is None or workitem["value"] is None or len(workitem) == 0)

    def get_worklist(self, pcity):
        """Populates data to the production tab in the city dialog."""
            
    def _action_packet(self):
        packet = {"pid" : packet_city_change, "city_id" : self.pcity["id"],
                  "production_kind": self.prod_kind, "production_value" : self.prod_value}
        return packet

class CityChangeUnitProduction(CityChangeProduction):
    action_key = "change_unit_prod"
    def __init__(self, ws_client, pcity, punit_type):
        CityChangeProduction.__init__(self, ws_client, pcity, VUT_UTYPE, punit_type["id"])
        self.punit_type = punit_type
        
    def is_action_valid(self):
        if self.punit_type['name'] == "Barbarian Leader" or self.punit_type['name'] == "Leader":
            return False
        
        return self.can_city_build_unit_now(self.pcity, self.punit_type["id"])
    
    @staticmethod
    def can_city_build_unit_now(pcity, punittype_id):
        """
          Return whether given city can build given building returns FALSE if
          the building is obsolete.
        """
        
        return (pcity != None and pcity['can_build_unit'] != None and
                pcity['can_build_unit'][punittype_id] == "1")
    
    def get_impact_of_action(self):
        return dict([(key, self.punit_type[key]) for key in ["name", "helptext", "rule_name", 
                                                             "build_cost", "attack_strength",
                                                             "defense_strength", "firepower"]])


class CityChangeImprovementProduction(CityChangeProduction):
    action_key = "change_improve_prod"
    def __init__(self, ws_client, pcity, pimprovement):
        CityChangeProduction.__init__(self, ws_client, pcity, VUT_IMPROVEMENT, pimprovement["id"])
        self.pimprovement = pimprovement
        
    def is_action_valid(self):
        return self.can_city_build_improvement_now(self.pcity, self.prod_value)
    
    def get_impact_of_action(self):
        build_cost = self.pimprovement['build_cost']
        if self.pimprovement['name'] == "Coinage":
            build_cost = "-"
            
        infos = dict([(key, self.pimprovement[key]) for key in ["name", "helptext", "rule_name"]])
        infos["build_cost"] = build_cost
        return infos

    @staticmethod
    def can_city_build_improvement_now(pcity, pimprove_id):
        """
        Return whether given city can build given building; returns FALSE if
        the building is obsolete.
        """
        return  pcity != None and pcity['can_build_improvement'] != None and \
              pcity['can_build_improvement'][pimprove_id] == "1"

class CityRename(Action):
    """Rename a city - ignored for bot"""
    def __init__(self, ws_client, pcity, suggested_name):
        Action.__init__(self, ws_client)
        self.pcity = pcity
        self.suggested_name = suggested_name

    def is_action_valid(self):
        return True

    def _action_packet(self):
        packet = {"pid" : packet_city_rename,
                  "name" : urllib.quote(unicode(self.suggested_name).encode('utf-8')),
                  "city_id" : self.pcity['id'] }
        return packet

class CityDoWorklist(Action):
    """Set worklist for city - Irrelevant for bot - can automatically assess production each turn"""
    def send_city_worklist(self, city_id):
        """Notifies the server about a change in the city worklist."""
        
        worklist = self.cities[city_id]['worklist']
        overflow = worklist.length - MAX_LEN_WORKLIST
        if overflow > 0:
            worklist = worklist[:MAX_LEN_WORKLIST-1]

        packet = {"pid"     : packet_city_worklist,
                 "city_id" : city_id,
                 "worklist": worklist}
        self.ws_client.send_request(packet)
    
    def send_city_worklist_add(self, city_id, kind, value):
        pcity = self.cities[city_id]
        if len(pcity['worklist']) >= MAX_LEN_WORKLIST:
            return

        pcity['worklist'].append({"kind" : kind, "value" : value})
        self.send_city_worklist(city_id)
    
    @staticmethod
    def find_universal_in_worklist(universal, worklist):
        for i, work_item in enumerate(worklist):
            if (work_item.kind == universal.kind and
                work_item.value == universal.value):
                return i
        return -1
