import docker

# For 409 errors, it is possibly because the host uses docker desktop.
# In this case, please set the DOCKER_HOST environment variable according to https://stackoverflow.com/questions/76919611/docker-python-client-cannot-connect-docker-desktop
client = docker.from_env()
container_name = 'freeciv-web'
settings_path = '/docker/publite2/settings.ini'

cmd = f'cat {settings_path}'
exec_response = client.containers.get(container_name).exec_run(cmd)
file_content = exec_response.output.decode("utf-8")

search_string = 'server_capacity_test'
# Split the content into lines
lines = file_content.splitlines()

found_line = None
for line in lines:
    if search_string in line:
        found_line = line
        break  # Stop searching once the line is found

assert found_line is not None, f"Server setting with '{search_string}' not found in file_content"

# Read server_capacity_test configuration
multi = int(found_line.split(' ')[-1])


# from civrealm.freeciv.utils.freeciv_logging import fc_logger
# fc_logger.debug(f'*******Multi: {multi}')
# print(f'*******Multi: {multi}')

PORT_LIST = [6001]
dev_multi = int(multi * 3 / 4)
eval_multi = multi - dev_multi
DEV_PORT_LIST = [6300 + i for i in range(dev_multi)]
EVAL_PORT_LIST = [6300 + dev_multi + i for i in range(eval_multi)]
PORT_LIST = PORT_LIST + DEV_PORT_LIST + EVAL_PORT_LIST
