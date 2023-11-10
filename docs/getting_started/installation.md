## Installation
> We suggest using Conda to create a clean virtual environment for installation.

Installation through the source code in the civrealm folder:

```bash
cd civrealm
pip install -e .
```

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