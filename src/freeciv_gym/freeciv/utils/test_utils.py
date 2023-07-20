import time
import random
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.freeciv.utils.port_list import DEV_PORT_LIST

def get_first_observation_option(controller):
    # Random choose one port for test
    port = random.choice(DEV_PORT_LIST)
    controller.client_port = port
    # Reset controller. Otherwise, the states (clstate, conn info, etc.) changed in the previous login will cause errors.
    controller.reset()
    opt = None
    obs = None
    # Handle port conflict if exist
    try:
        controller.init_network()
        opt = controller.get_info()['available_actions']
        obs = controller.get_observation()
        # controller.clstate.set_multiplayer_game()
    except Exception as e:
        fc_logger.error(repr(e))
        # Sleep for a random time and try again
        time.sleep(random.uniform(3, 10))
        obs, opt = get_first_observation_option(controller)

    return obs, opt
