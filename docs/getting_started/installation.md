## Download the source code

Clone the CivRealm repository from GitHub and enter the directory:

```bash
cd civrealm
```

## Installation
>
> We suggest using Conda to create a clean virtual environment for installation.

Installation through the source code in the CivRealm folder:

```bash
pip install -e .
```

## Test the installation

To test the installation, run the following command in the CivRealm folder:

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