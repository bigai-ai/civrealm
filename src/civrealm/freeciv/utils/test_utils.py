import time
import random
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.freeciv.utils.port_list import PORT_LIST
from civrealm.freeciv.civ_controller import CivController


def get_first_observation_option(controller: CivController, client_port=None):
    # Random choose one port for test
    if client_port is not None:
        controller.client_port = client_port
    else:
        controller.client_port = random.choice(PORT_LIST)
    # Reset controller. Otherwise, the states (clstate, conn info, etc.) changed in the previous login will cause errors.
    controller.reset()
    # Handle port conflict if exist
    try:
        controller.init_network()
        _, observation = controller.get_info_and_observation()
        options = controller.turn_manager.turn_actions
        # controller.clstate.set_multiplayer_game()
        return observation, options
    except Exception as e:
        fc_logger.error(f'get_first_observation_option error: {repr(e)}')
        controller.ws_client.close()
        # Sleep for a random time and try again
        time.sleep(random.uniform(3, 5))
        return get_first_observation_option(controller, client_port)
