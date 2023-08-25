import time
import random
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.freeciv.utils.port_list import DEV_PORT_LIST


def get_first_observation_option(controller, client_port=None):
    # Random choose one port for test
    if client_port is not None:
        controller.client_port = client_port
    else:
        controller.client_port = random.choice(DEV_PORT_LIST)
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
        fc_logger.error(f'get_first_observation_option error: {repr(e)}')
        # Sleep for a random time and try again
        time.sleep(random.uniform(3, 5))
        obs, opt = get_first_observation_option(controller, client_port)

    return obs, opt
