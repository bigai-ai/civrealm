# Copyright (C) 2023  The CivRealm project
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

import os
import csv
import h5py
import yaml
import json
from datetime import datetime
from typing import final
from civrealm.configs import fc_args
import numpy as np

def parse_dataset_settings(config_file='../../../../dataset_setting.yaml'):
    with open(f'{CURRENT_DIR}/{config_file}', 'r') as file:
        dataset_settings = yaml.safe_load(file)
    return dataset_settings

def read_h5py_file(file_path:str):
    file = h5py.File(file_path, "r")
    return file

def read_raw_data(file:h5py.File, index:int):
    return [raw[:] if len(i.shape) > 0 else raw[()] 
            for i in file[str(index)].values()]

def search(data, fields):
    if isinstance(fields, str):
        fields = fields.split(".")
    if len(fields) == 0 or fields[0] not in data:
        return 
    if len(fields) == 1 and fields[0] in data:
        return data[fields[0]]
    return search(data[fields[0]], fields[1:])

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_SETTING = parse_dataset_settings()

class BaseWriter(object):

    def __init__(self, dataset:str, 
                 data_dir:str=DATASET_SETTING["data_dir"], 
                 input_register_info:list[dict[str, str]]=None):
        self.dataset = dataset
        self.data_dir = data_dir
        self.file_handlers = dict()
        self.writers = dict()
        self.req_fields = dict()
        self.init_dir()
        self.init_writer(self.create_register_info(input_register_info))

    def init_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        return
    
    def create_register_info(self, register_info):
        if register_info is None:
            register_info = list()
            if isinstance(self.dataset, list):
                for dataset in self.dataset:
                    register_info.append([{
                        "key": self.dataset, 
                        "req_fields": DATASET_SETTING[self.dataset]
                    }])
            else:
                register_info = [{
                    "key": self.dataset, 
                    "req_fields": DATASET_SETTING[self.dataset]
                }]
        return register_info

    def init_writer(self, register_info):
        for info in register_info:
            if "key" not in info:
                raise Exception("Please make sure the register_info containing `key`!")
            key = info["key"] + "_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            self.req_fields[key] = self.handle_req_fields(key, info.get("req_fields"))
            self.register_file_handler(key)
            self.register_writer(key)
        return

    def handle_req_fields(self, key, req_fields):
        if req_fields is None:
            req_fields = key
        if isinstance(req_fields, str):
            req_fields = [req_fields]
        return req_fields

    def insert(self, input_data:list[dict[str, any]], key:str=None):            
        for writer_key in self.writers:
            if key is not None:
                self.insert_tick_data(writer_key, input_data, key)
                continue
            tick_data = list()
            for field in self.req_fields[writer_key]:
                is_found = 0
                for data in input_data:
                    if (_data := search(data, field)) is not None:
                        tick_data.append(_data)
                        is_found = 1
                        break
                assert is_found == 1, f"Please make sure the input_data containing field {field}"
            self.insert_tick_data(writer_key, tick_data)
        return

    def register_file_handler(self, key):
        raise NotImplementedError

    def register_writer(self):
        raise NotImplementedError

    def insert_tick_data(self, writer_key:str, tick_raw_data:list[any], key:str=None):
        raise NotImplementedError

    @final
    def close(self):
        for file_handler in self.file_handlers:
            self.file_handlers[file_handler].close()
        return

class H5pyWriter(BaseWriter):

    def register_file_handler(self, key:str):
        self.file_handlers[key] = h5py.File(self.data_dir+f"/{key}.h5", "w")
        return

    def register_writer(self, key:str):
        self.writers[key] = 0
        return

    def insert_tick_data(self, writer_key:str, tick_raw_data:list[any], key:str=None):
        if key is not None:
            self.file_handlers[writer_key].create_dataset(key, data=json.dumps(tick_raw_data))
            return
        grp = self.file_handlers[writer_key].create_group(str(self.writers[writer_key]))
        for i, field in enumerate(self.req_fields[writer_key]):
            grp.create_dataset(field, data=tick_raw_data[i])
        self.writers[writer_key] += 1
        return
