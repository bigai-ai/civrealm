# Installation

## Download the Source Code

Clone the CivRealm repository from GitHub and enter the directory:

```bash
cd civrealm
```

## Installation

!!! note "Python Environment"
    We suggest using Conda to create a clean virtual environment for installation.

Installation through the source code in the CivRealm folder:

```bash
pip install -e .
```

## Test the Installation

To test the installation, run the following command after installation:

```bash
test_civrealm
```

If the installation is successful, the output should be similar to the following:

```bash
Reset with port: 6300
Step: 0, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 104, 'move NorthEast')
Step: 1, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 117, 'move North')
Step: 2, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 118, 'move North')
Step: 3, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 119, 'move SouthEast')
Step: 4, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 120, 'move SouthEast')
```

## Multi-Player Mode
To test with multiple players, run the following command in one terminal to start the game with player `myagent`:

```bash
test_civrealm --minp=2 --username=myagent --client_port=6001
```

Then start another terminal and join the game with player `myagent1`:

```bash
test_civrealm --username=myagent1 --client_port=6001
```

!!! warning "Connect to the same port"
    Note that to run multiple agents in the same game, you need to make them connect to the same port (specified by client_port). The available client_port range is 6001, 6300~6331.

!!! warning " 10 seconds delay to reuse a port"
    Note that when a game finishes on a port, the server on that port will take some time (around 10 seconds) to restart itself. If you start a new game on that port before the server is ready, the program will encounter unexpected errors and may stop/halt.

<!-- 
### Update the freeciv-web image

Start the freeciv-web docker with the "docker-compose.yml" file in the civrealm folder:

```bash
docker compose up -d
```

Update the freeciv-web image:

```bash
update_freeciv_web_docker
```

Restart the freeciv-web container so that the change takes effect

```bash
docker compose down
docker compose up -d
```
-->