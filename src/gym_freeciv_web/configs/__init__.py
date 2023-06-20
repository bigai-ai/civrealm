import argparse
import yaml
# import configparser

def parse_args():
    """
    Initialize default arguments with yaml and renew values with input arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', help="configuration file *.yml", type=str, required=False, default='src/gym_freeciv_web/configs/random_test.yml')
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
    
opt = parse_args()

# conf_parser = argparse.ArgumentParser(
#         description=__doc__, # printed with -h/--help
#         # Don't mess with format of description
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         # Turn off help, so we print all options in response to -h
#         add_help=False
#         )

# conf_parser.add_argument("-c", "--conf_file",
#                         help="Specify config file", metavar="FILE")
# args, remaining_argv = conf_parser.parse_known_args()

# defaults = { "option":"default" }

# if args.conf_file:
#     config = configparser.SafeConfigParser()
#     config.read([args.conf_file])
#     defaults.update(dict(config.items("Defaults")))

# # Parse rest of arguments
# # Don't suppress add_help here so it will handle -h
# parser = argparse.ArgumentParser(
#     # Inherit options from config_parser
#     parents=[conf_parser]
#     )
# parser.set_defaults(**defaults)
# # parser.add_argument("--option")
# args = parser.parse_args(remaining_argv)

# print("config arguments: {}".format(str(vars(args))))