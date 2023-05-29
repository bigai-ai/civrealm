import docker


def init_freeciv_docker():
    client = docker.from_env()
    port_map = {"8443/tcp": 8080, "80/tcp": 80, "7000/tcp": 7000,
                "7001/tcp": 7001, "7002/tcp": 7002, "6000/tcp": 6000,
                "6001/tcp": 6001, "6002/tcp": 6002}

    client.containers.run('freeciv-web',
                          "./start-freeciv-web.sh",
                          ports=port_map,
                          user="docker",
                          tty=True,
                          detach=True,
                          auto_remove=True)
