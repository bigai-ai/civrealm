import argparse
import yaml
# import configparser

def parse_args():
    """
    Initialize default arguments with yaml and renew values with input arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', help="configuration file *.yml", type=str, required=False, default='src/gym_freeciv_web/configs/default_setting.yml')
    args, remaining_argv = parser.parse_known_args()

    opt = yaml.load(open(args.config_file), Loader=yaml.FullLoader)
    for key in opt.keys():
        # print(opt[key])
        if type(opt[key]) is dict:
            group = parser.add_argument_group(key)
            # print(key)
            for sub_key in opt[key].keys():
                group.add_argument('--' + key + '.' + sub_key, default=opt[key][sub_key])
        else:
            parser.add_argument('--' + key, default=opt[key])
    args = parser.parse_args(remaining_argv)
    opt.update(vars(args))
    
    return opt
    
args = parse_args()
