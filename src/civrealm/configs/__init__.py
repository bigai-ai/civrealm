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
import re
import os
import argparse
import yaml

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def boolean_string(s):
    s = s.lower()
    if s not in {'false', 'true'}:
        raise ValueError(f'{s} is not a valid boolean string')
    return s == 'true'


def parse_args():
    """
    Initialize default arguments with yaml and renew values with input arguments.
    """

    default_config_file = os.path.normpath(
        os.path.join(CURRENT_DIR,
                     '../../../default_settings.yaml'))
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', help="configuration file *.yml", type=str,
                        required=False, default=default_config_file)
    args, remaining_argv = parser.parse_known_args()

    opt = yaml.load(open(args.config_file), Loader=yaml.FullLoader)
    for key in opt.keys():
        # print(opt[key])
        if type(opt[key]) is dict:
            group = parser.add_argument_group(key)
            # print(key)
            for sub_key in opt[key].keys():
                assert type(opt[key][sub_key]) is not dict, "Config only accepts two-level of arguments"
                if type(opt[key][sub_key]) is bool:
                    group.add_argument('--' + key + '.' + sub_key, default=opt[key][sub_key], type=boolean_string)
                else:
                    group.add_argument(
                        '--' + key + '.' + sub_key, default=opt[key][sub_key],
                        type=type(opt[key][sub_key]))
        else:
            if type(opt[key]) is bool:
                parser.add_argument('--' + key, default=opt[key], type=boolean_string)
            else:
                parser.add_argument('--' + key, default=opt[key], type=type(opt[key]))
    args, remaining_argv = parser.parse_known_args(remaining_argv)

    return vars(args)

def parse_fc_web_args(config_file='../../../docker-compose.yml'):

    with open(f'{CURRENT_DIR}/{config_file}', 'r') as file:
        fc_web_args = yaml.safe_load(file)

    image = fc_web_args['services']['freeciv-web']['image']
    fc_web_args['tag'] = 'latest'

    if tag := re.search(r'\:(.*)', image):
        fc_web_args['tag'] = tag[1]

    return fc_web_args

fc_args = parse_args()
fc_web_args = parse_fc_web_args()
